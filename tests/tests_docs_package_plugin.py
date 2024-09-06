import pytest
from mkdocs.config.defaults import MkDocsConfig

from documentation_mkdocs_partial.docs_package_plugin import DocsPackagePlugin, DocsPackagePluginConfig


@pytest.mark.parametrize(
    "root,path,expected_src_uri",
    [
        ("", "/docs/file.md", "file.md"),
        ("", "/docs/subfolder/file.md", "subfolder/file.md"),
        ("root", "/docs/subfolder/file.md", "root/subfolder/file.md"),
    ],
    ids=["No root, no subfolder", "No root, has subfolder", "Root and subfolder"],
)
def test_get_src_uri(root, path, expected_src_uri):
    plugin = DocsPackagePlugin(directory=root)
    plugin.config = DocsPackagePluginConfig()
    plugin.config.docs_path = "/docs"
    plugin.on_config(MkDocsConfig())
    assert plugin.get_src_uri(path) == expected_src_uri
