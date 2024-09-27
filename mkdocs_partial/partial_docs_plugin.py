# pylint: disable=unused-argument
import traceback
from typing import Callable, Dict, List, cast

from mkdocs import plugins
from mkdocs.config import Config, config_options
from mkdocs.config.config_options import Plugins
from mkdocs.config.defaults import MkDocsConfig
from mkdocs.exceptions import PluginError
from mkdocs.plugins import BasePlugin, get_plugin_logger
from mkdocs.structure.nav import Navigation
from mkdocs.structure.pages import Page
from mkdocs.utils.templates import TemplateContext

from mkdocs_partial.docs_package_plugin import DocsPackagePlugin, DocsPackagePluginConfig

log = get_plugin_logger("partial_docs")


class PartialDocsPluginConfig(Config):
    enabled = config_options.Type(bool, default=True)
    packages = config_options.DictOfItems(config_options.SubConfig(DocsPackagePluginConfig), default={})


class PartialDocsPlugin(BasePlugin[PartialDocsPluginConfig]):
    docs_path_overrides: Dict[str, str] = {}

    def __init__(self):
        self.is_serve = False
        self.is_dirty = False

    def on_startup(self, *, command, dirty):
        if not self.config.enabled:
            return
        self.is_serve = command == "serve"
        self.is_dirty = dirty

    def on_shutdown(self) -> None:
        pass

    def on_page_context(
        self, context: TemplateContext, /, *, page: Page, config: MkDocsConfig, nav: Navigation
    ) -> TemplateContext | None:
        return context

    @plugins.event_priority(100)
    def on_config(self, config):
        if not self.config.enabled:
            return

        global_plugins: Plugins = cast(Plugins, dict(config._schema)["plugins"])
        assert isinstance(global_plugins, Plugins)

        self.docs_package_plugins: dict[str, BasePlugin] = {}
        try:
            for name, plugin in self._load(global_plugins):
                if plugin.config.enabled:
                    src = ""
                    if plugin.config.docs_path is not None:
                        src = f" from source path '{plugin.config.docs_path}'"
                    log.info(f"Injecting doc package {name} to '{plugin.directory}' directory{src}.")
                    self.docs_package_plugins[name] = plugin
        except Exception:
            raise PluginError(traceback.format_exc())  # pylint: disable=raise-missing-from

        # Invoke `on_startup`
        command = "serve" if self.is_serve else "build"
        for method in global_plugins.plugins.events["startup"]:
            plugin = self._get_plugin(method)

            if plugin and plugin in self.docs_package_plugins.values():
                method(command=command, dirty=self.is_dirty)

    # Load doc package plugins
    def _load(self, option: Plugins) -> List[tuple[str, DocsPackagePlugin]]:
        for entrypoint in option.installed_plugins.values():
            try:
                plugin_class = entrypoint.load()
            except ModuleNotFoundError:
                continue
            if issubclass(plugin_class, DocsPackagePlugin) and plugin_class != DocsPackagePlugin:
                plugin_config: DocsPackagePluginConfig = self.config.packages.setdefault(
                    entrypoint.name, DocsPackagePluginConfig()
                )
                if entrypoint.name in PartialDocsPlugin.docs_path_overrides:
                    plugin_config.docs_path = PartialDocsPlugin.docs_path_overrides[entrypoint.name]

                name, plugin = option.load_plugin_with_namespace(entrypoint.name, plugin_config.data)
                yield name, cast(DocsPackagePlugin, plugin)

    def _get_plugin(self, method: Callable):
        return getattr(method, "__self__", None)