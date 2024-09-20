from typing import Dict

from mkdocs.utils import normalize_url
from mkdocs_macros.plugin import MacrosPlugin # pylint: disable=import-error

from documentation_mkdocs_partial.docs_package_plugin import DocsPackagePlugin


# NOTE: has to be replaced with register_filters implementation in PartialDocsPlugin
#       once https://github.com/fralau/mkdocs-macros-plugin/issues/237 is released
class MacrosPluginShim(MacrosPlugin):
    def __init__(self):
        super().__init__()
        self.__docs_packages: Dict[str, DocsPackagePlugin] = {}

    def register_docs_package(self, name: str, package: DocsPackagePlugin):
        self.__docs_packages[name] = package

    def package_link(self, value, name: str):
        page = self.page
        package = self.__docs_packages.get(name, None)
        if package is not None:
            return normalize_url(f"{package.directory}/{value}", page)
        raise LookupError(f"Package {name} is not installed")

    def on_config(self, config):
        self.filter(self.package_link)
        return super().on_config(config)
