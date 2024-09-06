import glob
import hashlib
import inspect
import logging
import os
import zipfile
from abc import ABC
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from documentation_mkdocs_partial import MODULE_NAME_RESTRICTED_CHARS, version
from documentation_mkdocs_partial.report_base import ReportBase


class Packager(ABC):
    def __init__(self):
        pass

    def pack(
        self, docs_dir, site_dir, package_name, package_version, package_description, output_dir, edit_url_template
    ):
        start = datetime.now()
        logging.info(f"Building package {package_name} v{package_version} form folder {docs_dir}.")
        module_name = MODULE_NAME_RESTRICTED_CHARS.sub("_", package_name.lower())

        wheel_filename = os.path.join(output_dir, f"{package_name}-{package_version}-py3-none-any.whl")
        script_dir = os.path.dirname(os.path.realpath(__file__))
        resources_dir = os.path.join(script_dir, "templates")
        report = ReportBase(templates_dir=resources_dir, output_path=None)

        with zipfile.ZipFile(wheel_filename, "w") as zipf:
            dist_info_dir = f"{package_name}-{package_version}.dist-info"

            wheel_files = {
                f"{dist_info_dir}/METADATA": "METADATA.j2",
                f"{dist_info_dir}/WHEEL": "WHEEL.j2",
                f"{dist_info_dir}/entry_points.txt": "entry_points.txt.j2",
                "setup.py": "setup.py.j2",
                f"{module_name}/__init__.py": "__init__.py.j2",
                f"{module_name}/plugin.py": "plugin.py.j2",
            }

            record_lines = []
            for path, template in wheel_files.items():
                content = report.write_template(
                    template,
                    # name=path,
                    package_name=package_name,
                    module_name=module_name,
                    package_version=package_version,
                    dependency=f'{inspect.getmodule(version).__name__.split(".")[0]} >= {version.__version__}',
                    root="None" if site_dir is None else f'"{site_dir}"',
                    edit_url_template="None" if edit_url_template is None else f'"{edit_url_template}"',
                    package_description=package_description,
                )
                file_data = bytes(content, "utf8")
                record_line = self.write_file(path, file_data, zipf)
                if not path.startswith(dist_info_dir):
                    record_lines.append(record_line)

            for file in glob.glob(os.path.join(docs_dir, "**/*"), recursive=True):
                if os.path.isfile(file):
                    path = os.path.relpath(file, docs_dir)
                    path = os.path.join(module_name, "docs", path)
                    path = path.replace("\\", "/")
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
