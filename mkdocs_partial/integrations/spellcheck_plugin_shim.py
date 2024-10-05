# pylint: disable=unused-argument
import os
import re
from typing import Any

from mkdocs import plugins
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page
from mkdocs_spellcheck.plugin import SpellCheckPlugin  # pylint: disable=import-error

import mkdocs_partial


class SpellCheckShim(SpellCheckPlugin):
    SKIP_SPELLCHECK = re.compile("<!-- *spellcheck: +disable *-->.*?($|<!-- *spellcheck: +enable *-->)", re.DOTALL)

    def on_page_content(self, html: str, page: Page, **kwargs: Any) -> None:
        if not mkdocs_partial.SpellCheckShimActive:
            super().on_page_content(html, page, **kwargs)
            return

        if page.meta.get("spellcheck", True):
            html_to_spellcheck = self.SKIP_SPELLCHECK.sub("", html)
            if page.file.generated_by is None:
                super().on_page_content(html_to_spellcheck, page, **kwargs)
            else:
                original_path = page.file.src_path
                try:
                    page.file.src_path = f"{page.file.generated_by}:{page.file.src_path}"
                    super().on_page_content(html_to_spellcheck, page, **kwargs)
                finally:
                    page.file.src_path = original_path

    @plugins.event_priority(-100)
    def on_files(self, files: Files, /, *, config: MkDocsConfig) -> Files | None:
        if not mkdocs_partial.SpellCheckShimActive:
            return files if not hasattr(super(), "on_files") else super().on_files(files, config=config)

        known_words_files = list(file for file in files if os.path.basename(file.src_path) == "known_words.txt")
        # remove known_words.txt files to avoid exposing them wth other docs
        for file in known_words_files:
            self.known_words.update(file.content_string.splitlines())
            files.remove(file)

        return files
