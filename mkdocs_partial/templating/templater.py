import os
from abc import ABC
from argparse import ArgumentError
from io import StringIO
from pathlib import Path
from typing import Callable, Dict

import jinja2

from mkdocs_partial.templating.templater_extension import TemplaterExtension


class Templater(ABC):
    def __init__(self, templates_dir, template_filters: Dict[str, Callable] = None, output_path=None, **template_args):
        if template_filters is None:
            template_filters = {}
        if output_path is None:
            output_path = os.getcwd()
        self.output_path = output_path
        self.templates_dir = templates_dir
        template_loader = jinja2.FileSystemLoader(searchpath=templates_dir)
        self.__template_environment = jinja2.Environment(
            loader=template_loader, trim_blocks=True, lstrip_blocks=False, newline_sequence="\r\n"
        )
        self.__template_args = template_args
        filters = {}
        filters.update(template_filters)
        for name, method in filters.items():
            self.__template_environment.filters[name] = method

    def extend(self, extension: TemplaterExtension):
        for name, method in extension.filters:
            self.__template_environment.filters[name] = method
        self.__template_args.update(extension.args)
        return self

    def write_template(self, template: str, /, *, path=None, **args):
        if template is None or template == "":
            raise ArgumentError(template, "template should not be None")
        template_vars = {}
        if path is None:
            path = template
        template_vars.update(args)
        report_file = path
        if not os.path.isabs(path):
            report_file = os.path.normpath(os.path.join(self.output_path, path))
        Path(os.path.dirname(report_file)).mkdir(parents=True, exist_ok=True)
        with open(report_file, "w", encoding="utf-8") as file:
            self.__template(template, file, **args)
        return report_file

    def template(self, template, **args):
        stream = StringIO()
        self.__template(template, stream, **args)
        stream.seek(0)
        return stream.read()

    def template_string(self, template, **args):
        stream = StringIO()
        self.__template(template, stream, is_str=True, **args)
        stream.seek(0)
        return stream.read()

    def __template(self, template, stream, is_str=False, **args):
        template_vars = {}
        if args is None:
            args = {}
        args = dict(args)
        args.update(self.__template_args)
        template_vars.update(args)
        template = (
            self.__template_environment.from_string(template)
            if is_str
            else self.__template_environment.get_template(template)
        )
        template.stream(template_vars).dump(stream)
