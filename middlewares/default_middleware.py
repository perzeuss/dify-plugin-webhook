import json
import logging
from typing import Mapping
from werkzeug import Request, Response

logger = logging.getLogger(__name__)


class DefaultMiddleware:
    """
    A default middleware class that provides core functionality for request handling,
    including transformation of request bodies into JSON strings. This middleware can
    be extended or supplemented by custom middlewares for third-party services.
    """

    def invoke(self, r: Request, settings: Mapping) -> Response:
        """
        Handle the incoming request with optional transformations based on settings.
        """
        logger.debug("Request received with body: %s", r.data)

        if settings.get("json_string_input", False):
            self.transform_request_body(r)

        return None

    def transform_request_body(self, request: Request) -> bool:
        """
        Transform the request body into a JSON string and attach it to the request
        object for subsequent processing.
        """
        try:
            logger.debug("Transform request body to json string")
            request_json = request.get_json()
            json_string = json.dumps(request_json)
            request.default_middleware_json = {'json_string': json_string}
        except (TypeError, ValueError) as e:
            logger.error(
                "Failed to parse request JSON for request transformation: %s", e)
