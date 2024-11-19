from mkdocs_partial.site_entry_point import SiteEntryPoint


def test_list(capsys):
    SiteEntryPoint("0.1.0").list(None, None)
    captured = capsys.readouterr().out.splitlines()
    assert len(captured) > 0
    assert "docs-documentation" in captured
    pass
