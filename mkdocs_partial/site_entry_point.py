# pylint: disable=duplicate-code
import glob
import inspect
import logging
import os
import shutil
import sys
from abc import ABC
from argparse import ArgumentParser, ArgumentTypeError
from pathlib import Path

import yaml
from mkdocs.__main__ import build_command as mkdocs_build_command, serve_command as mkdocs_serve_command
from mkdocs.plugins import get_plugins

from mkdocs_partial.argparse_types import directory
from mkdocs_partial.docs_package_plugin import DocsPackagePlugin, DocsPackagePluginConfig
from mkdocs_partial.entry_point import add_command_parser
from mkdocs_partial.mkdcos_helpers import normalize_path
from mkdocs_partial.partial_docs_plugin import PartialDocsPlugin


def local_docs(value: str, check_path: bool = True):
    values = value.split("=", maxsplit=1)
    plugin = values[0]
    docs_directory = None
    if len(values) <= 1:
        path = "/docs"
    else:
        values = values[1].rsplit("::", maxsplit=1)
        docs_directory = None if len(values) <= 1 else values[1]
        path = values[0]

    if check_path and not os.path.isdir(path):
        raise ArgumentTypeError(f"directory '{path}' for plugin '{plugin}' does not exist.")
    return plugin, normalize_path(path), docs_directory


class SiteEntryPoint(ABC):

    def __init__(self, version, site_root=None, prog=None):
        self.__prog = prog
        self.__version = version
        if site_root is None:
            script_dir = os.path.dirname(os.path.realpath(inspect.getfile(self.__class__)))
            self.__default_site_root = os.path.join(script_dir, "site")
        else:
            self.__default_site_root = site_root
        logging.basicConfig(
            level=logging.INFO,
            format="{asctime} [{levelname}] {message}",
            style="{",
        )
        self.logger = logging.getLogger(__name__)

    def run(self):

        parser = ArgumentParser(description=f"v{self.__version}", prog=self.__prog)
        subparsers = parser.add_subparsers(help="commands")
        self.add_mkdocs_command_parser(
            subparsers,
            "serve",
            "execute mkdocs serve",
            func=lambda args, argv: self.mkdocs(mkdocs_serve_command, args, argv),
        )

        self.add_mkdocs_command_parser(
            subparsers,
            "build",
            "execute mkdocs build",
            func=lambda args, argv: self.mkdocs(mkdocs_build_command, args, argv),
        )

        self.add_command_parser(subparsers, "list", "lists partial docs plugins", func=self.list)
        self.add_command_parser(subparsers, "version", "outputs site version", func=self.version)

        dump_command = self.add_command_parser(subparsers, "dump", "dump site files to the dir", func=self.dump)
        dump_command.add_argument(
            "--output", required=False, type=directory, help="Output directory. Default - Current directory"
        )

        args, argv = parser.parse_known_args()

        if not hasattr(args, "func"):
            parser.print_help()
            sys.exit(0)
        try:
            success, message = args.func(args, argv)
            if not success:
                print(message, file=sys.stderr)
            elif message is not None:
                print(message)
        except Exception as e:  # pylint: disable=broad-exception-caught
            self.logger.exception(f"FAIL! {e}")
            success = False

        sys.exit(0 if success else 1)

    @staticmethod
    def add_command_parser(subparsers, name, help_text, func):
        command_parser = subparsers.add_parser(name, help=help_text)
        command_parser.set_defaults(func=func, commandName=name)
        return command_parser

    @staticmethod
    def add_mkdocs_command_parser(subparsers, name, help_text, func):
        command_parser = add_command_parser(subparsers, name, help_text, func)
        command_parser.add_argument(
            "--local-docs",
            required=False,
            type=local_docs,
            help="loads local directory as `docs_package` plugin content. "
            "Format <plugin name>[=<docs_path>[::<directory>]]. "
            "If `docs_path` is not provided `/docs` is used as default. "
            "If plugin is configured within site mkdocs.yml `directory` overrides "
            "corresponding plugin config option. "
            "If plugin not configured within site mkdocs.yml, it is added to config",
        )
        command_parser.add_argument(
            "--site-root",
            required=False,
            type=directory,
            help="loads local directory as site `docs_dir` instead of the content packed with " "site package",
        )
        return command_parser

    @staticmethod
    def list(args, argv):  # pylint: disable=unused-argument
        for name, entrypoint in get_plugins().items():
            try:
                plugin_class = entrypoint.load()
            except ModuleNotFoundError:
                continue
            if issubclass(plugin_class, DocsPackagePlugin) and plugin_class != DocsPackagePlugin:
                print(name)
        return True, None

    def version(self, args, argv):  # pylint: disable=unused-argument
        print(self.__version)
        return True, None

    def mkdocs(self, command, args, argv):

        site_root_path = args.site_root
        if site_root_path is None:
            site_root_path = self.__default_site_root

        self.logger.info(f"site root: {site_root_path}")
        mkdocs_yaml_path = os.path.join(site_root_path, "mkdocs.yml")
        if not os.path.isfile(mkdocs_yaml_path):
            return False, "Site root does not have mkdocs.yml"
        with open(mkdocs_yaml_path) as file:
            mkdocs_yaml = yaml.safe_load(file)
        plugins = mkdocs_yaml.get("plugins", [])
        if not any("partial_docs" in plugin for plugin in plugins):
            return False, f"{mkdocs_yaml_path} must define 'partial_docs' plugin"

        if args.local_docs is not None:
            plugin, docs_path, docs_directory = args.local_docs
            override = DocsPackagePluginConfig()
            override.docs_path = docs_path
            override.directory = docs_directory
            PartialDocsPlugin.overrides[plugin] = override

        current_dir = os.getcwd()
        os.chdir(site_root_path)
        try:
            os.chdir(site_root_path)
            Path(site_root_path).mkdir(parents=True, exist_ok=True)
            command(argv)  # pylint: disable=too-many-function-args
        finally:
            os.chdir(current_dir)
        return False, ""

    def dump(self, args, argv):  # pylint: disable=unused-argument
        output = args.output
        if output is None:
            output = os.getcwd()
        output = normalize_path(output)

        for path in glob.glob(os.path.join(self.__default_site_root, "**/*"), recursive=True):
            path = normalize_path(path)
            dest = os.path.relpath(path, self.__default_site_root)
            dest = os.path.join(output, dest)
            dest = normalize_path(dest)
            if os.path.isdir(path):
                os.makedirs(dest, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy(path, dest)

        return True, ""


if __name__ == "__main__":
    SiteEntryPoint("1.0", r"d:\CODE\cy\subsystems\documentation\docs-site-documentation-inceptum").run()
