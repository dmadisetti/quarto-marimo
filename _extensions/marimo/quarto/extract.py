#!/home/dylan/downloads/manim/bin/python
# Only works with latest marimo version
# #!/usr/bin/env nix-shell
# #! nix-shell -i python3 -p python3Packages.marimo python3Packages.numpy python3Packages.pandas python3Packages.matplotlib

import sys
import re
import os
import json

import marimo
from marimo import MarimoIslandGenerator
from marimo._cli.convert.markdown import (
    MarimoParser,
    MARIMO_MD,
    SafeWrap,
)

from typing import Any, Callable, Union, Literal

import asyncio

# Native to python
from xml.etree.ElementTree import Element, SubElement


# See https://quarto.org/docs/computations/execution-options.html
default_config = {
    "eval": True,
    "echo": False,
    "output": True,
    "warning": True,
    "error": True,
    "include": True,
    # Particular to marimo
    "editor": False,
}


def extract_and_strip_quarto_config(block):
    pattern = r"^\s*\#\|\s*(.*?)\s*:\s*(.*?)(?=\n|\Z)"
    config = {}
    lines = block.split("\n")
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        source_match = re.search(pattern, line)
        if not source_match:
            break
        key, value = source_match.groups()
        config[key] = json.loads(value)
    return config, "\n".join(lines[i:])


def get_mime_render(global_options, stub, config, mime_sensitive):
    # Local supersede global supersedes default options
    config = {**global_options, **config}
    if not config["include"]:
        return {"type": "html", "value": ""}

    output = stub.output
    render_options = {
        "display_code": config["echo"],
        "reactive": config["eval"] and not mime_sensitive,
        "code": stub.code,
    }
    if config["output"] and mime_sensitive:
        if output.mimetype.startswith("image"):
            return {"type": "figure", "value": f"{output.data}", **render_options}
        if output.mimetype.startswith("text/plain"):
            return {"type": "para", "value": f"{output.data}", **render_options}
        if output.mimetype == "application/vnd.marimo+error":
            if config["error"]:
                return {
                    "type": "blockquote",
                    "value": f"{output.data}",
                    **render_options,
                }
            # Suppress errors otherwise
            return {"type": "para", "value": "", **render_options}

    elif output.mimetype == "application/vnd.marimo+error":
        if config["warning"]:
            print("Error", output.data, file=sys.stderr)
        if not config["error"]:
            return {"type": "html", "value": ""}

    # HTML as catch all default
    return {
        "type": "html",
        "value": stub.render(
            display_code=config["echo"],
            display_output=config["output"],
            is_reactive=render_options["reactive"],
        ),
        **render_options,
    }


def app_config_from_root(root: Element):
    # Extract meta data from root attributes.
    config_keys = {"title": "app_title", "marimo-layout": "layout_file"}
    config = {
        config_keys[key]: value for key, value in root.items() if key in config_keys
    }
    # Try to pass on other attributes as is
    config.update({k: v for k, v in root.items() if k not in config_keys})
    # Remove values particular to markdown saves.
    config.pop("marimo-version", None)
    return config


def build_export_with_mime_context(
    mime_sensitive: bool,
) -> Callable[[Element], SafeWrap]:
    def tree_to_pandoc_export(root: Element) -> SafeWrap:
        global_options = {**default_config, **app_config_from_root(root)}
        app = MarimoIslandGenerator()

        has_attrs: bool = False
        stubs = []
        for child in root:
            # only process code cells
            if child.tag == MARIMO_MD:
                continue
            # We only care about the disabled attribute.
            if child.attrib.get("disabled") == "true":
                # Don't even add to generator
                stubs.append(({"include": False}, None))
                continue
            # Check to see id attrs are defined on the tag
            has_attrs = has_attrs | bool(child.attrib.items())

            code = child.text
            config, code = extract_and_strip_quarto_config(code)
            stubs.append(
                (
                    config,
                    app.add_code(
                        code,
                        is_raw=True,
                    ),
                )
            )

        if has_attrs and global_options.get("warning", True):
            print(
                (
                    "Warning: Only the `disabled` codeblock attribute is utilized"
                    " for pandoc export. Be sure to set desired code attributes "
                    "in quarto form."
                ),
                file=sys.stderr,
            )

        _ = asyncio.run(app.build())
        dev_server = os.environ.get("QUARTO_MARIMO_DEBUG_ENDPOINT")
        header = app.render_head(
            _development_url=dev_server, version_override=marimo.__version__
        )

        return SafeWrap(
            {
                "header": header,
                "outputs": [
                    get_mime_render(global_options, stub, config, mime_sensitive)
                    for config, stub in stubs
                ],
                "count": len(stubs),
            }
        )

    return tree_to_pandoc_export


class MarimoPandocParser(MarimoParser):
    """Parses Markdown to marimo notebook string."""

    output_formats = {  # type: ignore[assignment, misc]
        "marimo-pandoc-export": build_export_with_mime_context(mime_sensitive=False),
        "marimo-pandoc-export-with-mime": build_export_with_mime_context(
            mime_sensitive=True
        ),
    }


def convert_from_md_to_pandoc_export(text: str, mime_sensitive: bool) -> dict[str, str]:
    if not text:
        return {"header": "", "outputs": []}
    if mime_sensitive:
        parser = MarimoPandocParser(output_format="marimo-pandoc-export-with-mime")
    else:
        parser = MarimoPandocParser(output_format="marimo-pandoc-export")
    return parser.convert(text)  # type: ignore[arg-type, return-value]


if __name__ == "__main__":
    assert len(sys.argv) == 3, f"Unexpected call format got {sys.argv}"
    _, reference_file, mime_sensitive = sys.argv
    mime_sensitive = mime_sensitive == "yes"
    file = sys.stdin.read()
    if not file:
        with open(reference_file, "r") as f:
            file = f.read()
    conversion = convert_from_md_to_pandoc_export(file, mime_sensitive)
    print(json.dumps(conversion))
