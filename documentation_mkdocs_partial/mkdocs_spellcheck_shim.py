# pylint: disable=unused-argument
import os
from typing import Any

from mkdocs import plugins
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page
from mkdocs_spellcheck.plugin import SpellCheckPlugin  # pylint: disable=import-error


class SpellCheckShim(SpellCheckPlugin):

    def on_page_content(self, html: str, page: Page, **kwargs: Any) -> None:
        if page.meta.get("spellcheck", True) and not page.meta.get("generated", False):
            super().on_page_content(html, page, **kwargs)

    @plugins.event_priority(-100)
    def on_files(self, files: Files, /, *, config: MkDocsConfig) -> Files | None:
        known_words_files = list(file for file in files if os.path.basename(file.src_path) == "known_words.txt")
        # remove known_words.txt files to avoid exposing them wth other docs
        for file in known_words_files:
            self.known_words.update(file.content_string.splitlines())
            files.remove(file)

        return files
