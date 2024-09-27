import glob
import os
from importlib.metadata import EntryPoint
from pathlib import Path

import watchdog
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.livereload import LiveReloadServer
from mkdocs.plugins import BasePlugin
from watchdog.events import FileSystemEvent


def normalize_path(path: str) -> str:
    return os.path.normpath(path).replace("\\", "/")


def get_mkdocs_plugin(name: str, entrypoint: str, config: MkDocsConfig) -> BasePlugin | None:
    plugin_entrypoint: EntryPoint = MkDocsConfig.plugins.installed_plugins.get(name, None)
    plugin = config.plugins.get(name, None)
    if (
        # macros entry point is registered by mkdocs_macros plugin
        plugin_entrypoint is not None
        and plugin_entrypoint.value == entrypoint
        # macros_plugin plugin is active
        and plugin is not None
    ):
        return plugin
    return None


def get_mkdocs_plugin_name(plugin: BasePlugin, config: MkDocsConfig):
    for name, instance in config.plugins.items():
        if instance == plugin:
            return name
    return None


def replace_mkdocs_plugin_entrypoint(name, entrypoint, new_entrypoint):
    found_entrypoint: EntryPoint = MkDocsConfig.plugins.installed_plugins.get(name, None)
    if found_entrypoint is not None and found_entrypoint.value == entrypoint:
        MkDocsConfig.plugins.installed_plugins[name] = EntryPoint(name, new_entrypoint, "mkdocs.plugins")
        if hasattr(MkDocsConfig.plugins, "plugins"):
            plugin = MkDocsConfig.plugins.plugins.get(name, None)
            assert plugin is None
        return True
    return False


def mkdocs_watch_ignore_path(server: LiveReloadServer, config: MkDocsConfig, ignore_dir, watched_dir=None):
    if watched_dir is None:
        watched_dir = config.docs_dir

    try:
        # Unwatch the directory watched by mkdocs.
        server.unwatch(watched_dir)
    except KeyError:
        # watched_dir is not watched
        pass

    def callback(event: FileSystemEvent):
        # Ignore events for directories as they do not affect mkdocs livereload
        if event.is_directory:
            return

        # Ignore events for files within `ignore_dir`
        if Path(event.src_path).is_relative_to(ignore_dir):
            return

        # Unwatch deleted files
        if event.event_type in [watchdog.events.EVENT_TYPE_DELETED, watchdog.events.EVENT_TYPE_MOVED]:
            try:
                server.unwatch(event.src_path)
            except KeyError:
                # src_path is not watched
                pass

        # Watch created files
        if event.event_type in [watchdog.events.EVENT_TYPE_CREATED]:
            server.watch(event.src_path)
        if event.event_type in [watchdog.events.EVENT_TYPE_MOVED]:
            server.watch(event.dest_path)

        # Touch mkdocs config file which is always watched to trigger rebuild and handle created/deleted files
        os.utime(config.config_file_path)
        return

    # Call mkdocs watch for files within in `watched_dir` tree except those in `ignore_dir`
    for path in glob.glob(os.path.join(watched_dir, "**/*"), recursive=True):
        if os.path.isfile(path) and not Path(path).is_relative_to(ignore_dir):
            server.watch(path)

    # Start watching `watched_dir` updating mkdocs watches for files that are not in `ignored_dir`
    handler = watchdog.events.FileSystemEventHandler()
    handler.on_moved = callback
    handler.on_deleted = callback
    handler.on_created = callback
    server.observer.schedule(handler, watched_dir, recursive=True)
