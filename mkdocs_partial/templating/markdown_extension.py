import re
from html import escape
from typing import Callable, Dict

from mkdocs_partial.templating.templater_extension import TemplaterExtension


class TemplaterMarkdownExtension(TemplaterExtension):
    @property
    def filters(self) -> Dict[str, Callable]:
        yield "escape_markdown", self.escape_markdown
        yield "escape_new_lines", self.escape_new_lines
        yield "nowrap", self.nowrap
        yield "table_safe", self.table_safe
        yield "eclipse", self.eclipse
        yield "remove_tags", self.remove_tags

    def escape_markdown(self, text):
        text = escape(str(text))
        return text.replace("|", "&#124;").replace("_", "&#95;").replace("*", "&#42;")

    def escape_new_lines(self, text):
        return text.replace("\r\n", "<br/>").replace("\n", "<br/>").rstrip("<br/>")

    def nowrap(self, text):
        return text.replace("-", "&#x2011;").replace(" ", "&#160;")

    def table_safe(self, text):
        return text.replace("|", "\\|")

    def eclipse(self, value, length=48, add_spaces=False):
        if len(value) > length:
            return value[: length - 3] + "..."

        return value.ljust(length) if add_spaces else value

    def remove_tags(self, value):
        return re.sub("\\[.*?\\]\\s*", "", value)
