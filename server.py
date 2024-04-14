#! /usr/bin/env nix-shell
#! nix-shell -i python3 -p python3Packages.marimo python3Packages.flask python3Packages.matplotlib

import marimo
from flask import Flask, request, jsonify

import re
import os

from marimo._ast import codegen
from marimo._ast.cell import CellConfig
import tempfile

from marimo._output.formatters.formatters import (
    register_formatters,
)
from marimo._output.formatting import try_format
import marimo as mo

# Maybe do over sockets instead of web?
# Feels very hacky

app = Flask(__name__)

# Just need globals
sources = {}
lookups = {}


@app.route("/run", methods=["POST"])
def run():
    data = request.get_json()
    code = data.get("code", None)
    key = data.get("key", None).strip()
    print("run", key, code)
    if code is None or key is None:
        return jsonify({"error": "No code provided"}), 400
    sources[key] = code
    return ""


@app.route("/lookup", methods=["POST"])
def lookup():
    data = request.get_json()
    key = data.get("key", None).strip()
    if key is None or key not in lookups:
        return jsonify({"type": "html", "value": "error: No key provided"}), 400
    if lookups[key] is None:
        return jsonify({"type": "html", "value": ""})

    data = lookups[key]
    output = try_format(data)
    # Ideally handle this client side, but just a sanity check
    if output.mimetype == "image/png":
        return jsonify({"type": "figure", "value": f"{output.data}"})

    # Default to whatever the output was, assuming html
    return jsonify({"type": "html", "value": f"{mo.as_html(data)}"})


@app.route("/execute", methods=["GET"])
def execute():

    keys, code = list(zip(*sources.items()))
    generated = codegen.generate_filecontents(
        code,
        keys,
        [CellConfig() for _ in range(len(sources))],
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py") as f:
        f.write(generated)
        f.seek(0)
        app = codegen.get_app(f.name)

    register_formatters()
    for key, output in zip(keys, app.run()[0]):
        lookups[key] = output
    return ""


@app.route("/flush", methods=["GET"])
def flush():
    lookups.clear()
    sources.clear()
    return ""


@app.route("/assets", methods=["GET"])
def assets():
    # Read the HTML file
    with open(f"{marimo.__path__[0]}/_static/index.html", "r") as file:
        html_content = file.read()
    (js,) = re.findall(r"index-.*\.js", html_content)
    (css,) = re.findall(r"index-.*\.css", html_content)
    base = f"https://cdn.jsdelivr.net/npm/@marimo-team/frontend@{marimo.__version__}/dist/assets/"
    dev_server = os.environ.get("QUARTO_MARIMO_DEBUG_ENDPOINT")
    js = f"{base}{js}"
    if dev_server:
        js = f"http://{dev_server}/src/main.tsx"
    return f"""
      <div id="root" style="display:none"></div>
      <marimo-mode data-mode="read" hidden=""></marimo-mode>
      <marimo-filename hidden="">quarto app</marimo-filename>
      <marimo-version data-version="{marimo.__version__}" hidden=""></marimo-version>
      <marimo-user-config data-config="{{}}" hidden=""> </marimo-user-config>
      <marimo-app-config data-config="{{}}"> </marimo-app-config>
      <script data-marimo="true">
        window.__MARIMO_STATIC__ = {{}};
        window.__MARIMO_STATIC__.version = "{marimo.__version__}";
        window.__MARIMO_STATIC__.notebookState = {{}};
        window.__MARIMO_STATIC__.assetUrl = "{base}";
        window.__MARIMO_STATIC__.files = {{}};
      </script>

      <marimo-code hidden="">
      </marimo-code>

      <link rel="stylesheet" crossorigin="anonymous" href="{base}{css}">
      <script type="module" crossorigin="anonymous" src="{js}"></script>
  """


if __name__ == "__main__":
    app.run(debug=True, port=6000)
