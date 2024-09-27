import os.path
from typing import Dict

from mkdocs.config.defaults import MkDocsConfig
from mkdocs_macros.plugin import MacrosPlugin  # pylint: disable=import-error

from mkdocs_partial.docs_package_plugin import DocsPackagePlugin


# NOTE: has to be replaced with register_filters implementation in PartialDocsPlugin
#       once https://github.com/fralau/mkdocs-macros-plugin/issues/237 is released
class MacrosPluginShim(MacrosPlugin):
    def __init__(self):
        super().__init__()
        self.__docs_packages: Dict[str, DocsPackagePlugin] = {}

    def register_docs_package(self, name: str, package: DocsPackagePlugin):
        self.__docs_packages[name] = package

    def package_link(self, value, name: str = None):
        page = self.page
        if name is None:
            name = page.meta.get("docs_package", None)

        package = self.__docs_packages.get(name, None)
        if package is not None:
            url = os.path.relpath(f"{package.directory}/{value}", os.path.dirname(page.file.src_path))
            url = url.replace("\\", "/")
            return url
        if name is None:
            raise LookupError("`package_link` may be used only on pages managed with `docs_package` plugin")
        raise LookupError(f"Package {name} is not installed")

    def on_config(self, config: MkDocsConfig):
        self.filter(self.package_link)
        return super().on_config(config)
