import json
import logging
from typing import Mapping
from werkzeug import Request, Response
from dify_plugin import Endpoint
from endpoints.helpers import apply_middleware, validate_api_key

logger = logging.getLogger(__name__)


class WorkflowEndpoint(Endpoint):
    """
    The WorkflowEndpoint is used to trigger a Dify workflow via an HTTP request.

    This endpoint interfaces with the Dify workflow API, allowing you to execute 
    workflows by providing necessary parameters. The request body should be JSON 
    formatted with the following fields:

    - `app_id` (required): The ID of the workflow you intend to trigger. This field 
      is mandatory, and the request will return an error if it is missing.

    - `inputs` (optional): An object containing the inputs needed for the workflow. 
      If provided, it must be a dictionary (object) type. If omitted, an empty 
      object will be assumed as default.

    When a request is made, this endpoint validates the presence of `app_id` and 
    ensures `inputs` is either a dictionary or omitted. It then invokes the 
    specified workflow using the `app_id` and `inputs`, and provides a blocking 
    response from the workflow execution.

    On successful invocation, the endpoint will return a JSON response containing 
    the workflow's output with a 200 status code. In case of validation failure or 
    JSON parsing errors, it returns an error message with a 400 status code.
    """

    def _invoke(self, r: Request, values: Mapping, settings: Mapping) -> Response:
        """
        Invokes the endpoint with the given request.
        """
        logger.info("Received request to invoke workflow.")

        middleware_response = apply_middleware(r, settings)
        if middleware_response:
            logger.debug("Middleware response: %s", middleware_response)
            return middleware_response

        logger.debug("No middleware response")

        validation_response = validate_api_key(r, settings)
        if validation_response:
            logger.debug("API key validation failed: %s", validation_response)
            return validation_response

        try:
            request_data = r.default_middleware_json or r.get_json()
            app_id = values["app_id"]
            logger.debug("Parsed request data: %s", request_data)
            logger.debug("Extracted app_id: %s", app_id)

            if not app_id:
                logger.error("app_id is required but not provided.")
                return Response(json.dumps({"error": "app_id is required"}),
                                status=400, content_type="application/json")

            if settings["explicit_inputs"]:
                inputs = request_data.get("inputs", {})
                if not isinstance(inputs, dict):
                    logger.error(
                        "Invalid inputs type: expected object, got %s", type(inputs).__name__)
                    return Response(json.dumps({"error": "inputs must be an object"}),
                                    status=400, content_type="application/json")
            else:
                inputs = request_data
                if not isinstance(inputs, dict):
                    logger.error(
                        "Invalid inputs type: expected object, got %s", type(inputs).__name__)
                    return Response(json.dumps({"error": "inputs must be an object"}),
                                    status=400, content_type="application/json")

            logger.info(
                "Invoking workflow with app_id: %s and inputs: %s", app_id, inputs)
            dify_response = self.session.app.workflow.invoke(
                app_id=app_id, inputs=inputs, response_mode="blocking"
            )

            response = dify_response["data"]["outputs"] if settings["raw_data_only"] else dify_response

            logger.debug("Workflow response: %s", response)
            return Response(json.dumps(response), status=200, content_type="application/json")

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.error("Error during request processing: %s", str(e))
            return Response(json.dumps({"error": str(e)}), status=500, content_type="application/json")
