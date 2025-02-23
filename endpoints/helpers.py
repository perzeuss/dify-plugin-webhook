import json
from typing import Mapping, Optional
from werkzeug import Request, Response
from middlewares.discord_middleware import DiscordMiddleware

def apply_middleware(r: Request, settings: Mapping) -> Optional[Response]:
    """
    Applies middleware based on the settings provided.

    :param r: The request object
    :param settings: A dictionary containing configuration settings
    :return: A Response object if middleware processing returns a response, otherwise None
    """
    try:
        middleware_type = settings.get("middleware")
        signature_verification_key = settings.get("signature_verification_key")

        if middleware_type == "discord":
            middleware = DiscordMiddleware(signature_verification_key)
            response = middleware.invoke(r)
            if response:
                return response
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        return Response(json.dumps({"error": f"Middleware error: {str(e)}"}), status=500, content_type="application/json")

    return None

def validate_api_key(r: Request, settings: Mapping) -> Optional[Response]:
    """
    Validates the API key based on the location specified in the settings.

    :param r: The request object
    :param settings: A dictionary containing configuration settings
    :return: A Response object if validation fails, otherwise None
    """
    api_key_location = settings.get("api_key_location", "api_key_header")
    expected_api_key = settings.get("api_key")

    if api_key_location != 'none' and not expected_api_key:
        return Response(json.dumps({"error": "Expected API key is not configured."}),
                        status=500, content_type="application/json")

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