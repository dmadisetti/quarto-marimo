#! /usr/bin/env nix-shell
#! nix-shell -i python3 -p python3Packages.marimo python3Packages.flask python3Packages.matplotlib

from flask import Flask, request, jsonify

import re
import os
import tempfile
import urllib.parse

from marimo._ast import codegen
from marimo._ast.cell import CellConfig

from marimo._output.formatters.formatters import (
    register_formatters,
)
from marimo._output.formatting import try_format
import marimo as mo

from marimo import (
    experimental_MarimoIslandGenerator as MarimoIslandGenerator
)

import asyncio

# Maybe do over sockets instead of web?
# Feels very hacky

app = Flask(__name__)

# Just need globals
stubs = {}
apps = {}


@app.route("/run", methods=["POST"])
def run():
    data = request.get_json()
    code = data.get("code", None)
    key = data.get("key", None).strip()

    app_id = data.get("app", None).strip()

    if app_id not in apps:
      apps[app_id] = MarimoIslandGenerator()

    if code is None or key is None:
        return jsonify({"error": "No code provided"}), 400

    stubs[key] = apps[app_id].add_code(code)
    return ""


@app.route("/lookup", methods=["POST"])
def lookup():
    data = request.get_json()
    key = data.get("key", None).strip()
    if key is None or key not in stubs:
        return jsonify({"type": "html", "value": "error: No key provided"}), 400

    response = stubs[key].render()
    del stubs[key]
    return jsonify({"type": "html", "value": response})

    ## TODO: Add back mimetype switching
    # data = lookups[key]
    # # output = try_format(data)
    # # Ideally handle this client side, but just a sanity check
    # if output.mimetype == "image/png":
    #     return jsonify({"type": "figure", "value": f"{output.data}"})

    # # Default to whatever the output was, assuming html
    # return jsonify({"type": "html", "value": f"{mo.as_html(data)}"})


@app.route("/execute", methods=["POST"])
def execute():
    data = request.get_json()
    app_id = data.get("app", None).strip()
    app = asyncio.run(apps[app_id].build())
    return ""


@app.route("/assets", methods=["POST"])
def assets():
    data = request.get_json()
    app_id = data.get("app", None).strip()
    dev_server = os.environ.get("QUARTO_MARIMO_DEBUG_ENDPOINT")
    header = apps[app_id].render_head(_development_url=dev_server)
    del apps[app_id]
    return header


if __name__ == "__main__":
    app.run(debug=True, port=6000)
