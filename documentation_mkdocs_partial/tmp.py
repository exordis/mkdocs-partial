import os

from documentation_mkdocs_partial.site_entry_point import SiteEntryPoint
from documentation_mkdocs_partial.version import __version__


def run():
    script_dir = os.path.dirname(__file__)
    SiteEntryPoint(__version__, os.path.join(script_dir, "site"))


if __name__ == "__main__":
    run()
