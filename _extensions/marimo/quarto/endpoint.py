import sys
import requests
import random
import string

def post(data, endpoint):
    # Define the URL for the /run endpoint
    url = f"http://localhost:6000/{endpoint}"
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, headers=headers, json=data)
    # Return the response
    return response


def get(endpoint):
    url = f"http://localhost:6000/{endpoint}"
    return requests.get(url).text


def lookup(key):
    return post({"key": key}, "lookup").text


def run(code):
    key = ''.join(random.choices(string.ascii_letters, k=5))
    post({"code": code, "key": key}, "run")
    return key

callbacks = {
    "lookup": lookup,
    "run": run,
}

# Stream to allow for data
if __name__=="__main__":
    assert len(sys.argv) == 2, "Unexpected call format"
    endpoint = sys.argv[1]
    if endpoint in callbacks:
      payload = sys.stdin.read()
      print(callbacks[endpoint](payload))
    else:
      print(get(endpoint))
