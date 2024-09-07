import inspect
import os

from documentation_mkdocs_partial.site_entry_point import SiteEntryPoint


def run():
    script_dir = os.path.dirname(os.path.realpath(inspect.getfile(run)))
    SiteEntryPoint(os.path.join(script_dir, "site"))


if __name__ == "__main__":
    run()