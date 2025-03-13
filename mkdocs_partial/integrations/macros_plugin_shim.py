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
        # self.__log = get_plugin_logger("partial_docs")

    def register_docs_package(self, name: str, package: DocsPackagePlugin):
        self.__docs_packages[name] = package

    def package_link(self, value, name: str = None):
        page = self.page
        if name is None:
            name = page.meta.get("docs_package", None)

        package = self.__docs_packages.get(name, None)
        if package is not None:
            link = os.path.relpath(
                f"{package.directory.lstrip("/").lstrip("\\")}/{value}", os.path.dirname(page.file.src_path)
            )
            link = link.replace("\\", "/")
            # self.__log.info(f"<package_link> package.directory: {package.directory}, file: {value}, link: {link}")
            return link
        if name is None:
            raise LookupError("`package_link` may be used only on pages managed with `docs_package` plugin")
        raise LookupError(f"Package {name} is not installed")

    def package_version(self, name: str = None):
        page = self.page
        if name is None or name == "":
            name = page.meta.get("docs_package", None)
        if name is None:
            raise LookupError(
                "name arg is mandatory for `package_version` when used on pages which are "
                "not managed with `docs_package` plugin"
            )

        package = self.__docs_packages.get(name, None)
        if package is None:
            raise LookupError(f"Package {name} is not installed")

        return package.version

    def on_config(self, config: MkDocsConfig):
        self.filter(self.package_link)
        self.filter(self.package_version)
        super().on_config(config)
        self.env.globals.update({"package_version": self.package_version})
