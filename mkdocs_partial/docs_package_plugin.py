# pylint: disable=unused-argument
from __future__ import annotations

import glob
import inspect
import logging
import os
import re
from pathlib import Path
from typing import Callable

import frontmatter
from mkdocs import plugins
from mkdocs.config import Config, config_options
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.livereload import LiveReloadServer
from mkdocs.plugins import BasePlugin, PrefixedLogger, get_plugin_logger
from mkdocs.structure.files import File, Files
from mkdocs.structure.nav import Navigation
from mkdocs.structure.pages import Page
from mkdocs.utils.templates import TemplateContext

import mkdocs_partial
from mkdocs_partial import (
    MACROS_ENTRYPOINT_NAME,
    MACROS_ENTRYPOINT_SHIM,
    REDIRECTS_ENTRYPOINT_NAME,
    REDIRECTS_ENTRYPOINT_SHIM,
    SPELLCHECK_ENTRYPOINT_NAME,
    SPELLCHECK_ENTRYPOINT_SHIM,
)
from mkdocs_partial.integrations.material_blog_integration import MaterialBlogsIntegration
from mkdocs_partial.mkdcos_helpers import get_mkdocs_plugin, get_mkdocs_plugin_name, normalize_path


class DocsPackagePluginConfig(Config):
    enabled = config_options.Type(bool, default=True)
    docs_path = config_options.Optional(config_options.Type(str))
    directory = config_options.Optional(config_options.Type(str))
    edit_url_template = config_options.Optional(config_options.Type(str))
    name = config_options.Optional(config_options.Type(str))
    blog_categories = config_options.Optional(config_options.Type(str))

    def patch(self, patch: DocsPackagePluginConfig):
        if patch.docs_path is not None:
            self.docs_path = patch.docs_path
        if patch.directory is not None:
            self.directory = patch.directory


