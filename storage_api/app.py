import uuid

import requests
from flask import Flask, g, request
from jwt_validation.exceptions import ValidationFailure
from jwt_validation.validate import validate
from storage_api.exceptions import ApplicationError

app = Flask(__name__)

app.config.from_pyfile("config.py")


class RequestsSessionTimeout(requests.Session):
    """Custom requests session class to set some defaults on g.requests"""

    def request(self, *args, **kwargs):
        # Set a default timeout for the request.
        # Can be overridden in the same way that you would normally set a timeout
        # i.e. g.requests.get(timeout=5)
        if not kwargs.get("timeout"):
            kwargs["timeout"] = app.config["DEFAULT_TIMEOUT"]

        return super(RequestsSessionTimeout, self).request(*args, **kwargs)


@app.before_request
def before_request():
    g.trace_id = request.headers.get('X-Trace-ID', uuid.uuid4().hex)
    g.requests = RequestsSessionTimeout()
    g.requests.headers.update({'X-Trace-ID': g.trace_id})

    # Allow gets for document retrieval and health
    if request.method == 'GET':
        return

    if 'Authorization' not in request.headers:
        raise ApplicationError("Missing Authorization header", "AUTH1", 401)

    try:
        validate(app.config['AUTHENTICATION_API_URL'] + '/authentication/validate',
                 request.headers['Authorization'], g.requests)
    except ValidationFailure as fail:
        raise ApplicationError(fail.message, "AUTH1", 401)

    bearer_jwt = request.headers['Authorization']
    g.requests.headers.update({'Authorization': bearer_jwt})


@app.after_request
def after_request(response):
    response.headers["X-API-Version"] = "1.0.0"
    return response
