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
from tempfile import TemporaryDirectory
from typing import Dict, List

import yaml
from mkdocs.__main__ import build_command as mkdocs_build_command, serve_command as mkdocs_serve_command

from documentation_mkdocs_partial.packages.packager import Packager


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
            self.__site_root = os.path.join(script_dir, "site")
        else:
            self.__site_root = site_root
        logging.info(f"script_dir: {self.__site_root}")

    def run(self):
        logging.basicConfig(
            level=logging.INFO,
            format="{asctime} [{levelname}] {message}",
            style="{",
        )

        parser = ArgumentParser(description=f"v{self.__version}")
        subparsers = parser.add_subparsers(help="commands")
        serve_command = self.add_command_parser(
            subparsers, "serve", "", func=lambda args, argv: self.mkdocs(mkdocs_serve_command, args, argv)
        )
        serve_command.add_argument("--local-docs", required=False, type=local_docs)

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
            logging.exception(f"FAIL! {e}")
            success = False

        sys.exit(0 if success else 1)

    @staticmethod
    def add_command_parser(subparsers, name, help_text, func):
        command_parser = subparsers.add_parser(name, help=help_text)
        command_parser.set_defaults(func=func, commandName=name)
        return command_parser

    def mkdocs(self, command, args, argv):
        with TemporaryDirectory() as site_root:
            mkdocs_yaml = {}
            logging.info(f"site root: {self.__site_root}")
            for file in glob.glob(os.path.join(self.__site_root, "**/*"), recursive=True):
                logging.info(f"\t{file}")
                path = os.path.relpath(file, self.__site_root).replace("\\", "/")
                is_mkdocs_yaml = path.lower() == "mkdocs.yml"
                path = os.path.join(site_root, path).replace("\\", "/")
                Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
                if os.path.isfile(file):
                    if not is_mkdocs_yaml:
                        shutil.copyfile(file, path)
                    else:
                        mkdocs_yaml = self.write_mkdocs_yaml(args, file, path)
            current_dir = os.getcwd()

            docs_dir = mkdocs_yaml.get("docs_dir", "docs")
            try:
                os.chdir(site_root)
                Path(docs_dir).mkdir(parents=True, exist_ok=True)
                command(argv)  # pylint: disable=too-many-function-args
            finally:
                os.chdir(current_dir)

    @staticmethod
    def write_mkdocs_yaml(args, source, path):  # pylint: disable=unused-argument
        with open(source) as stream:
            # TODO: args to override doc package docs_dir for local documentation writing
            # logging.info(args.local_docs)
            source = yaml.safe_load(stream)
            if "plugins" not in source:
                source["plugins"] = []
            plugins: List = source["plugins"]
            partial_docs = next(
                (plugin["partial_docs"] for plugin in plugins if isinstance(plugin, dict) and "partial_docs" in plugin),
                None,
            )
            if partial_docs is None:
                partial_docs: Dict = {}
                plugins.append({"partial_docs": partial_docs})
            if args.local_docs is not None:
                plugin, docs_path = args.local_docs
                plugin = partial_docs.setdefault("packages", {}).setdefault(plugin, {})
                plugin["docs_path"] = docs_path

            with open(path, "w") as target:
                yaml.dump(source, target)
            return source


if __name__ == "__main__":
    SiteEntryPoint("1.0", site_root=r"d:\CODE\cy\subsystems\documentation\docs-site-documentation-inceptum").run()
