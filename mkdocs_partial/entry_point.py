import logging
import os
import sys
from argparse import ArgumentParser, ArgumentTypeError

from mkdocs_partial import PACKAGE_NAME, PACKAGE_NAME_RESTRICTED_CHARS
from mkdocs_partial.argparse_types import directory, file
from mkdocs_partial.packages.packager import Packager
from mkdocs_partial.version import __version__


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
    parser = ArgumentParser(description=f"v{__version__}", prog="mkdocs-partial")
    subparsers = parser.add_subparsers(help="commands")
    package_command = add_command_parser(
        subparsers, "package", "Creates partial documentation package from directory", func=package
    )

    add_packager_args(
        package_command,
        package_name_extra_help=" Default - normalized `--directory` value directory name.",
        output_dir_extra_help=" Default - `--source-dir` value directory name.",
    )
    package_command.add_argument(
        "--directory",
        required=False,
        help="Path in target documentation to inject documentation, relative to mkdocs `doc_dir`. "
        "Pass empty string to inject files directly to mkdocs `docs_dir`"
        "Default - `--source-dir` value directory name",
    )
    package_command.add_argument(
        "--title",
        required=False,
        help="Override title if defined in package root index.md",
    )
    package_command.add_argument(
        "--blog-categories",
        required=False,
        default="",
        help="`/` separated list of  categories to  be prepended  to defined in blog posts of the package."
        "Empty by default",
    )
    package_command.add_argument(
        "--edit-url-template",
        required=False,
        help="f-string template for page edit url with {path} as placeholder for markdown file  path "
        "relative to directory from --docs-dir",
    )

    site_package_command = add_command_parser(
        subparsers, "site-package", "Creates documentation site-package package from  directory", func=site_package
    )

    add_packager_args(
        site_package_command,
        package_name_extra_help=" Default - `--source-dir` value directory name.",
        output_dir_extra_help=" Default - `--source-dir` value directory name.",
    )

    freeze_command = add_command_parser(
        subparsers, "freeze", "Pins doc package versions in requirements.txt to currently installed", func=freeze
    )
    freeze_command.add_argument(
        "path",
        type=file,
        help="path to requirements.txt",
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


def add_packager_args(
    parser,
    source_dir_help="Directory to be packaged. Default - current directory",
    package_name_extra_help="",
    output_dir_extra_help="",
):
    parser.add_argument(
        "--source-dir",
        required=False,
        default=os.getcwd(),
        type=directory,
        help=source_dir_help,
    )
    parser.add_argument(
        "--package-name",
        required=False,
        type=package_name,
        help=f"Name of the package to build. {package_name_extra_help}",
    )
    parser.add_argument("--package-version", required=True, help="Version of the package to build")
    parser.add_argument("--package-description", required=False, help="Description of the package to build")
    parser.add_argument(
        "--output-dir",
        required=False,
        type=directory,
        help=f"Directory to write generated package file.{output_dir_extra_help}",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        required=False,
        default=[],
        help="Exclude glob (should be relative to directory provided with `--source-dir` ",
    )
    parser.add_argument(
        "--freeze",
        dest="freeze",
        action="store_true",
        help="Pin doc package versions in requirements.txt to currently installed."
        " (if there is no requirements.txt in `--source-dir` directory, has no effect)",
    )


def package(args):
    if args.directory is None:
        args.directory = os.path.basename(args.source_dir)
    if args.output_dir is None:
        args.output_dir = args.source_dir
    if args.package_name is None:
        args.package_name = PACKAGE_NAME_RESTRICTED_CHARS.sub("-", args.directory.lower())

    Packager("docs-package").pack(
        package_name=args.package_name,
        package_version=args.package_version,
        package_description=args.package_description,
        resources_src_dir=args.source_dir,
        output_dir=args.output_dir,
        resources_package_dir="docs",
        requirements_path="requirements.txt",
        freeze=args.freeze,
        excludes=["requirements.txt", "requirements.txt.j2"] + args.exclude,
        directory="None" if args.directory is None else f'"{args.directory}"',
        edit_url_template="None" if args.edit_url_template is None else f'"{args.edit_url_template}"',
        title="None" if args.title is None else f'"{args.title}"',
        blog_categories="None" if args.blog_categories is None else f'"{args.blog_categories}"',
    )
    return True, None


def site_package(args):
    if args.output_dir is None:
        args.output_dir = args.source_dir
    if args.package_name is None:
        args.package_name = PACKAGE_NAME_RESTRICTED_CHARS.sub("-", os.path.basename(args.source_dir).lower())

    Packager("site-package").pack(
        package_name=args.package_name,
        package_version=args.package_version,
        package_description=args.package_description,
        resources_src_dir=args.source_dir,
        output_dir=args.output_dir,
        resources_package_dir="site",
        requirements_path="requirements.txt",
        freeze=args.freeze,
        excludes=["requirements.txt", "requirements.txt.j2"] + args.exclude,
    )
    return True, None


def freeze(args):
    Packager.freeze(args.__path)
    return True, None


if __name__ == "__main__":
    run()
