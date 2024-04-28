import sys
import os
import requests
import random
import string
import json


def post(app_id, endpoint, mime_sensitive=False, data=None):
    if data is None:
        data = {}
    data |= {"app": app_id, "mime_sensitive": mime_sensitive == "yes"}
    # Define the URL for the /run endpoint
    base = os.environ.get("MARIMO_RUN_ENDPOINT", "http://localhost:6000")
    url = f"{base}/{endpoint}"
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, json=data)
    # Return the response
    return response


def lookup(args, key):
    return post(*args, {"key": key}).text


def run(args, code):
    key = "".join(random.choices(string.ascii_letters, k=5))
    post(*args, {"code": code, "key": key})
    return key


def execute(args, options):
    options = json.loads(options)
    # Blank options are passed in as tables, so fix accordingly.
    if isinstance(options, list):
        options = {}
    return post(*args, {"options": options}).text


callbacks = {
    "run": run,
    "execute": execute,
    "lookup": lookup,
}


# Stream to allow for data
if __name__ == "__main__":
    assert len(sys.argv) == 4, f"Unexpected call format got {sys.argv}"
    app_id = sys.argv[1]
    endpoint = sys.argv[2]
    mime_sensitive = sys.argv[3]
    if endpoint in callbacks:
        payload = sys.stdin.read()
        print(callbacks[endpoint](sys.argv[1:], payload))
    else:
        print(post(*sys.argv[1:]).text)
