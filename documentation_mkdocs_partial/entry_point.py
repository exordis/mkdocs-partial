import logging
import os
import re
import sys
from argparse import ArgumentParser, ArgumentTypeError

from documentation_mkdocs_partial.packaging.packager import Packager

PACKAGE_NAME_RESTRICTED_CHARS = re.compile(r"[^A-Za-z0-9+_-]")
PACKAGE_NAME = re.compile(r"^[A-Za-z0-9+_-]+$")


def directory(value):
    if not os.path.isdir(value):
        raise ArgumentTypeError("Must be an existing directory")
    return value


def package_name(value):
    if not PACKAGE_NAME.match(value):
        raise ArgumentTypeError(f"'{value}' is invalid package name")
    return value


def run():
    logging.basicConfig(
        level=logging.INFO,
        format="{asctime} [{levelname}] {message}",
        style="{",
    )
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(help="commands")
    package_command = add_command_parser(
        subparsers, "package", "Creates partial documentation package from documentation directory", func=package
    )
    package_command.add_argument(
        "--docs-dir",
        help="Folder with documentation. Default - current directory",
        required=False,
        default=os.getcwd(),
        type=directory,
    )
    package_command.add_argument(
        "--output-dir",
        help="Folder to write generated package file. Default - current directory",
        required=False,
        default=os.getcwd(),
        type=directory,
    )
    package_command.add_argument(
        "--site-dir",
        help="Path in target documentation to inject documentation. " "Default - `--docs-dir` value directory name",
        required=False,
    )
    package_command.add_argument(
        "--package-name",
        help="Name of the package to build. " "Default - normalized `--site-root` value directory name",
        required=False,
        type=package_name,
    )
    package_command.add_argument("--package-version", help="Version of the package to build", required=True)
    package_command.add_argument("--package-description", help="Description of the package to build", required=False)
    package_command.add_argument(
        "--edit-url-template",
        help="f-string template for page edit url "
        "with {path} as placeholder for markdown file  path "
        "relative to directory from --docs-dir",
        required=False,
    )
    args = parser.parse_args()

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)
    try:
        success, message = args.func(args)
        if not success:
            print(message, file=sys.stderr)
        elif message is not None:
            print(message)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logging.exception(f"FAIL! {e}")
        success = False

    sys.exit(0 if success else 1)


def add_command_parser(subparsers, name, help_text, func):
    command_parser = subparsers.add_parser(name, help=help_text)
    command_parser.set_defaults(func=func, commandName=name)
    return command_parser


def package(args):
    if args.site_dir is None:
        args.site_dir = os.path.basename(args.docs_dir)
    if args.package_name is None:
        args.package_name = PACKAGE_NAME_RESTRICTED_CHARS.sub("-", args.site_dir)

    Packager().pack(
        docs_dir=args.docs_dir,
        site_dir=args.site_dir,
        package_name=args.package_name,
        package_version=args.package_version,
        package_description=args.package_description,
        output_dir=args.output_dir,
        edit_url_template=args.edit_url_template,
    )
    return True, None


if __name__ == "__main__":
    run()
