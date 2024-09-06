# pylint: disable=unused-argument
import glob
import inspect
import os
import re
from pathlib import Path
from typing import Callable

import frontmatter
from mkdocs.config import Config, config_options
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.livereload import LiveReloadServer
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import File, Files


class DocsPackagePluginConfig(Config):
    docs_path = config_options.Optional(config_options.Type(str))
    directory = config_options.Optional(config_options.Type(str))
    edit_url_template = config_options.Optional(config_options.Type(str))


class DocsPackagePlugin(BasePlugin[DocsPackagePluginConfig]):
    supports_multiple_instances = True
    H1_TITLE = re.compile(r"^#[^#]", flags=re.MULTILINE)
    TITLE = re.compile(r"^#", flags=re.MULTILINE)

    def __init__(self, directory=None, edit_url_template=None):
        script_dir = os.path.dirname(os.path.realpath(inspect.getfile(self.__class__)))
        resources_dir = os.path.join(script_dir, "docs")
        self.__docs_path = resources_dir
        self.__directory = directory
        self.__edit_url_template = edit_url_template
        self.__files: list[File] = []

    def on_config(self, _: MkDocsConfig) -> MkDocsConfig | None:
        if self.config.docs_path is not None:
            self.__docs_path = self.config.docs_path

        if self.config.directory is not None:
            self.__directory = self.config.directory
        if self.__directory is None:
            self.__directory = ""
        self.__directory = self.__directory.rstrip("/")

        if self.config.edit_url_template is not None:
            self.__edit_url_template = self.config.edit_url_template

    def on_serve(
        self, server: LiveReloadServer, /, *, config: MkDocsConfig, builder: Callable
    ) -> LiveReloadServer | None:
        if self.config.docs_path != "":
            server.watch(self.__docs_path, recursive=True)
        return server

    def on_files(self, files: Files, /, *, config: MkDocsConfig) -> Files | None:
        self.__files = []
        if not os.path.isdir(self.__docs_path):
            return files

        for file_path in glob.glob(os.path.join(self.__docs_path, "**/*.md"), recursive=True):
            self.add_md_file(file_path, files, config)
        for file_path in glob.glob(os.path.join(self.__docs_path, "**/*.png"), recursive=True):
            self.add_media_file(file_path, files, config)
        return files

    def add_md_file(self, file_path, files: Files, config):
        md = frontmatter.loads(Path(file_path).read_text(encoding="utf8"))
        src_uri = self.get_src_uri(file_path)
        existing_file = files.src_uris.get(src_uri, None)
        if existing_file is not None:
            existing = frontmatter.loads(existing_file.content_string)
            content = existing.content + "\n" + md.content
            meta = dict(existing.metadata)
            meta.update(md.metadata)
            md = frontmatter.Post(content)
            md.metadata.update(meta)

        file = File.generated(config=config, src_uri=src_uri, content=frontmatter.dumps(md))
        files.append(file)
        self.__files.append(file)

    def on_page_context(self, context, page, config, **kwargs):
        if page.file not in self.__files:
            return context
        path = os.path.relpath(page.file.src_path, self.config.directory)
        if self.__edit_url_template is not None and page.file in self.__files:
            page.edit_url = str(self.__edit_url_template).format(path=self.get_edit_url_template_path(path))
        return context

    def add_media_file(self, path, files, config):
        files.append(
            File.generated(
                config=config,
                src_uri=self.get_src_uri(path),
                content=Path(path).read_bytes(),
            )
        )

    def get_src_uri(self, file_path):
        path = os.path.relpath(file_path, self.__docs_path)
        return os.path.join(self.__directory, path).replace("\\", "/").lstrip("/")

    def get_edit_url_template_path(self, path):
        return os.path.relpath(path, self.__directory).replace("\\", "/")
