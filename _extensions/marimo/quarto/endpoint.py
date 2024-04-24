import sys
import requests
import random
import string

def post(app_id, endpoint, data=None):
    if data is None:
        data = {}
    data |= {"app": app_id}
    # Define the URL for the /run endpoint
    url = f"http://localhost:6000/{endpoint}"
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, json=data)
    # Return the response
    return response


def lookup(app_id, key):
    return post(app_id, "lookup", {"key": key}).text


def run(app_id, code):
    key = ''.join(random.choices(string.ascii_letters, k=5))
    post(app_id, "run", {"code": code, "key": key})
    return key

callbacks = {
    "lookup": lookup,
    "run": run,
}

# Stream to allow for data
if __name__=="__main__":
    assert len(sys.argv) == 3, "Unexpected call format"
    app_id = sys.argv[1]
    endpoint = sys.argv[2]
    if endpoint in callbacks:
      payload = sys.stdin.read()
      print(callbacks[endpoint](app_id, payload))
    else:
      print(post(app_id, endpoint).text)
