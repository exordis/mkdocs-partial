import glob
import hashlib
import importlib
import logging
import os
import zipfile
from abc import ABC
from datetime import datetime
from importlib.metadata import entry_points
from itertools import chain
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List

from packaging.requirements import Requirement
from packaging.version import Version

from mkdocs_partial import MODULE_NAME_RESTRICTED_CHARS, version
from mkdocs_partial.docs_package_plugin import DocsPackagePlugin
from mkdocs_partial.mkdcos_helpers import normalize_path
from mkdocs_partial.templating.markdown_extension import TemplaterMarkdownExtension
from mkdocs_partial.templating.templater import Templater


class Packager(ABC):
    def __init__(self, templates_dir):
        self.__templates_dir = templates_dir

    def pack(  # pylint: disable=too-many-positional-arguments
        self,
        package_name,
        package_version,
        package_description,
        output_dir,
        resources_src_dir,
        excludes=None,
        resources_package_dir=None,
        add_self_dependency=True,
        requirements_path=None,
        freeze=False,
        **kwargs,
    ):
        resources_src_dir = os.path.abspath(resources_src_dir)
        resources_src_dir = normalize_path(resources_src_dir)

        output_dir = normalize_path(output_dir)
        if excludes is None:
            excludes = []
        start = datetime.now()
        logging.info(f"Building package {package_name} v{package_version} form folder {resources_src_dir}.")
        module_name = MODULE_NAME_RESTRICTED_CHARS.sub("_", package_name.lower())

        wheel_filename = os.path.join(output_dir, f"{module_name}-{package_version}-py3-none-any.whl")
        script_dir = os.path.dirname(os.path.realpath(__file__))
        templates_dir = os.path.join(script_dir, os.path.join("templates", self.__templates_dir))
        templater = Templater(templates_dir=templates_dir).extend(TemplaterMarkdownExtension())

        requirements = []
        if requirements_path is not None:
            if not os.path.isfile(requirements_path) and not os.path.isabs(requirements_path):
                requirements_path = os.path.join(resources_src_dir, requirements_path)
            if os.path.isfile(requirements_path):
                requirements = self.parse_requirements(requirements_path)

        if add_self_dependency:
            parsed_version = Version(version.__version__)
            base_version = Version(parsed_version.base_version)
            if base_version == parsed_version:
                self_dependency = f"mkdocs-partial >={version.__version__}"
            elif base_version.micro > 0:
                self_dependency = (
                    f"mkdocs-partial > {parsed_version.major}.{parsed_version.minor}.{parsed_version.micro - 1}."
                )
            elif base_version.minor > 0:
                self_dependency = f"mkdocs-partial > {parsed_version.major}.{parsed_version.minor - 1}.0"
            else:
                self_dependency = f"mkdocs-partial > {parsed_version.major - 1}.0.0"
            requirements.append(Requirement(self_dependency))

        if freeze:
            requirements = Packager.freeze_requirements(requirements)
        args = {**kwargs}
        args.update(
            {
                "package_name": package_name,
                "module_name": module_name,
                "package_version": package_version,
                "requirements": list(requirements),
                "package_description": package_description,
            }
        )

        with zipfile.ZipFile(wheel_filename, "w") as zipf:
            dist_info_dir = f"{module_name}-{package_version}.dist-info"

            record_lines = []

            for templates_subdir, wheel_subdir, record in [
                ("dist-info", dist_info_dir, False),
                ("package", module_name, True),
            ]:
                for file in glob.glob(os.path.join(templates_dir, templates_subdir, "**/*"), recursive=True):
                    if os.path.isfile(file):
                        path = os.path.relpath(os.path.normpath(file), os.path.join(templates_dir, templates_subdir))
                        path = os.path.join(wheel_subdir, path).replace("\\", "/")
                        path = templater.template_string(path, **args)
                        if path.lower().endswith(".j2"):
                            path = path[:-3]
                        content = templater.template(os.path.relpath(file, templates_dir).replace("\\", "/"), **args)
                        content.replace("\r\n", "\n")
                        file_data = bytes(content, "utf8")
                        record_line = self.write_file(path, file_data, zipf)
                        if record:
                            record_lines.append(record_line)

            excluded = chain(
                *[
                    glob.glob(normalize_path(os.path.join(resources_src_dir, exclude)), recursive=True)
                    for exclude in excludes
                ]
            )
            excluded = [normalize_path(exclude) for exclude in excluded]
            for exclude in excludes:
                logging.info(f"Excluded glob {normalize_path(os.path.join(resources_src_dir, exclude))}")
            for exclude in excluded:
                logging.info(f"Excluding file {exclude}")
            for file in glob.glob(os.path.join(resources_src_dir, "**/*"), recursive=True):
                file = normalize_path(file)
                if os.path.isfile(file) and file not in excluded:
                    logging.info(f"Packaging file {file}")
                    path = module_name
                    if resources_package_dir is not None and resources_package_dir != "":
                        path = os.path.join(path, resources_package_dir)
                    path = os.path.join(path, os.path.relpath(file, resources_src_dir))
                    path = normalize_path(path)
                    record_lines.append(self.write_file(path, Path(file).read_bytes(), zipf))

            zipf.writestr(f"{dist_info_dir}/RECORD", "\n".join(record_lines) + "\n")

        logging.info(f"Package is built within {(datetime.now() - start)}. File is written to {wheel_filename}")

    @staticmethod
    def write_file(arcname, file_data, zipf):
        sha256_hash = hashlib.sha256(file_data).hexdigest()
        file_size = len(file_data)
        with NamedTemporaryFile("wb", delete_on_close=False) as file:
            file.write(file_data)
            file.close()
            zipf.write(file.name, arcname)
        return f"{arcname},sha256={sha256_hash},{file_size}"

    @staticmethod
    def parse_requirements(path):
        with open(path) as f_requirements:
            requirements = [
                Requirement(dependency)
                for dependency in f_requirements.readlines()
                if not dependency.isspace() and dependency != "" and dependency[0] != "#"
            ]
        return requirements

    @staticmethod
    def freeze(path):
        requirements = Packager.parse_requirements(path)

        with open(path, "w") as f_requirements:
            for requirement in Packager.freeze_requirements(requirements):
                f_requirements.write(f"{requirement}\n")
        return True, None

    @staticmethod
    def freeze_requirements(requirements: List[Requirement]):
        plugin_requirements = {}
        for mkdocs_plugin in entry_points(group="mkdocs.plugins"):
            try:
                plugin_class = mkdocs_plugin.load()
            except ModuleNotFoundError:
                continue

            if issubclass(plugin_class, DocsPackagePlugin) and plugin_class != DocsPackagePlugin:
                plugin_requirements[mkdocs_plugin.dist.name] = Requirement(
                    f"{mkdocs_plugin.dist.name}=={mkdocs_plugin.dist.version}"
                )

        for requirement in requirements:
            yield plugin_requirements.get(requirement.name, requirement)

    @staticmethod
    def get_mudules_from_packages(*packages: str):
        installed_packages = list(chain(*[importlib.metadata.distributions(name=package) for package in packages]))
        module_names = set()
        for package in installed_packages:
            distribution = importlib.metadata.distribution(package.metadata["Name"])
            for file in distribution.files:
                if (
                    not file.name.endswith(".pyc")  # pylint: disable=too-many-boolean-expressions
                    and "__pycache__" not in Path(file.name).parts
                    and ".dist-info" not in Path(file.name).parts
                    and not file.parts[0].endswith(".dist-info")
                    and not file.parts[0].endswith(".egg-info")
                    and ".." not in file.parts
                ):
                    module_name = file.parts[0]
                    name, extension = os.path.splitext(module_name)
                    if extension == ".py":
                        module_name = name
                        extension = ""
                    if extension == "" and not name.startswith("_"):
                        module_names.add(module_name)

        return module_names


if __name__ == "__main__":
    modules = Packager.get_mudules_from_packages(
        "mkdocs-material",
        "mkdocs-glightbox",
        "mkdocs-macros-plugin",
        "mkdocs-spellcheck",
        "documentation-mkdocs-landscape",
        "documentation-mkdocs-plugins",
        "docs-documentation-inceptum",
        "docs-documentation",
        "docs-cicd",
        "docs-observability",
        "docs-organisation",
        "docs-infrastructure",
        "mkdocs_partial",
    )
    print(modules)
