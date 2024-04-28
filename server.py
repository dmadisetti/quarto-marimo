#! /usr/bin/env nix-shell
#! nix-shell -i python3 -p python3Packages.marimo python3Packages.flask python3Packages.matplotlib

from flask import Flask, request, jsonify

import sys
import re
import os
import json

from marimo import experimental_MarimoIslandGenerator as MarimoIslandGenerator

import asyncio

# Maybe do over sockets instead of web?
# Feels very hacky

app = Flask(__name__)

# Just need globals
stubs = {}
apps = {}
options = {}

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

    config, code = extract_and_strip_quarto_config(code)
    stubs[key] = (
        config,
        apps[app_id].add_code(
            code,
            is_raw=True,
        ),
    )
    return ""


@app.route("/lookup", methods=["POST"])
def lookup():
    data = request.get_json()
    key = data.get("key", None).strip()
    mime_sensitive = data.get("mime_sensitive", False)
    app_id = data.get("app", None).strip()
    if key is None or key not in stubs:
        return jsonify({"type": "html", "value": "error: No key provided"}), 400

    config, stub = stubs[key]
    global_options = options.get(app_id, {})
    # Local supersede global supersedes default options
    config = {**default_config, **global_options, **config}
    if not config["include"]:
        return jsonify({"type": "html", "value": ""})

    del stubs[key]
    output = stub.output
    render_options = {
        "display_code": config["echo"],
        "reactive": config["eval"] and not mime_sensitive,
        "code": stub.code,
    }
    if config["output"] and mime_sensitive:
        if output.mimetype.startswith("image"):
            return jsonify({"type": "figure", "value": f"{output.data}"} | render_options)
        if output.mimetype.startswith("text/plain"):
            return jsonify({"type": "para", "value": f"{output.data}"} | render_options)
        if output.mimetype == "application/vnd.marimo+error":
            if config["error"]:
                return jsonify({"type": "blockquote", "value": f"{output.data}"} | render_options)
            # Suppress errors otherwise
            return jsonify({"type": "para", "value": ""} | render_options)

    elif output.mimetype == "application/vnd.marimo+error":
        if config["warning"]:
            print("Error", output.data, file=sys.stderr)
        if not config["error"]:
            return jsonify({"type": "html", "value": ""})

    # HTML as catch all default
    return jsonify(
        {
            "type": "html",
            "value": stub.render(
                display_code=config["echo"],
                display_output=config["output"],
                is_reactive=render_options["reactive"],
            ),
        } | render_options
    )


@app.route("/execute", methods=["POST"])
def execute():
    data = request.get_json()
    app_id = data.get("app", None).strip()
    options[app_id] = data.get("options", {})
    _ = asyncio.run(apps[app_id].build())
    return ""


@app.route("/assets-and-flush", methods=["POST"])
def assets():
    data = request.get_json()
    app_id = data.get("app", None).strip()
    dev_server = os.environ.get("QUARTO_MARIMO_DEBUG_ENDPOINT")
    header = apps[app_id].render_head(
        _development_url=dev_server, version_override="0.4.9-dev1"
    )
    del apps[app_id]
    return header


@app.route("/flush", methods=["POST"])
def flush():
    data = request.get_json()
    app_id = data.get("app", None).strip()
    del apps[app_id]
    return ""


if __name__ == "__main__":
    app.run(debug=True, port=6000)
