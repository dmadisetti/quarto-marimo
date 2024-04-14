#! /usr/bin/env nix-shell
#! nix-shell -i python3 -p python3Packages.marimo

import sys
import os
import ast

from marimo._ast import codegen
import textwrap


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
        md = textwrap.dedent(const_string(value.args))
        if callout:
            md = f"""
::: {{.callout-{callout}}}
{md}
:::"""
        return md
    except:  # noqa: E722
        return None


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python script.py <filename> [--native-callout]")
        sys.exit(1)

    filename = sys.argv[1]
    if not os.path.isfile(filename):
        print(f"Error: File '{filename}' does not exist.")
        sys.exit(1)
    native_callout = sys.argv[-1] == "--native-callout"

    app = codegen.get_app(filename)

    document = """---
format: html
filters:
  - marimo/quarto
---
"""
    for cell_data in app._cell_manager.cell_data():
        cell = cell_data.cell
        code = cell_data.code
        markdown = get_markdown(cell, code, native_callout)
        if markdown:
            document += markdown + "\n"
        else:
            document += f"""
```{{marimo}}
{code}
```
"""
    return document


if __name__ == "__main__":
    print(main())
