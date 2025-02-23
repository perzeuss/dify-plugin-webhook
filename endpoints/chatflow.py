import json
from typing import Mapping
from werkzeug import Request, Response
from dify_plugin import Endpoint
from endpoints.helpers import apply_middleware, validate_api_key


class ChatflowEndpoint(Endpoint):
    """
    The ChatflowEndpoint is used to trigger a Dify chatflow via an HTTP request.
    This endpoint interfaces with the Dify chatflow API, allowing you to execute 
    chatflows by providing necessary parameters. The request body should be JSON 
    formatted with the following fields:

    - `app_id` (required): The ID of the chatflow you intend to trigger. This field 
      is mandatory, and the request will return an error if it is missing.

    - `query` (required): A string representing the query to be processed.

    - `inputs` (optional): An object containing the inputs needed for the chatflow. 
      If provided, it must be a dictionary (object) type. If omitted, an empty 
      object will be assumed as default.

    - `conversation_id` (optional): A string representing the conversation ID.

    When a request is made, this endpoint validates the presence of `app_id` and 
    ensures `inputs` is either a dictionary or omitted. It also validates `query` 
    and `conversation_id` as strings if provided. It then invokes the specified 
    chatflow using the `app_id`, `query`, `conversation_id`, and `inputs`, and provides 
    a blocking response from the chatflow execution.

    On successful invocation, the endpoint will return a JSON response containing 
    the chatflow's output with a 200 status code. In case of validation failure or 
    JSON parsing errors, it returns an error message with a 400 status code.
    """
    def _invoke(self, r: Request, values: Mapping, settings: Mapping) -> Response:
        """
        Invokes the endpoint with the given request.
        """
        middleware_response = apply_middleware(r, settings)
        if middleware_response:
            return middleware_response
        validation_response = validate_api_key(r, settings)
        if validation_response:
            return validation_response

        try:
            request_data = r.get_json()
            app_id = values["app_id"]

            if not app_id:
                return Response(json.dumps({"error": "app_id is required"}),
                                status=400, content_type="application/json")

            if settings["explicit_inputs"]:
                inputs = request_data.get("inputs", {})
                if not isinstance(inputs, dict):
                    return Response(json.dumps({"error": "inputs must be an object"}),
                                    status=400, content_type="application/json")
            else:
                inputs = request_data
                if not isinstance(inputs, dict):
                    return Response(json.dumps({"error": "inputs must be an object"}),
                                    status=400, content_type="application/json")

            query = inputs.get("query") if settings["explicit_inputs"] else inputs.pop("query")
            if not query or not isinstance(query, str):
                return Response(json.dumps({"error": "query must be a string"}),
                                status=400, content_type="application/json")

            conversation_id = inputs.get("conversation_id") if settings["explicit_inputs"] else inputs.pop("conversation_id")
            if conversation_id is not None and not isinstance(conversation_id, str):
                return Response(json.dumps({"error": "conversation_id must be a string"}),
                                status=400, content_type="application/json")

            response = self.session.app.chat.invoke(
                app_id=app_id,
                query=query,
                conversation_id=conversation_id,
                inputs=inputs,
                response_mode="blocking"
            )

            return Response(json.dumps(response), status=200, content_type="application/json")

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            return Response(json.dumps({"error": str(e)}), status=500, content_type="application/json")