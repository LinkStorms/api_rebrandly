from flask import Flask, request, json
from werkzeug.exceptions import HTTPException
from flasgger import Swagger, swag_from
import requests

from validation import (
    url_validation,
    token_validation,
    alias_validation
)
from settings import (
    HOST,
    PORT
)

template = {
    "info":{
        "title": "Rebrandly API",
        "description": "Rebrandly adapter service to shorten URLs"
    }
}

BASE_URL = "https://api.rebrandly.com/v1/links"

app = Flask(__name__)
swagger = Swagger(app, template=template)


@app.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps({
        "code": e.code,
        # "name": e.name,
        "data": {},
        "errors": [e.description],
    })
    response.content_type = "application/json"
    return response


@app.route("/create", methods=["POST"])
@swag_from("flasgger_docs/create_endpoint.yml")
def create_endpoint():
    # Get the url from the request body
    url = request.json.get("url")
    # Get the alias from the request body
    alias = request.json.get("alias", "")
    # Get the token from the request body
    token = request.json.get("token")

    errors = []
    # Validate the url
    try:
        url_validation(url)
    except ValueError as e:
        errors.append(str(e))
    # Validate the token
    try:
        token_validation(token)
    except ValueError as e:
        errors.append(str(e))
    # Validate the alias
    # try:
    #     alias_validation(alias)
    # except ValueError as e:
    #     errors.append(str(e))
    # Return the errors if any
    if errors:
        return {"data": {}, "errors": errors, "code": 422}, 422

    # Create the short url
    status_code, short_url, errors, code = create_short_url(url, alias, token)
    # Return the short url
    if status_code == 200:
        return {"data": {"short_url": short_url}, "errors": [], "code": status_code}, status_code
    if status_code == 401:
        return {"data": {}, "errors": errors, "code": status_code}, status_code
    return {"data": {}, "errors": [errors[0]["message"]], "code": status_code}, status_code


@app.route("/delete", methods=["DELETE"])
@swag_from("flasgger_docs/delete_endpoint.yml")
def delete_endpoint():
    # Get the url from the request body
    alias = request.json.get("alias")
    # Get the token from the request body
    token = request.json.get("token")

    

    errors = []
    # Validate the token
    try:
        token_validation(token)
    except ValueError as e:
        errors.append(str(e))
    # Validate the alias
    try:
        alias_validation(alias)
    except ValueError as e:
        errors.append(str(e))
    # Return the errors if any
    if errors:
        return {"data": {}, "errors": errors, "code": 422}, 422
        
    alias = alias.split("/")[-1]

    # Delete the short url
    status_code, errors, code = delete_short_url(alias, token)
    # Return the response
    return {"data": {}, "errors": errors, "code": status_code}, status_code


def create_short_url(url, alias, token):
    # Set the header
    header = {
        'apikey': token,
        'content-type': 'application/json'
    }
    # Set the body
    body = {
        "destination": url,
        "slashtag": alias
    }
    # Make the request
    response = requests.post(BASE_URL, json=body, headers=header)
    # Return the short url
    status_code = response.status_code
    # Unauthorized error being sent in text
    if status_code == 401:
        return status_code, None, response.text, status_code
    json = response.json()
    if status_code == 200:
        return status_code, json["shortUrl"], json.get("errors", None), json.get("code")
    return status_code, None, json.get("errors", []), json.get("code")


def delete_short_url(alias, token):
    # Get the url id
    url_id, response_code = get_link_id(alias, token)
    if(response_code == 401):
        return response_code, ["Unauthorized"], response_code
    if(not url_id):
        return 404, ["Given alias does not exist"], 404
    # Set the header
    header = {
        'apikey': token,
        'content-type': 'application/json'
    }
    # Make the request
    response = requests.delete(
        BASE_URL + "/" + url_id,
        headers=header
    )
    status_code = response.status_code
    json = response.json()
    return status_code, json.get("errors", []), json.get("code")

def get_link_id(alias, token):

    # Set the header
    header = {
        'apikey': token,
        'content-type': 'application/json'
    }
    # Make the request
    response = requests.get(
        BASE_URL + "?domain.fullName=rebrand.ly&slashtag=" + alias, headers=header)
    # Return the url id
    status_code = response.status_code
    if status_code == 200:
        json = response.json()
        if json:
            return json[0]["id"], status_code
    return None, status_code

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=True)
