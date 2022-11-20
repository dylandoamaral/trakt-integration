#!/usr/bin/env python

"""
This a script to spam trakt and provok a rate limite and handle it.
It is related to: https://github.com/dylandoamaral/trakt-integration/issues/54.

It didn't work ^^, I made more than 3000 requests in less then 5 minutes.
According to https://trakt.docs.apiary.io/#introduction/rate-limiting it
should fail but it doesn't.
"""

import requests
import os
import multiprocessing as mp

trakt_url = "https://api.trakt.tv"

client_id = os.environ["TRAKT_CLIENT_ID"]
client_secret = os.environ["TRAKT_CLIENT_SECRET"]

device_code_response = requests.post(
    url = f"{trakt_url}/oauth/device/code",
    json={"client_id": client_id}
)

device_code_json = device_code_response.json()
verification_url = device_code_json["verification_url"]
user_code = device_code_json["user_code"]

print(f"Go to {verification_url} and enter {user_code}")

input("Press Enter to continue when it is done...")

device_code = device_code_json["device_code"]

device_token_response = requests.post(
    url = f"{trakt_url}/oauth/device/token",
    json={
        "code": device_code,
        "client_id": client_id,
        "client_secret": client_secret
    }
)

device_token_json = device_token_response.json()

access_token = device_token_json["access_token"]

path = "users/hidden/calendar?type=show"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {access_token}",
    "trakt-api-version": "2",
    "trakt-api-key": client_id,
}

def spam_api(n):
  response = requests.get(
    f"{trakt_url}/{path}",
    headers=headers,
  )

  print(f"{n}: {response.status_code}")

  if response.status_code == 429:
    print(response.headers["Retry-After"])

pool = mp.Pool(mp.cpu_count())
results = [pool.apply(spam_api, args=(i,)) for i in range(0, 1005)]
pool.close()
