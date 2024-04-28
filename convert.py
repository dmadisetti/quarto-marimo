#! /usr/bin/env nix-shell
#! nix-shell -i python3 -p python3Packages.marimo

import sys
import os
import ast
import re

from marimo._ast import codegen
from marimo._cli.ipynb_to_marimo import convert_from_path
import textwrap
import tempfile


def get_code_guard(code):
    guard = "```"
    while guard in code:
        guard += "`"
    return guard


def format_filename(filename):
    base_name = os.path.basename(filename)
    name, ext = os.path.splitext(base_name)
    if ext in [".ipynb", ".py"]:
        name = re.sub("[-_]", " ", name)
        name = name.title()
    else:
        name = "Marimo Notebook"
    return name


def const_string(args):
    (inner,) = args
    if hasattr(inner, "values"):
        (inner,) = inner.values
    return inner.value


def get_markdown(cell, code, native_callout=False):
    if not (cell.refs == {"mo"} and not cell.defs):
        return None
    markdown_lines = [
        line for line in code.strip().split("\n") if line.startswith("mo.md(")
    ]
    if len(markdown_lines) > 1:
        return None

    code = code.strip()
    try:
        (body,) = ast.parse(code).body
        callout = None
        if body.value.func.attr == "md":
            value = body.value
        elif body.value.func.attr == "callout":
            if not native_callout:
                return None
            if body.value.args:
                callout = const_string(body.value.args)
            else:
                (keyword,) = body.value.keywords
                assert keyword.arg == "kind"
                callout = const_string([keyword.value])
            value = body.value.func.value
        else:
            return None
        assert value.func.value.id == "mo"
        # Dedent behavior is a little different that in marimo js, so handle
        # accordingly.
        md = const_string(value.args).split("\n")
        md = [line.rstrip() for line in md]
        md = textwrap.dedent(md[0]) + "\n" + textwrap.dedent("\n".join(md[1:]))
        if callout:
            md = f"""
::: {{.callout-{callout}}}
{md}
:::"""
        return md
    except:  # noqa: E722
        return None


def to_markdown(filename, native_callout=False):
    app = codegen.get_app(filename)
    document = f"""---
title: {format_filename(filename)}
format: html
filters:
  - marimo/quarto
---
"""
    for cell_data in app._cell_manager.cell_data():
        cell = cell_data.cell
        code = cell_data.code
        if cell:
            markdown = get_markdown(cell, code, native_callout)
            if markdown:
                document += markdown + "\n"
            else:
                guard = get_code_guard(code)
                document += f"""
{guard}{{marimo}}
{code}
{guard}
"""
    return document


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 4:
        print("Usage: convert <filename> [--to-marimo|--native-callout]?")
        sys.exit(1)

    filename = sys.argv[1]
    # Exists captures file descriptors in addition to just files.
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' does not exist.")
        sys.exit(1)

    to_app = "--to-marimo" in sys.argv[2:]
    native_callout = "--native-callout" in sys.argv[2:]

    if filename.endswith(".py"):
        assert not to_app, "Cannot convert a Python file to Marimo"
        return to_markdown(filename, native_callout)

    # Fallback to ipynb or whatever else marimo can do
    app = convert_from_path(filename)
    if to_app:
        return app
    # marimo requires a file for parsing.
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py") as f:
        f.write(app)
        f.seek(0)
        return to_markdown(f.name, native_callout)


if __name__ == "__main__":
    print(main())
