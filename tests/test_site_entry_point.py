import pytest

from mkdocs_partial.site_entry_point import SiteEntryPoint, local_docs


def test_list(capsys):
    SiteEntryPoint("0.1.0").list(None, None)
    captured = capsys.readouterr().out.splitlines()
    assert len(captured) > 0
    assert "docs-documentation" in captured


@pytest.mark.parametrize(
    "value,plugin, docs_path, docs_directory",
    [
        (r"test=d:\tmp\local-docs\docs::test/sub", "test", r"d:/tmp/local-docs/docs", r"test/sub"),
        (r"test=/tmp/local-docs/docs::test/sub", "test", r"/tmp/local-docs/docs", r"test/sub"),
    ],
    ids=[
        "windows path",
        "linux path",
    ],
)
def test_local_docs(value, plugin, docs_path, docs_directory):
    actual_plugin, actual_docs_path, actual_docs_directory = local_docs(value)
    assert actual_plugin == plugin
    assert actual_docs_path == docs_path
    assert actual_docs_directory == docs_directory