class DocsPackagePlugin(BasePlugin[DocsPackagePluginConfig]):
    supports_multiple_instances = True
    H1_TITLE = re.compile(r"^#[^#]", flags=re.MULTILINE)
    TITLE = re.compile(r"^#", flags=re.MULTILINE)

    @property
    def directory(self):
        return self.__directory

    def __init__(
        self, directory=None, edit_url_template=None, title=None, blog_categories=None, version: str = None
    ):  # pylint: disable=too-many-positional-arguments
        self.__version = version
        self.__title = title
        script_dir = os.path.dirname(os.path.realpath(inspect.getfile(self.__class__)))
        self.__docs_path = os.path.join(script_dir, "docs")
        self.__directory = directory
        self.__edit_url_template = edit_url_template
        self.__files: list[File] = []
        self.__blog_integration = MaterialBlogsIntegration()
        self.__plugin_name = ""
        self.__log = get_plugin_logger("partial_docs")
        self.__blog_categories = blog_categories
        if self.__blog_categories is None:
            self.__blog_categories = self.__title
        if self.__blog_categories is None:
            self.__blog_categories = self.__directory

    @property
    def version(self):
        return self.__version

    def on_startup(self, *, command, dirty):
        # Mkdocs handles plugins with on_startup singletons
        pass

    def on_shutdown(self) -> None:
        # Disable shin in case mkdocs is rebuilding without doc_package plugins enabled
        mkdocs_partial.SpellCheckShimActive = False
        self.__blog_integration.shutdown()

    @plugins.event_priority(100)
    def on_pre_build(self, *, config: MkDocsConfig) -> None:
        self.__blog_integration.sync()

    @plugins.event_priority(-100)
    def on_config(self, config: MkDocsConfig) -> MkDocsConfig | None:
        if not self.config.enabled:
            self.__blog_integration.stop()
            return
        if self.config.docs_path is not None:
            self.__docs_path = self.config.docs_path

        if self.config.directory is not None:
            self.__directory = self.config.directory
        if self.__directory is None:
            self.__directory = ""
        self.__directory = self.__directory.rstrip("/")

        if self.config.name is not None:
            self.__plugin_name = self.config.name
        else:
            self.__plugin_name = get_mkdocs_plugin_name(self, config)

        logger = logging.getLogger(f"mkdocs.plugins.{__name__}")
        self.__log = PrefixedLogger(f"partial_docs[{self.__plugin_name}]", logger)

        if self.config.edit_url_template is not None:
            self.__edit_url_template = self.config.edit_url_template
        if self.config.blog_categories is not None:
            self.__blog_categories = self.config.blog_categories

        self.__blog_integration.init(config, self.__docs_path, self.__plugin_name, self.__blog_categories)

        spellcheck_plugin = get_mkdocs_plugin(SPELLCHECK_ENTRYPOINT_NAME, SPELLCHECK_ENTRYPOINT_SHIM, config)
        if spellcheck_plugin is not None and not mkdocs_partial.SpellCheckShimActive:
            self.__log.info("Enabling `mkdocs_spellcheck` integration.")
            mkdocs_partial.SpellCheckShimActive = True

        macros_plugin = get_mkdocs_plugin(MACROS_ENTRYPOINT_NAME, MACROS_ENTRYPOINT_SHIM, config)
        if macros_plugin is not None:
            self.__log.info("Detected configured mkdocs_macros plugin. Registering filters")
            macros_plugin.register_docs_package(self.__plugin_name, self)

    def on_serve(
        self, server: LiveReloadServer, /, *, config: MkDocsConfig, builder: Callable
    ) -> LiveReloadServer | None:
        if not self.config.enabled:
            return server

        if self.config.docs_path is not None:
            if not self.__blog_integration.watch(server, config):
                server.watch(self.config.docs_path)
        return server

    def on_files(self, files: Files, /, *, config: MkDocsConfig) -> Files | None:
        if not self.config.enabled:
            return files

        self.__files = []
        if not os.path.isdir(self.__docs_path):
            return files

        for file_path in glob.glob(os.path.join(self.__docs_path, "**/*.md"), recursive=True):
            self.add_md_file(file_path, files, config)
        for file_path in glob.glob(os.path.join(self.__docs_path, "**/*.png"), recursive=True):
            self.add_media_file(file_path, files, config)

        if mkdocs_partial.SpellCheckShimActive:
            known_words = os.path.join(self.__docs_path, "known_words.txt")
            if os.path.isfile(known_words):
                self.add_media_file(known_words, files, config)

        return files

    def add_md_file(self, file_path, files: Files, config):
        if self.__blog_integration.is_blog_related(file_path):
            return

        md = frontmatter.loads(Path(file_path).read_text(encoding="utf8"))
        src_uri, is_index = self.get_src_uri(file_path)
        existing_file = files.src_uris.get(src_uri, None)
        if existing_file is not None:
            existing = frontmatter.loads(existing_file.content_string)
            content = existing.content + "\n\n" + md.content
            if len(self.H1_TITLE.findall(content)) > 1:
                content = self.TITLE.sub("##", content)

            meta = dict(existing.metadata)
            meta.update(md.metadata)
            md = frontmatter.Post(content)
            md.metadata.update(meta)
            files.remove(existing_file)
        if is_index and self.__title is not None:
            md.metadata["title"] = self.__title
        md.metadata["partial"] = True
        md.metadata["docs_package"] = self.__plugin_name
        file = File.generated(config=config, src_uri=src_uri, content=frontmatter.dumps(md))
        files.append(file)
        self.__files.append(file)

        redirects_plugin = get_mkdocs_plugin(REDIRECTS_ENTRYPOINT_NAME, REDIRECTS_ENTRYPOINT_SHIM, config)
        if redirects_plugin is not None:
            normalized_redirects = [
                f"{self.directory}/{redirect}".replace("\\", "/").replace("//", "/")
                for redirect in md.metadata.get("redirects", [])
            ]
            redirects_plugin.add_redirects(files, file, normalized_redirects, config)

    def on_page_context(
        self, context: TemplateContext, /, *, page: Page, config: MkDocsConfig, nav: Navigation
    ) -> TemplateContext | None:
        if page.file in self.__files:
            path = os.path.relpath(page.file.src_path, self.config.directory)
            path = self.get_edit_url_template_path(path)
        else:
            path = self.__blog_integration.get_src_path(page.file.src_path)
        if self.__edit_url_template is not None and path is not None:
            page.edit_url = str(self.__edit_url_template).format(path=path)
        return context

    def add_media_file(self, path, files, config):
        if self.__blog_integration.is_blog_related(path):
            return
        src_uri = self.get_src_uri(path)[0]
        existing_file = files.src_uris.get(src_uri, None)
        if existing_file is not None:
            plugin_info = ""
            if existing_file.generated_by is not None:
                plugin_info = f"registered by '{existing_file.generated_by}' plugin"
            self.__log.warning(
                f"Can not register file '{src_uri}' as there is already file with same path.{plugin_info}"
            )
            return
        file = File.generated(config=config, src_uri=src_uri, content=Path(path).read_bytes())
        files.append(file)

    def get_src_uri(self, file_path):
        is_index = False
        path = normalize_path(os.path.relpath(file_path, self.__docs_path))
        if path.lower() == "index.md":
            is_index = True
        path = normalize_path(os.path.join(self.__directory, path)).lstrip("/")
        return path, is_index

    def get_edit_url_template_path(self, path):
        return normalize_path(os.path.relpath(path, self.__directory))
