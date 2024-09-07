# pylint: disable=duplicate-code
import glob
import inspect
import logging
import os
import shutil
import sys
from abc import ABC
from argparse import ArgumentParser
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List

import yaml
from mkdocs.__main__ import build_command as mkdocs_build_command, serve_command as mkdocs_serve_command


class SiteEntryPoint(ABC):

    def __init__(self, site_root=None):
        if site_root is None:
            script_dir = os.path.dirname(os.path.realpath(inspect.getfile(self.__class__)))
            self.__site_root = os.path.join(script_dir, "site")
        else:
            self.__site_root = site_root

    def run(self):
        logging.basicConfig(
            level=logging.INFO,
            format="{asctime} [{levelname}] {message}",
            style="{",
        )

        parser = ArgumentParser()
        subparsers = parser.add_subparsers(help="commands")
        serve_command = self.add_command_parser(subparsers, "serve", "", func=self.serve)
        serve_command.add_argument("--local-docs")

        self.add_command_parser(subparsers, "build", "", func=self.build)

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

    def add_command_parser(self, subparsers, name, help_text, func):
        command_parser = subparsers.add_parser(name, help=help_text)
        command_parser.set_defaults(func=func, commandName=name)
        return command_parser

    def build(self, args, argv):  # pylint: disable=unused-argument
        with TemporaryDirectory() as site_root:
            for file in glob.glob(os.path.join(self.__site_root, "**/*"), recursive=True):
                path = os.path.relpath(file, self.__site_root).replace("\\", "/")
                path = os.path.join(site_root, path).replace("\\", "/")
                Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
                if os.path.isfile(file):
                    shutil.copyfile(file, path)
            current_dir = os.getcwd()
            try:
                os.chdir(site_root)
                mkdocs_serve_command(argv)  # pylint: disable=too-many-function-args
            finally:
                os.chdir(current_dir)

    def serve(self, args, argv):
        with TemporaryDirectory() as site_root:
            for file in glob.glob(os.path.join(self.__site_root, "**/*"), recursive=True):
                path = os.path.relpath(file, self.__site_root).replace("\\", "/")
                is_mkdocs_yaml = path.lower() == "mkdocs.yml"
                path = os.path.join(site_root, path).replace("\\", "/")
                Path(os.path.dirname(path)).mkdir(parents=True, exist_ok=True)
                if os.path.isfile(file):
                    if not is_mkdocs_yaml:
                        shutil.copyfile(file, path)
                    else:
                        self.write_mkdocs_yaml(args, file, path)
            current_dir = os.getcwd()
            try:
                os.chdir(site_root)
                mkdocs_build_command(argv)  # pylint: disable=too-many-function-args
            finally:
                os.chdir(current_dir)

    def write_mkdocs_yaml(self, args, source, path):
        with open(source) as stream:
            try:
                # TODO: ars to override doc package docs_dir for local documentation writing
                logging.info(args.local_docs)
                source = yaml.safe_load(stream)
                if "plugins" not in source:
                    source["plugins"] = []
                plugins: List = source["plugins"]
                partial_docs = next(
                    (
                        plugin["partial_docs"]
                        for plugin in plugins
                        if isinstance(plugin, dict) and "partial_docs" in plugin
                    ),
                    None,
                )
                if partial_docs is None:
                    partial_docs = {}
                    plugins.append({"partial_docs": partial_docs})
                with open(path, "w") as target:
                    yaml.dump(source, target)
            except yaml.YAMLError as exc:
                print(exc)


if __name__ == "__main__":
    SiteEntryPoint(site_root=r"d:\CODE\tmp\site").run()
