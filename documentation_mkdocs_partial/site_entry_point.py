# pylint: disable=duplicate-code
import inspect
import logging
import os
import sys
from abc import ABC
from argparse import ArgumentParser, ArgumentTypeError
from pathlib import Path

import yaml
from mkdocs.__main__ import build_command as mkdocs_build_command, serve_command as mkdocs_serve_command

from documentation_mkdocs_partial.packages.argparse_types import directory
from documentation_mkdocs_partial.packages.packager import Packager
from documentation_mkdocs_partial.partial_docs_plugin import PartialDocsPlugin


def local_docs(value: str):
    values = value.split("=", maxsplit=1)
    plugin = values[0]
    path = "/docs" if len(values) <= 1 else values[1]
    if not os.path.isdir(path):
        raise ArgumentTypeError(f"directory '{path}' for plugin '{plugin}' does not exist")
    return plugin, Packager.normalize_path(path)


class SiteEntryPoint(ABC):

    def __init__(self, version, site_root=None):
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

        parser = ArgumentParser(description=f"v{self.__version}")
        subparsers = parser.add_subparsers(help="commands")
        self.add_command_parser(
            subparsers, "serve", "", func=lambda args, argv: self.mkdocs(mkdocs_serve_command, args, argv)
        )

        self.add_command_parser(
            subparsers, "build", "", func=lambda args, argv: self.mkdocs(mkdocs_build_command, args, argv)
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
        command_parser.add_argument("--local-docs", required=False, type=local_docs)
        command_parser.add_argument("--site-root", required=False, type=directory)
        return command_parser

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
            plugin, docs_path = args.local_docs
            PartialDocsPlugin.docs_path_overrides[plugin] = docs_path

        current_dir = os.getcwd()
        os.chdir(site_root_path)
        try:
            os.chdir(site_root_path)
            Path(site_root_path).mkdir(parents=True, exist_ok=True)
            command(argv)  # pylint: disable=too-many-function-args
        finally:
            os.chdir(current_dir)
        return False, ""


if __name__ == "__main__":
    SiteEntryPoint("1.0").run()
