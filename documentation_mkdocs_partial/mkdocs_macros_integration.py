from abc import ABC

from mkdocs.utils import normalize_url


# NOTE: has to be replaced with register_filters implementation in PartialDocsPlugin
#       once https://github.com/fralau/mkdocs-macros-plugin/issues/237 is released
class MkdocsMacrosIntegration(ABC):

    def __init__(self, env, packages):
        self.__packages = packages
        self.__env = env
        env.filter(self.package_link)
        super().__init__()

    def package_link(self, value, name: str):
        page = self.__env.page
        package = self.__packages.get(name, None)
        if package is not None:
            return normalize_url(f"{package.directory}/{value}", page)
        raise LookupError(f"Package {name} is not installed")
