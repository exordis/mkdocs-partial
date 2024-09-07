import pytest
from mkdocs.config.defaults import MkDocsConfig

from documentation_mkdocs_partial.docs_package_plugin import DocsPackagePlugin, DocsPackagePluginConfig


@pytest.mark.parametrize(
    "directory,path,expected_src_uri",
    [
        ("", "/docs/file.md", "file.md"),
        ("", "/docs/subfolder/file.md", "subfolder/file.md"),
        ("directory", "/docs/subfolder/file.md", "directory/subfolder/file.md"),
    ],
    ids=["No root, no subfolder", "No root, has subfolder", "Root and subfolder"],
)
def test_get_src_uri(directory, path, expected_src_uri):
    plugin = DocsPackagePlugin(directory=directory)
    plugin.config = DocsPackagePluginConfig()
    plugin.config.docs_path = "/docs"
    plugin.on_config(MkDocsConfig())
    assert plugin.get_src_uri(path) == expected_src_uri


@pytest.mark.parametrize(
    "directory,path,url_template_path",
    [
        ("", "file.md", "file.md"),
        ("", "subfolder/file.md", "subfolder/file.md"),
        ("directory", "directory/file.md", "file.md"),
        ("directory", "directory/subfolder/file.md", "subfolder/file.md"),
    ],
    ids=[
        "directory=='', file in root directory",
        "directory=='', file in subfolder",
        "directory=='directory', file in root directory",
        "directory=='directory', file in subfolder",
    ],
)
def test_get_edit_url_template_path(directory, path, url_template_path):
    plugin = DocsPackagePlugin(directory=directory)
    plugin.config = DocsPackagePluginConfig()
    plugin.config.docs_path = "/docs"
    plugin.on_config(MkDocsConfig())
    assert plugin.get_edit_url_template_path(path) == url_template_path