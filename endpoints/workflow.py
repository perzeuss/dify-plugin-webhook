import json
from typing import Mapping
from werkzeug import Request, Response
from dify_plugin import Endpoint
from endpoints.helpers import validate_api_key

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

    def _invoke(self, r: Request, _values: Mapping, settings: Mapping) -> Response:
        """
        Invokes the endpoint with the given request.
        """
        try:
            auth_response = validate_api_key(r, settings)
            if auth_response:
                return auth_response

            request_data = r.get_json()
            app_id = request_data.get("app_id")

            if not app_id:
                return Response(json.dumps({"error": "app_id is required"}),
                                status=400, content_type="application/json")

            inputs = request_data.get("inputs", {})

            if not isinstance(inputs, dict):
                return Response(json.dumps({"error": "inputs must be an object"}),
                                status=400, content_type="application/json")

            response = self.session.app.workflow.invoke(
                app_id=app_id, inputs=inputs, response_mode="blocking"
            )

            return Response(json.dumps(response), status=200, content_type="application/json")

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            return Response(json.dumps({"error": str(e)}), status=400, content_type="application/json")
