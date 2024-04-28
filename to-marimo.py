#! /usr/bin/env nix-shell
#! nix-shell -i python3 -p python3Packages.marimo

import sys
import os

from marimo._ast import codegen
from marimo._ast.cell import CellConfig

# Markdown is a dependency of marimo, as such we utilize it as much as possible
# to parse markdown.
from markdown import Markdown
from markdown.util import Registry, HTML_PLACEHOLDER_RE
from markdown.blockparser import BlockParser
from markdown.blockprocessors import BlockProcessor
from markdown.treeprocessors import Treeprocessor
from markdown.extensions.meta import MetaPreprocessor

# As are extensions
from pymdownx.superfences import SuperFencesCodeExtension

# Native to python
from xml.etree.ElementTree import Element, SubElement
from dataclasses import dataclass

from typing import Any

MARIMO_MD = "marimo-md"
MARIMO_CODE = "marimo-code"


def _is_code_tag(text):
    head = text.split("\n")[0].strip()
    return head.endswith("{marimo}")


class ExpandAndClassifyProcessor(BlockProcessor):
    """Seperates code blocks and markdown blocks."""

    stash: dict[str, Any]
    yaml_meta: bool

    def test(*args) -> bool:
        return True

    def run(self, parent: Element, blocks: list[str]) -> None:

        text = []
        self.yaml_meta = True

        def add_paragraph():
            # On first markdown block, check if it contains yaml
            # (or partially parsed yaml).
            if self.yaml_meta:
                self.yaml_meta = False
                if text[-1] == "---":
                    text.clear()
                    return
            if text:
                paragraph = SubElement(parent, MARIMO_MD)
                paragraph.text = "\n".join(text)
                text.clear()

        # Operate on line basis, not block basis, but use block processor
        # instead of preprocessor, because we still want to operate on the
        # xml tree.
        for line in "\n".join(blocks).split("\n"):
            # Superfences replaces code blocks with a placeholder,
            # Check for the placeholder, and ensure it is a marimo code block,
            # otherwise consider it as markdown.
            if HTML_PLACEHOLDER_RE.match(line.strip()):
                lookup = line.strip()[1:-1]
                code = self.stash[lookup][0]
                if _is_code_tag(code):
                    add_paragraph()
                    code_block = SubElement(parent, MARIMO_CODE)
                    code_block.text = "\n".join(code.split("\n")[1:-1])
                    # If code block, then it cannot be the initial yaml.
                    self.yaml_meta = False
                else:
                    text.extend(code.split("\n"))
            else:
                text.append(line)
        add_paragraph()
        # Flush to indicate all blocks have been processed.
        blocks.clear()


class IdentityParser(Markdown):
    def build_parser(self) -> Markdown:
        """
        Creates blank registries as a base.

        Note that envoked by itself, will create an infinite loop, since
        block-parsers will never dequeue the extracted blocks.
        """
        self.preprocessors = Registry()
        self.parser = BlockParser(self)
        self.inlinePatterns = Registry()
        self.treeprocessors = Registry()
        self.postprocessors = Registry()
        return self


def _tree_to_app(root: Element):
    sources = []
    for child in root:
        source = child.text
        if source.strip() == "":
            continue
        if child.tag == MARIMO_MD:
            source = child.text.replace('"""', '\\"\\"\\"')
            source = "\n".join(
                [
                    "mo.md(",
                    # r-string: a backslash is just a backslash!
                    codegen.indent_text('r"""'),
                    codegen.indent_text(source),
                    codegen.indent_text('"""'),
                    ")",
                ]
            )
        elif child.tag != MARIMO_CODE:
            raise Exception(f"Unknown tag: {child.tag}")
        sources.append(source)

    return codegen.generate_filecontents(
        sources,
        ["__" for _ in sources],
        [CellConfig() for _ in range(len(sources))],
    )


def build_marimo_parser(**kwargs):

    # Considering how ubiquitous "markdown" is, it's a little suprising the
    # internal structure isn't cleaner/ more modular. This "monkey-patching"
    # is comparable to some of the code in markdown extensions- and given this
    # library has been around since 2004, the internals should be relatively
    # stable.
    class _MarimoInstance(IdentityParser):
        output_formats = {
            "marimo": _tree_to_app,
        }

    md = _MarimoInstance(output_format="marimo", **kwargs)
    md.stripTopLevelTags = False

    # Note: MetaPreprocessor does not properly handle frontmatter yaml, so
    # cleanup occurs in the block-processor.
    md.preprocessors.register(MetaPreprocessor(md), "meta", 100)
    fences_ext = SuperFencesCodeExtension()
    fences_ext.extendMarkdown(md)
    # TODO: Consider adding the admonition extension, and integrating it with
    # mo.markdown callouts.

    block_processors = ExpandAndClassifyProcessor(md.parser)
    block_processors.stash = fences_ext.stash.stash
    md.parser.blockprocessors.register(block_processors, "marimo-processor", 10)

    return md


def to_marimo(text, **kwargs):
    md = build_marimo_parser(**kwargs)
    return md.convert(text)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide a file name as an argument.")
        sys.exit(1)

    file_name = sys.argv[1]

    if not os.path.isfile(file_name):
        print(f"No such file: {file_name}")
        sys.exit(1)

    with open(file_name, "r") as file:
        data = file.read()

    print(to_marimo(data))
