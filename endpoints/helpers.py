import json
from typing import Mapping
from werkzeug import Request, Response

def validate_api_key(r: Request, settings: Mapping) -> Response:
    """
    Validates the API key based on the location specified in the settings.

    :param r: The request object
    :param settings: A dictionary containing configuration settings
    :return: A Response object if validation fails, otherwise None
    """
    api_key_location = settings.get("api_key_location", "api_key_header")
    expected_api_key = settings.get("api_key")

    if api_key_location == "api_key_header":
        request_api_key = r.headers.get("x-api-key")
        if request_api_key != expected_api_key:
            return Response(json.dumps({"error": "Invalid API key"}),
                            status=403, content_type="application/json")
    
    elif api_key_location == "token_query_param":
        request_api_key = r.args.get("difyToken")
        if request_api_key != expected_api_key:
            return Response(json.dumps({"error": "Invalid API key"}),
                            status=403, content_type="application/json")

    return None