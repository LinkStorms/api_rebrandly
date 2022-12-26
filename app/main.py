from flask import Flask, request, jsonify
import requests

from config import TOKEN

app = Flask(__name__)


@app.route("/create", methods=["POST"])
def create_short_url():
    # Get the destination url from the request body
    url = request.json.get("destintation")
    # Get the alias from the request body
    alias = request.json.get("slashtag")

    # Create the short url
    short_url = create_short_url(url, alias)

    # Return the short url
    return jsonify({"short_url": short_url})


def create_short_url(url, alias):
    # Set the base url
    BASE_URL = "https://api.rebrandly.com/v1/links"
    # Set the header
    header = {
        "accept": "application/json",
        "content-type": "application/json",
        "apikey": TOKEN
    }
    # Set the body
    body = {
        "destination": url,
        "slashtag": alias,
    }
    # Make the request
    response = requests.post(BASE_URL, json=body, headers=header)
    # Return the short url
    json = response.json()
    return json["shortUrl"]
