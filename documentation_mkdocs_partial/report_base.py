import os
import re
import shutil
from abc import ABC
from html import escape
from pathlib import Path

import jinja2
from hurry.filesize import size


class ReportBase(ABC):
    def __init__(self, output_path, templates_dir, template_filters=None, stdout_reports=False):
        self.stdout_reports = stdout_reports
        if template_filters is None:
            template_filters = {}

        self.output_path = output_path
        self.templates_dir = templates_dir
        template_loader = jinja2.FileSystemLoader(searchpath=templates_dir)
        self.__template_environment = jinja2.Environment(
            loader=template_loader, trim_blocks=True, lstrip_blocks=False, newline_sequence="\r\n"
        )
        filters = {
            "nowrap": self.nowrap,
            "table_safe": self.table_safe,
            "eclipse": self.eclipse,
            "remove_tags": self.remove_tags,
            "email_contact": self.email_contact,
            "phone_contact": self.phone_contact,
            "title_contact": self.title_contact,
            "escape": self.escape_markdown,
            "escape_new_lines": self.escape_new_lines,
            "filesize": size,
        }
        filters.update(template_filters)
        for name, method in filters.items():
            self.__template_environment.filters[name] = method

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

    def email_contact(self, value, markdown=True):
        if value is None:
            return ""
        if value["profile"] is None:
            try:
                name = value["email"]
                name = re.sub(r"\.", " ", name)
                name = re.sub("@.*", "", name)
                name = name.title()
                return f"[{name}](mailto:{value['email']})" if markdown else f"{name}"
            # flake8: noqa E722
            except:  # pylint: disable=bare-except
                return value

        return (
            f"[{value['profile']['displayName']}](mailto:{value['email']})"
            if markdown
            else value["profile"]["displayName"]
        )

    def phone_contact(self, value):
        if value["profile"] is None:
            return "N/A"

        phones = [value["profile"]["mobilePhone"]] + value["profile"]["businessPhones"]
        phones = [p for p in phones if p is not None and p != ""]
        phones = ", ".join(phones)
        return f"{phones}"

    def title_contact(self, value):
        if value["profile"] is None:
            return "N/A"

        return value["profile"].get("jobTitle", "N/A")

    def touch(self, path):
        basedir = os.path.dirname(path)
        if not os.path.exists(basedir):
            os.makedirs(basedir)
        with open(path, "a"):
            os.utime(path, None)

    def copy(self, resource_path, output_path):
        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path))
        shutil.copyfile(os.path.join(self.templates_dir, resource_path), output_path)

    def write_template(self, template, /, *, name=None, **args):
        template_vars = {}
        if args is None:
            args = {}
        template_vars.update(args)
        report_file = self.output_path
        if report_file is not None:
            if os.path.isdir(report_file) or report_file[-1] == "/" or report_file[-1] == "\\":
                report_file = os.path.join(report_file, name)

            Path(os.path.dirname(report_file)).mkdir(parents=True, exist_ok=True)

        template = self.__template_environment.get_template(template)
        if report_file is not None:
            template.stream(template_vars).dump(report_file)
            with open(report_file, encoding="utf-8") as file:
                content = file.read()
        else:
            content = template.render(template_vars)
        if self.stdout_reports:
            print(content)
        return content
