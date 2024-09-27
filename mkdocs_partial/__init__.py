import re

from mkdocs_partial.mkdcos_helpers import replace_mkdocs_plugin_entrypoint

PACKAGE_NAME_RESTRICTED_CHARS = re.compile(r"[^A-Za-z0-9+_-]")
MODULE_NAME_RESTRICTED_CHARS = re.compile(r"[^a-z0-9+_]")
PACKAGE_NAME = re.compile(r"^[A-Za-z0-9+_-]+$")

SPELLCHECK_ENTRYPOINT_NAME = "spellcheck"
SPELLCHECK_ENTRYPOINT_VALUE = "mkdocs_spellcheck.plugin:SpellCheckPlugin"
SPELLCHECK_ENTRYPOINT_SHIM = "mkdocs_partial.integrations.spellcheck_plugin_shim:SpellCheckShim"
SpellCheckShimActive = False  # pylint: disable=invalid-name

MACROS_ENTRYPOINT_NAME = "macros"
MACROS_ENTRYPOINT_VALUE = "mkdocs_macros.plugin:MacrosPlugin"
MACROS_ENTRYPOINT_SHIM = "mkdocs_partial.integrations.macros_plugin_shim:MacrosPluginShim"

REDIRECTS_ENTRYPOINT_NAME = "redirects"
REDIRECTS_ENTRYPOINT_VALUE = "mkdocs_redirects.plugin:RedirectPlugin"
REDIRECTS_ENTRYPOINT_SHIM = "mkdocs_partial.integrations.redirect_plugin_shim:RedirectPluginShim"

replace_mkdocs_plugin_entrypoint(SPELLCHECK_ENTRYPOINT_NAME, SPELLCHECK_ENTRYPOINT_VALUE, SPELLCHECK_ENTRYPOINT_SHIM)
replace_mkdocs_plugin_entrypoint(REDIRECTS_ENTRYPOINT_NAME, REDIRECTS_ENTRYPOINT_VALUE, REDIRECTS_ENTRYPOINT_SHIM)
replace_mkdocs_plugin_entrypoint(MACROS_ENTRYPOINT_NAME, MACROS_ENTRYPOINT_VALUE, MACROS_ENTRYPOINT_SHIM)
