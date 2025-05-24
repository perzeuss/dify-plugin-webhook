import json
import logging # Ensure logging is imported
from typing import Literal, Mapping, Optional
from werkzeug import Request, Response
from middlewares.discord_middleware import DiscordMiddleware
from middlewares.folo_middleware import FoloMiddleware # Import FoloMiddleware
from middlewares.default_middleware import DefaultMiddleware

logger = logging.getLogger(__name__) # Ensure logger is initialized

def apply_middleware(r: Request, settings: Mapping) -> Optional[Response]:
    """
    Applies middleware based on the settings provided.

    :param r: The request object
    :param settings: A dictionary containing configuration settings
    :return: A Response object if middleware processing returns a response, otherwise None
    """
    middleware_response: Optional[Response] = None
    middleware_processed_request = False # Flag to see if a specific middleware modified the request

    try:
        middleware_type = settings.get("middleware")
        signature_verification_key = settings.get("signature_verification_key")

        if middleware_type == "discord":
            logger.debug("Applying Discord middleware")
            middleware = DiscordMiddleware(signature_verification_key)
            middleware_response = middleware.invoke(r)
            if hasattr(r, 'default_middleware_json'): # Check if DiscordMiddleware modified the request
                 middleware_processed_request = True
        elif middleware_type == "folo":
            logger.debug("Applying Folo middleware")
            middleware = FoloMiddleware() # Instantiate FoloMiddleware
            middleware_response = middleware.invoke(r) # Call its invoke method
            if hasattr(r, 'default_middleware_json'): # Check if FoloMiddleware modified the request
                 middleware_processed_request = True
        
        if middleware_response: # If any middleware returned a direct response (e.g. on error)
            return middleware_response

    except Exception as e: # Catch errors during specific middleware instantiation or invocation
        logger.error(f"Error during {middleware_type} middleware processing: {str(e)}", exc_info=True)
        return Response(json.dumps({"error": f"Error in {middleware_type} middleware: {str(e)}"}),
                        status=500, content_type="application/json")

    # Apply DefaultMiddleware only if no other middleware has processed the request
    # and no specific middleware returned an error response.
    if not middleware_processed_request and not middleware_response:
        try:
            logger.debug("Applying Default middleware")
            default_middleware = DefaultMiddleware()
            # Assuming DefaultMiddleware.invoke might also set r.default_middleware_json or return a Response
            # It should also return None if it just modifies r.default_middleware_json
            default_middleware_response = default_middleware.invoke(r, settings)
            if default_middleware_response:
                return default_middleware_response
        except Exception as e:
            logger.error(f"Default Middleware Error: {str(e)}", exc_info=True)
            return Response(json.dumps({"error": f"Default Middleware error: {str(e)}"}),
                            status=500, content_type="application/json")

    return None # If all middlewares passed (returned None) and did not error

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

EndpointRoute = Literal["/workflow/<app_id>", "/chatflow/<app_id>", "/single-workflow", "/single-chatflow"]

def determine_route(path: str) -> Optional[EndpointRoute]:
    """
    Determines the endpoint route based on the request path.

    Args:
        path: The request path

    Returns:
        The endpoint route as a string, or None if the path doesn't match
    """
    if path.startswith("/workflow"):
        return "/workflow/<app_id>"
    elif path.startswith("/chatflow"):
        return "/chatflow/<app_id>"
    elif path.startswith("/single-workflow"):
        return "/single-workflow"
    elif path.startswith("/single-chatflow"):
        return "/single-chatflow"
    return None