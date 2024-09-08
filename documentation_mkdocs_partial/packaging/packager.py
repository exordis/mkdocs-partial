import glob
import hashlib
import inspect
import logging
import os
import zipfile
from abc import ABC
from datetime import datetime
from itertools import chain
from pathlib import Path
from tempfile import NamedTemporaryFile

from documentation_reporting.markdown_extension import TemplaterMarkdownExtension
from documentation_reporting.templater import Templater

from documentation_mkdocs_partial import MODULE_NAME_RESTRICTED_CHARS, version


class Packager(ABC):
    def __init__(self, templates_dir):
        self.__templates_dir = templates_dir

    def pack(
        self,
        package_name,
        package_version,
        package_description,
        output_dir,
        resources_src_dir,
        excludes=None,
        resources_package_dir=None,
        add_self_dependency=True,
        requirements=None,
        **kwargs,
    ):
        resources_src_dir = os.path.abspath(resources_src_dir)
        resources_src_dir = Packager.normalize_path(resources_src_dir)

        output_dir = Packager.normalize_path(output_dir)
        if excludes is None:
            excludes = []
        start = datetime.now()
        logging.info(f"Building package {package_name} v{package_version} form folder {resources_src_dir}.")
        module_name = MODULE_NAME_RESTRICTED_CHARS.sub("_", package_name.lower())

        wheel_filename = os.path.join(output_dir, f"{module_name}-{package_version}-py3-none-any.whl")
        script_dir = os.path.dirname(os.path.realpath(__file__))
        templates_dir = os.path.join(script_dir, os.path.join("templates", self.__templates_dir))
        templater = Templater(templates_dir=templates_dir).extend(TemplaterMarkdownExtension())

        dependencies = []
        if requirements:
            if not os.path.isfile(requirements):
                requirements = os.path.join(resources_src_dir, requirements)
            if os.path.isfile(requirements):
                with open(requirements) as f_requirements:
                    dependencies = [line.rstrip("\n").rstrip("\r") for line in f_requirements.readlines()]
                    dependencies = [dependency for dependency in dependencies if not dependency.isspace()]
        if add_self_dependency:
            dependencies.append(f'{inspect.getmodule(version).__name__.split(".")[0]} >={version.__version__}')

        args = {**kwargs}
        args.update(
            {
                "package_name": package_name,
                "module_name": module_name,
                "package_version": package_version,
                "dependencies": dependencies,
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
                    path = os.path.relpath(os.path.normpath(file), os.path.join(templates_dir, templates_subdir))
                    path = os.path.join(wheel_subdir, path).replace("\\", "/")
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
                    glob.glob(Packager.normalize_path(os.path.join(resources_src_dir, exclude)), recursive=True)
                    for exclude in excludes
                ]
            )
            excluded = [Packager.normalize_path(exclude) for exclude in excluded]
            for exclude in excludes:
                logging.info(f"Excluded glob {Packager.normalize_path(os.path.join(resources_src_dir, exclude))}")
            for exclude in excluded:
                logging.info(f"Excluding file {exclude}")
            for file in glob.glob(os.path.join(resources_src_dir, "**/*"), recursive=True):
                file = Packager.normalize_path(file)
                if os.path.isfile(file) and file not in excluded:
                    logging.info(f"Packaging file {file}")
                    path = module_name
                    if resources_package_dir is not None and resources_package_dir != "":
                        path = os.path.join(path, resources_package_dir)
                    path = os.path.join(path, os.path.relpath(file, resources_src_dir))
                    path = Packager.normalize_path(path)
                    record_lines.append(self.write_file(path, Path(file).read_bytes(), zipf))

            zipf.writestr(f"{dist_info_dir}/RECORD", "\n".join(record_lines) + "\n")

        logging.info(f"Package is built within {(datetime.now() - start)}. File is written to {wheel_filename}")

    @staticmethod
    def normalize_path(path: str) -> str:
        return os.path.normpath(path).replace("\\", "/")

    @staticmethod
    def write_file(arcname, file_data, zipf):
        sha256_hash = hashlib.sha256(file_data).hexdigest()
        file_size = len(file_data)
        with NamedTemporaryFile("wb", delete_on_close=False) as file:
            file.write(file_data)
            file.close()
            zipf.write(file.name, arcname)
        return f"{arcname},sha256={sha256_hash},{file_size}"
