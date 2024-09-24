import glob
import os
import posixpath
import shutil
from abc import ABC
from pathlib import Path
from typing import List

import frontmatter
import watchdog.events
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.livereload import LiveReloadServer

from documentation_mkdocs_partial.mkdcos_helpers import get_mkdocs_plugin, mkdocs_watch_ignore_path


class MaterialBlogsIntegration(ABC):
    def __init__(self):
        super().__init__()
        self.__enabled: bool = False

        self.__partial: str | None = None
        self.__source: str | None = None
        self.__target: str | None = None
        self.__category: str | None = None
        self.__docs_path: str | None = None
        self.__docs_dir: str | None = None
        self.__stop = lambda *args: None

    def init(self, config: MkDocsConfig, docs_path: str, name: str, category: str):
        blog_plugin = get_mkdocs_plugin("material/blog", "material.plugins.blog.plugin:BlogPlugin", config)
        self.__enabled = blog_plugin is not None
        if self.__enabled:
            root = posixpath.normpath(blog_plugin.config.data.get("blog_dir", "blog"))
            blog_posts = blog_plugin.config.data.get("post_dir", "{blog}/posts").format(blog=root)
            self.__source = os.path.join(docs_path, blog_posts)
            self.__docs_dir = config.docs_dir
            self.__partial = os.path.join(self.__docs_dir, blog_posts, "partial")
            self.__target = os.path.join(self.__partial, name)
            self.__category = category if category != "" else None
            self.__docs_path = docs_path
        return self.__enabled

    def watch(self, server: LiveReloadServer, config: MkDocsConfig):
        if not self.__enabled:
            return False
        mkdocs_watch_ignore_path(server, config, self.__source, self.__docs_path)

        def blogs_callback(event: watchdog.events.FileSystemEvent):
            # ignore directory events - teh do not affect blogs
            if event.is_directory:
                return

            # ignore events for files out of self.__source, likely self.__source was created after
            # watch started and watched dir its parent
            if not (event.src_path is not None and Path(event.src_path).is_relative_to(self.__source)) and not (
                event.dest_path is not None and Path(event.dest_path).is_relative_to(self.__source)
            ):
                return

            self.sync()

        handler = watchdog.events.FileSystemEventHandler()
        handler.on_any_event = blogs_callback  # type: ignore[method-assign]

        # If source dir does not exist get up the tree in case it would be created later
        source_watch_dir = self.__source
        while not os.path.isdir(source_watch_dir) and source_watch_dir is not None:
            if os.path.dirname(source_watch_dir) != source_watch_dir:
                source_watch_dir = os.path.dirname(source_watch_dir)
            else:
                source_watch_dir = None

        if source_watch_dir is not None:
            watch = server.observer.schedule(handler, source_watch_dir, recursive=True)

            def unsubscribe():
                try:
                    server.observer.unschedule(watch)
                except KeyError:
                    # At the moment mkdocs unschedules all watches,
                    # unsubscribe is just in case it changes in later releases
                    pass
                self.__stop = lambda *args: None

            self.__stop = unsubscribe
        return True

    def sync(self):
        if not self.__enabled:
            return
        posts = []
        for file_path in glob.glob(os.path.join(self.__source, "**/*.md"), recursive=True):
            if os.path.isfile(file_path):
                md = frontmatter.loads(Path(file_path).read_text(encoding="utf8"))
                abs_path = os.path.join(self.__target, os.path.relpath(file_path, self.__source))
                Path(os.path.dirname(abs_path)).mkdir(parents=True, exist_ok=True)
                if self.__category is not None:
                    categories: List[str] = md.metadata.setdefault("categories", [])
                    if not isinstance(categories, list):
                        categories = []
                        md.metadata["categories"] = categories
                    categories.insert(0, self.__category)
                if not os.path.isfile(abs_path) or Path(abs_path).read_text(encoding="utf8") != frontmatter.dumps(md):
                    frontmatter.dump(md, abs_path)
                posts.append(os.path.normpath(abs_path))
        for file_path in glob.glob(os.path.join(self.__target, "**/*.md"), recursive=True):
            if os.path.isfile(file_path):
                if os.path.normpath(file_path) not in posts:
                    os.remove(file_path)

    def is_blog_post(self, path):
        return self.__enabled and Path(path).is_relative_to(self.__source)

    def shutdown(self):
        if not self.__enabled:
            return
        self.stop()

    def get_src_path(self, path):
        if not self.__enabled:
            return None
        path = os.path.join(self.__docs_dir, path)
        if Path(path).is_relative_to(self.__target):
            path = os.path.join(self.__source, os.path.relpath(path, self.__target))
            path = os.path.relpath(path, self.__docs_path)
            return path
        return None

    def stop(self):
        self.__stop()
        if self.__enabled:
            shutil.rmtree(self.__target, ignore_errors=True)
            if os.path.isdir(self.__partial) and not os.listdir(self.__partial):
                shutil.rmtree(self.__partial, ignore_errors=True)
        self.__enabled = False
