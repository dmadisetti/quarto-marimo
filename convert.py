#! /usr/bin/env nix-shell
#! nix-shell -i python3 -p python3Packages.marimo

import marimo

import sys
import re
import os

from marimo._ast import codegen
import textwrap

prefix_kinds = ["", "f", "r", "fr", "rf"]

quote_kinds = [
    ['"""', '"""'],
    ["'''", "'''"],
    ['"', '"'],
    ["'", "'"],
]

pairs = [(prefix + start, end) for prefix in prefix_kinds for start, end in quote_kinds]

regexes = [
    (
        start,
        re.compile(
            f"^mo\\.md\\(\\s*{re.escape(start)}(.*){re.escape(end)}\\s*\\)$", re.DOTALL
        ),
    )
    for start, end in pairs
]


def get_markdown(cell, code):
    if not (cell.refs == {"mo"} and not cell.defs):
        return None
    markdown_lines = [
        line for line in code.strip().split("\n") if line.startswith("mo.md(")
    ]
    if len(markdown_lines) > 1:
        return Nonw
    for _, regex in regexes:
      search = regex.search(code)
      if search:
          return textwrap.dedent(search.group(1))
    return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <filename>")
        sys.exit(1)

    filename = sys.argv[1]
    if not os.path.isfile(filename):
        print(f"Error: File '{filename}' does not exist.")
        sys.exit(1)

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
        markdown = get_markdown(cell, code)
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
