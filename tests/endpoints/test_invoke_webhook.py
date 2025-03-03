# pylint: disable=W0212

import json
import unittest
from unittest.mock import Mock, patch
from werkzeug import Request, Response
from dify_plugin.core.runtime import Session
from endpoints.invoke_endpoint import WebhookEndpoint

class TestWebhookEndpoint(unittest.TestCase):
    def setUp(self):
        # Create a mock session
        self.mock_session = Mock(spec=Session)
        self.mock_session.app = Mock()
        self.mock_session.app.workflow = Mock()
        self.mock_session.app.chat = Mock()

        # Create the endpoint with the mock session
        self.endpoint = WebhookEndpoint(session=self.mock_session)

        # Create a mock request
        self.mock_request = Mock(spec=Request)
        self.mock_request.get_json = Mock(return_value={})
        self.mock_request.headers = {}
        self.mock_request.default_middleware_json = None
        
        # Set default path to empty string
        self.mock_request.path = ""

        # Default workflow response
        self.workflow_response = {
            "data": {"outputs": {"result": "Test workflow output"}}
        }
        self.mock_session.app.workflow.invoke.return_value = self.workflow_response

        # Default chatflow response
        self.chatflow_response = {"data": {"result": "Chatflow response"}}
        self.mock_session.app.chat.invoke.return_value = self.chatflow_response

        # Default settings
        self.default_settings = {
            "explicit_inputs": True,
            "raw_data_output": False,
            "api_key_required": False,
            "static_app_id": "static-app-id"  # Use static_app_id instead of app_id
        }
        
    # Reset the mock invocations after each test
    def tearDown(self):
        self.mock_session.app.workflow.invoke.reset_mock()
        self.mock_session.app.chat.invoke.reset_mock()

    # REQUEST PREPROCESSING TESTS
    
    @patch('endpoints.invoke_endpoint.apply_middleware')
    def test_middleware_blocks_request(self, mock_apply_middleware):
        """Tests apply_middleware function when it blocks a request.
        Ensures that requests are properly blocked when middleware returns a response."""
        # Return a response from middleware, indicating request is blocked
        middleware_response = Response(
            json.dumps({"error": "Blocked by middleware"}),
            status=403,
            content_type="application/json"
        )
        mock_apply_middleware.return_value = middleware_response

        self.mock_request.path = "/single-workflow"

        response = self.endpoint._invoke(
            self.mock_request, {}, self.default_settings)

        # Assert middleware response is returned
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.data),
            {"error": "Blocked by middleware"}
        )

    @patch('endpoints.invoke_endpoint.apply_middleware')
    @patch('endpoints.invoke_endpoint.validate_api_key')
    def test_api_key_validation_fails(self, mock_validate_api_key, mock_apply_middleware):
        """Tests API key validation when validation fails.
        Ensures requests with invalid API keys are properly rejected."""
        mock_apply_middleware.return_value = None

        # Return a response from API key validation, indicating validation failed
        validation_response = Response(
            json.dumps({"error": "Invalid API key"}),
            status=401,
            content_type="application/json"
        )
        mock_validate_api_key.return_value = validation_response

        self.mock_request.path = "/single-chatflow"
        self.default_settings["api_key_required"] = True

        response = self.endpoint._invoke(
            self.mock_request, {}, self.default_settings)

        # Assert validation response is returned
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            json.loads(response.data),
            {"error": "Invalid API key"}
        )

    @patch('endpoints.invoke_endpoint.apply_middleware')
    @patch('endpoints.invoke_endpoint.validate_api_key')
    def test_json_parsing_fails(self, mock_validate_api_key, mock_apply_middleware):
        """Tests JSON parsing error handling.
        Ensures proper error response when request JSON is invalid."""
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None
        
        # Mock both request.get_json and request.default_middleware_json 
        self.mock_request.get_json.side_effect = json.JSONDecodeError(
            "Invalid JSON", "doc", 0)
        self.mock_request.default_middleware_json = None

        self.mock_request.path = "/single-workflow"

        response = self.endpoint._invoke(
            self.mock_request, {}, self.default_settings)

        # Assert error response
        self.assertEqual(response.status_code, 500)
        self.assertIn("Invalid JSON", json.loads(response.data)["error"])

    @patch('endpoints.invoke_endpoint.apply_middleware')
    @patch('endpoints.invoke_endpoint.validate_api_key')
    def test_default_middleware_json_used(self, mock_validate_api_key, mock_apply_middleware):
        """Tests usage of default_middleware_json.
        Ensures middleware-provided JSON is used instead of request body."""
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        # Set middleware_json which should be used instead of get_json
        self.mock_request.default_middleware_json = {
            "inputs": {"from_middleware": "middleware value"}
        }
        
        # Ensure request.get_json won't be called
        self.mock_request.get_json.side_effect = Exception("Should not be called")
        
        self.mock_request.path = "/single-workflow"

        response = self.endpoint._invoke(
            self.mock_request, {}, self.default_settings)

        # Assert workflow was invoked with middleware json
        self.mock_session.app.workflow.invoke.assert_called_once_with(
            app_id="static-app-id",
            inputs={"from_middleware": "middleware value"},
            response_mode="blocking"
        )

        # Assert response
        self.assertEqual(response.status_code, 200)

    @patch('endpoints.invoke_endpoint.apply_middleware')
    @patch('endpoints.invoke_endpoint.validate_api_key')
    def test_middleware_json_used_for_all_routes(self, mock_validate_api_key, mock_apply_middleware):
        """Tests middleware JSON usage across all routes.
        Ensures middleware-provided JSON is consistently used for all endpoint routes."""
        routes_to_test = [
            ("/single-workflow", {}, self.default_settings),
            ("/single-chatflow", {}, self.default_settings),
            ("/workflow/test-app-id", {"app_id": "test-app-id"}, dict(self.default_settings, **{"static_app_id": None})),
            ("/chatflow/test-app-id", {"app_id": "test-app-id"}, dict(self.default_settings, **{"static_app_id": None}))
        ]
        
        for path, values, settings in routes_to_test:
            # Reset mocks
            self.mock_session.app.workflow.invoke.reset_mock()
            self.mock_session.app.chat.invoke.reset_mock()
            mock_apply_middleware.reset_mock()
            mock_validate_api_key.reset_mock()
            
            mock_apply_middleware.return_value = None
            mock_validate_api_key.return_value = None
            
            self.mock_request.path = path
            
            # Set middleware JSON
            if path.startswith("/workflow") or path == "/single-workflow":
                middleware_json = {"inputs": {"from_middleware": "middleware value"}}
            else:  # chatflow routes
                middleware_json = {"query": "Middleware query", "inputs": {}}
                
            self.mock_request.default_middleware_json = middleware_json
            
            # Make get_json fail to ensure it's not used
            self.mock_request.get_json.side_effect = Exception("Should not be called")
            
            response = self.endpoint._invoke(self.mock_request, values, settings)
            
            # Assert successful response
            self.assertEqual(response.status_code, 200)
            
            # Assert correct invocation based on route
            if path.startswith("/workflow") or path == "/single-workflow":
                app_id = "test-app-id" if path.startswith("/workflow") else "static-app-id"
                self.mock_session.app.workflow.invoke.assert_called_once()
                call_kwargs = self.mock_session.app.workflow.invoke.call_args[1]
                self.assertEqual(call_kwargs["app_id"], app_id)
                self.assertEqual(call_kwargs["inputs"], {"from_middleware": "middleware value"})
            else:  # chatflow routes
                app_id = "test-app-id" if path.startswith("/chatflow") else "static-app-id" 
                self.mock_session.app.chat.invoke.assert_called_once()
                call_kwargs = self.mock_session.app.chat.invoke.call_args[1]
                self.assertEqual(call_kwargs["app_id"], app_id)
                self.assertEqual(call_kwargs["query"], "Middleware query")

    # SINGLE WORKFLOW TESTS

    @patch('endpoints.invoke_endpoint.apply_middleware')
    @patch('endpoints.invoke_endpoint.validate_api_key')
    def test_successful_invocation_single_workflow(self, mock_validate_api_key, mock_apply_middleware):
        """Tests successful invocation of /single-workflow endpoint.
        Ensures the endpoint correctly processes requests with static app_id."""
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        self.mock_request.get_json.return_value = {"inputs": {"param1": "value1"}}
        self.mock_request.path = "/single-workflow"

        response = self.endpoint._invoke(
            self.mock_request, {}, self.default_settings)

        # Assert workflow was invoked with correct parameters
        self.mock_session.app.workflow.invoke.assert_called_once_with(
            app_id="static-app-id",
            inputs={"param1": "value1"},
            response_mode="blocking"
        )

        # Assert response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), self.workflow_response)

    @patch('endpoints.invoke_endpoint.apply_middleware')
    @patch('endpoints.invoke_endpoint.validate_api_key')
    def test_missing_static_app_id_workflow(self, mock_validate_api_key, mock_apply_middleware):
        """Tests /single-workflow endpoint with missing static app_id.
        Ensures proper error handling when configuration is incomplete."""
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        self.mock_request.get_json.return_value = {"inputs": {}}
        self.mock_request.path = "/single-workflow"
        
        # Remove static_app_id from settings
        settings_without_app_id = dict(self.default_settings)
        settings_without_app_id.pop("static_app_id")

        response = self.endpoint._invoke(
            self.mock_request, {}, settings_without_app_id)

        # Assert error response
        self.assertEqual(response.status_code, 404)

    @patch('endpoints.invoke_endpoint.apply_middleware')
    @patch('endpoints.invoke_endpoint.validate_api_key')
    def test_inputs_not_dictionary_single_workflow(self, mock_validate_api_key, mock_apply_middleware):
        """Tests /single-workflow with invalid inputs format.
        Ensures proper validation of inputs parameter type."""
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        self.mock_request.get_json.return_value = {"inputs": "not a dictionary"}
        self.mock_request.path = "/single-workflow"

        response = self.endpoint._invoke(
            self.mock_request, {}, self.default_settings)

        # Assert error response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.data), {"error": "inputs must be an object"})

    @patch('endpoints.invoke_endpoint.apply_middleware')
    @patch('endpoints.invoke_endpoint.validate_api_key')
    def test_raw_data_output_single_workflow(self, mock_validate_api_key, mock_apply_middleware):
        """Tests /single-workflow with raw_data_output=True.
        Ensures only the outputs object is returned when raw output is enabled."""
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        self.mock_request.get_json.return_value = {"inputs": {"param1": "value1"}}
        self.mock_request.path = "/single-workflow"
        
        settings_with_raw_output = dict(self.default_settings)
        settings_with_raw_output["raw_data_output"] = True

        response = self.endpoint._invoke(
            self.mock_request, {}, settings_with_raw_output)

        # Assert only outputs are returned (raw data output)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), self.workflow_response["data"]["outputs"])

    @patch('endpoints.invoke_endpoint.apply_middleware')
    @patch('endpoints.invoke_endpoint.validate_api_key')
    def test_explicit_inputs_false_single_workflow(self, mock_validate_api_key, mock_apply_middleware):
        """Tests /single-workflow with explicit_inputs=False.
        Ensures the entire request body is used as inputs when explicit_inputs is disabled."""
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        self.mock_request.get_json.return_value = {"param1": "value1", "param2": "value2"}
        self.mock_request.path = "/single-workflow"
        
        settings_no_explicit_inputs = dict(self.default_settings)
        settings_no_explicit_inputs["explicit_inputs"] = False

        response = self.endpoint._invoke(
            self.mock_request, {}, settings_no_explicit_inputs)

        # Assert entire request body was used as inputs
        self.mock_session.app.workflow.invoke.assert_called_once_with(
            app_id="static-app-id",
            inputs={"param1": "value1", "param2": "value2"},
            response_mode="blocking"
        )

    @patch('endpoints.invoke_endpoint.apply_middleware')
    @patch('endpoints.invoke_endpoint.validate_api_key')
    def test_workflow_invocation_exception_single_workflow(self, mock_validate_api_key, mock_apply_middleware):
        """Tests exception handling in /single-workflow endpoint.
        Ensures exceptions from workflow invocation are properly propagated."""
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        self.mock_request.get_json.return_value = {"inputs": {}}
        self.mock_request.path = "/single-workflow"
        
        # Make workflow.invoke raise an exception
        self.mock_session.app.workflow.invoke.side_effect = Exception("Workflow error")

        with self.assertRaises(Exception) as context:
            self.endpoint._invoke(self.mock_request, {}, self.default_settings)

        # Assert the exception message
        self.assertEqual(str(context.exception), "Workflow error")

    # SINGLE CHATFLOW TESTS

    @patch('endpoints.invoke_endpoint.apply_middleware')
    @patch('endpoints.invoke_endpoint.validate_api_key')
    def test_successful_invocation_single_chatflow(self, mock_validate_api_key, mock_apply_middleware):
        """Tests successful invocation of /single-chatflow endpoint.
        Ensures the endpoint correctly processes chat requests with static app_id."""
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        self.mock_request.get_json.return_value = {
            "query": "What is the weather?",
            "inputs": {}
        }
        self.mock_request.path = "/single-chatflow"

        response = self.endpoint._invoke(
            self.mock_request, {}, self.default_settings)

        # Assert chatflow was invoked with correct parameters
        self.mock_session.app.chat.invoke.assert_called_once_with(
            app_id="static-app-id",
            query="What is the weather?",
            conversation_id=None,
            inputs={},
            response_mode="blocking"
        )

        # Assert response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), self.chatflow_response)

    @patch('endpoints.invoke_endpoint.apply_middleware')
    @patch('endpoints.invoke_endpoint.validate_api_key')
    def test_missing_static_app_id_chatflow(self, mock_validate_api_key, mock_apply_middleware):
        """Tests /single-chatflow endpoint with missing static app_id.
        Ensures proper error handling when configuration is incomplete."""
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        self.mock_request.get_json.return_value = {
            "query": "What is the weather?",
            "inputs": {}
        }
        self.mock_request.path = "/single-chatflow"
        
        # Remove static_app_id from settings
        settings_without_app_id = dict(self.default_settings)
        settings_without_app_id.pop("static_app_id")

        response = self.endpoint._invoke(
            self.mock_request, {}, settings_without_app_id)

        # Assert error response
        self.assertEqual(response.status_code, 404)

    @patch('endpoints.invoke_endpoint.apply_middleware')
    @patch('endpoints.invoke_endpoint.validate_api_key')
    def test_missing_query_single_chatflow(self, mock_validate_api_key, mock_apply_middleware):
        """Tests /single-chatflow with missing query parameter.
        Ensures proper validation of required query parameter."""
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        self.mock_request.get_json.return_value = {"inputs": {}}
        self.mock_request.path = "/single-chatflow"

        response = self.endpoint._invoke(
            self.mock_request, {}, self.default_settings)

        # Assert error response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.data), {"error": "query must be a string"})

    @patch('endpoints.invoke_endpoint.apply_middleware')
    @patch('endpoints.invoke_endpoint.validate_api_key')
    def test_non_string_query_single_chatflow(self, mock_validate_api_key, mock_apply_middleware):
        """Tests /single-chatflow with non-string query parameter.
        Ensures proper validation of query parameter type."""
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        self.mock_request.get_json.return_value = {
            "query": 123,  # Not a string
            "inputs": {}
        }
        self.mock_request.path = "/single-chatflow"

        response = self.endpoint._invoke(
            self.mock_request, {}, self.default_settings)

        # Assert error response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.data), {"error": "query must be a string"})

    @patch('endpoints.invoke_endpoint.apply_middleware')
    @patch('endpoints.invoke_endpoint.validate_api_key')
    def test_explicit_inputs_false_single_chatflow(self, mock_validate_api_key, mock_apply_middleware):
        """Tests /single-chatflow with explicit_inputs=False.
        Ensures all additional parameters are used as inputs with explicit_inputs disabled."""
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        self.mock_request.get_json.return_value = {
            "query": "What is the weather?",
            "conversation_id": "123",
            "param1": "value1"
        }
        self.mock_request.path = "/single-chatflow"
        
        settings_no_explicit_inputs = dict(self.default_settings)
        settings_no_explicit_inputs["explicit_inputs"] = False

        response = self.endpoint._invoke(
            self.mock_request, {}, settings_no_explicit_inputs)

        # Assert chatflow was invoked with correct parameters
        self.mock_session.app.chat.invoke.assert_called_once_with(
            app_id="static-app-id",
            query="What is the weather?",
            conversation_id="123",
            inputs={"param1": "value1"},
            response_mode="blocking"
        )

    # DYNAMIC WORKFLOW TESTS

    @patch('endpoints.invoke_endpoint.apply_middleware')
    @patch('endpoints.invoke_endpoint.validate_api_key')
    def test_successful_invocation_workflow(self, mock_validate_api_key, mock_apply_middleware):
        """Tests successful invocation of /workflow/<app_id> endpoint.
        Ensures the endpoint correctly processes requests with dynamic app_id."""
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        self.mock_request.get_json.return_value = {"inputs": {"param1": "value1"}}
        self.mock_request.path = "/workflow/test-app-id"
        
        # Remove static_app_id to allow dynamic app_id routes
        settings_without_static_app_id = dict(self.default_settings)
        settings_without_static_app_id.pop("static_app_id")
        
        response = self.endpoint._invoke(
            self.mock_request, {"app_id": "test-app-id"}, settings_without_static_app_id)

        # Assert workflow was invoked with correct parameters
        self.mock_session.app.workflow.invoke.assert_called_once_with(
            app_id="test-app-id",
            inputs={"param1": "value1"},
            response_mode="blocking"
        )

        # Assert response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), self.workflow_response)

    @patch('endpoints.invoke_endpoint.apply_middleware')
    @patch('endpoints.invoke_endpoint.validate_api_key')
    def test_inputs_not_dictionary_workflow(self, mock_validate_api_key, mock_apply_middleware):
        """Tests /workflow/<app_id> with invalid inputs format.
        Ensures proper validation of inputs parameter type."""
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        self.mock_request.get_json.return_value = {"inputs": "not a dictionary"}
        self.mock_request.path = "/workflow/test-app-id"
        
        # Remove static_app_id to allow dynamic app_id routes
        settings_without_static_app_id = dict(self.default_settings)
        settings_without_static_app_id.pop("static_app_id")
        
        response = self.endpoint._invoke(
            self.mock_request, {"app_id": "test-app-id"}, settings_without_static_app_id)

        # Assert error response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.data), {"error": "inputs must be an object"})

    @patch('endpoints.invoke_endpoint.apply_middleware')
    @patch('endpoints.invoke_endpoint.validate_api_key')
    def test_missing_app_id_workflow(self, mock_validate_api_key, mock_apply_middleware):
        """Tests /workflow/<app_id> with missing app_id parameter.
        Ensures proper error handling when app_id is not provided."""
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        self.mock_request.path = "/workflow/"
        
        # Remove static_app_id to allow dynamic app_id routes
        settings_without_static_app_id = dict(self.default_settings)
        settings_without_static_app_id.pop("static_app_id")
        
        response = self.endpoint._invoke(
            self.mock_request, {"app_id": ""}, settings_without_static_app_id)

        # Assert error response
        self.assertEqual(response.status_code, 404)

    @patch('endpoints.invoke_endpoint.apply_middleware')
    @patch('endpoints.invoke_endpoint.validate_api_key')
    def test_raw_data_output_workflow_dynamic(self, mock_validate_api_key, mock_apply_middleware):
        """Tests /workflow/<app_id> with raw_data_output=True.
        Ensures only the outputs object is returned when raw output is enabled."""
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        self.mock_request.get_json.return_value = {"inputs": {"param1": "value1"}}
        self.mock_request.path = "/workflow/test-app-id"
        
        # Remove static_app_id to allow dynamic app_id routes
        settings_without_static_app_id = dict(self.default_settings)
        settings_without_static_app_id.pop("static_app_id")
        settings_without_static_app_id["raw_data_output"] = True
        
        response = self.endpoint._invoke(
            self.mock_request, {"app_id": "test-app-id"}, settings_without_static_app_id)

        # Assert only outputs are returned (raw data output)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), self.workflow_response["data"]["outputs"])

    @patch('endpoints.invoke_endpoint.apply_middleware')
    @patch('endpoints.invoke_endpoint.validate_api_key')
    def test_explicit_inputs_false_workflow_dynamic(self, mock_validate_api_key, mock_apply_middleware):
        """Tests /workflow/<app_id> with explicit_inputs=False.
        Ensures the entire request body is used as inputs when explicit_inputs is disabled."""
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        self.mock_request.get_json.return_value = {"param1": "value1", "param2": "value2"}
        self.mock_request.path = "/workflow/test-app-id"
        
        # Remove static_app_id to allow dynamic app_id routes
        settings_without_static_app_id = dict(self.default_settings)
        settings_without_static_app_id.pop("static_app_id")
        settings_without_static_app_id["explicit_inputs"] = False
        
        response = self.endpoint._invoke(
            self.mock_request, {"app_id": "test-app-id"}, settings_without_static_app_id)

        # Assert entire request body was used as inputs
        self.mock_session.app.workflow.invoke.assert_called_once_with(
            app_id="test-app-id",
            inputs={"param1": "value1", "param2": "value2"},
            response_mode="blocking"
        )

    @patch('endpoints.invoke_endpoint.apply_middleware')
    @patch('endpoints.invoke_endpoint.validate_api_key')
    def test_workflow_invocation_exception_workflow_dynamic(self, mock_validate_api_key, mock_apply_middleware):
        """Tests exception handling in /workflow/<app_id> endpoint.
        Ensures exceptions from workflow invocation are properly propagated."""
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        self.mock_request.get_json.return_value = {"inputs": {}}
        self.mock_request.path = "/workflow/test-app-id"
        
        # Remove static_app_id to allow dynamic app_id routes
        settings_without_static_app_id = dict(self.default_settings)
        settings_without_static_app_id.pop("static_app_id")
        
        # Make workflow.invoke raise an exception
        self.mock_session.app.workflow.invoke.side_effect = Exception("Workflow error")

        with self.assertRaises(Exception) as context:
            self.endpoint._invoke(self.mock_request, {"app_id": "test-app-id"}, settings_without_static_app_id)

        # Assert the exception message
        self.assertEqual(str(context.exception), "Workflow error")

    # DYNAMIC CHATFLOW TESTS

    @patch('endpoints.invoke_endpoint.apply_middleware')
    @patch('endpoints.invoke_endpoint.validate_api_key')
    def test_successful_invocation_chatflow(self, mock_validate_api_key, mock_apply_middleware):
        """Tests successful invocation of /chatflow/<app_id> endpoint.
        Ensures the endpoint correctly processes chat requests with dynamic app_id."""
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        self.mock_request.get_json.return_value = {
            "query": "What is the weather?",
            "inputs": {}
        }
        self.mock_request.path = "/chatflow/test-app-id"

        # Remove static_app_id to allow dynamic app_id routes
        settings_without_static_app_id = dict(self.default_settings)
        settings_without_static_app_id.pop("static_app_id")
        
        response = self.endpoint._invoke(
            self.mock_request, {"app_id": "test-app-id"}, settings_without_static_app_id)

        # Assert chatflow was invoked with correct parameters
        self.mock_session.app.chat.invoke.assert_called_once_with(
            app_id="test-app-id",
            query="What is the weather?",
            conversation_id=None,
            inputs={},
            response_mode="blocking"
        )

        # Assert response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), self.chatflow_response)

    @patch('endpoints.invoke_endpoint.apply_middleware')
    @patch('endpoints.invoke_endpoint.validate_api_key')
    def test_missing_query_chatflow(self, mock_validate_api_key, mock_apply_middleware):
        """Tests /chatflow/<app_id> with missing query parameter.
        Ensures proper validation of required query parameter."""
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        self.mock_request.get_json.return_value = {"inputs": {}}
        self.mock_request.path = "/chatflow/test-app-id"

        # Remove static_app_id to allow dynamic app_id routes
        settings_without_static_app_id = dict(self.default_settings)
        settings_without_static_app_id.pop("static_app_id")
        
        response = self.endpoint._invoke(
            self.mock_request, {"app_id": "test-app-id"}, settings_without_static_app_id)
        # Assert error response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.data), {"error": "query must be a string"})

    @patch('endpoints.invoke_endpoint.apply_middleware')
    @patch('endpoints.invoke_endpoint.validate_api_key')
    def test_non_string_query_chatflow_dynamic(self, mock_validate_api_key, mock_apply_middleware):
        """Tests /chatflow/<app_id> with non-string query parameter.
        Ensures proper validation of query parameter type."""
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        self.mock_request.get_json.return_value = {
            "query": 123,  # Not a string
            "inputs": {}
        }
        self.mock_request.path = "/chatflow/test-app-id"
        
        # Remove static_app_id to allow dynamic app_id routes
        settings_without_static_app_id = dict(self.default_settings)
        settings_without_static_app_id.pop("static_app_id")

        response = self.endpoint._invoke(
            self.mock_request, {"app_id": "test-app-id"}, settings_without_static_app_id)

        # Assert error response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.data), {"error": "query must be a string"})

    @patch('endpoints.invoke_endpoint.apply_middleware')
    @patch('endpoints.invoke_endpoint.validate_api_key')
    def test_invalid_conversation_id_chatflow(self, mock_validate_api_key, mock_apply_middleware):
        """Tests /chatflow/<app_id> with invalid conversation_id parameter.
        Ensures proper validation of conversation_id parameter type."""
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        self.mock_request.get_json.return_value = {
            "query": "What is the weather?",
            "inputs": {},
            "conversation_id": 123  # Invalid conversation_id
        }
        self.mock_request.path = "/chatflow/test-app-id"

        # Remove static_app_id to allow dynamic app_id routes
        settings_without_static_app_id = dict(self.default_settings)
        settings_without_static_app_id.pop("static_app_id")
        
        response = self.endpoint._invoke(
            self.mock_request, {"app_id": "test-app-id"}, settings_without_static_app_id)

        # Assert error response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.data), {"error": "conversation_id must be a string"})

    @patch('endpoints.invoke_endpoint.apply_middleware')
    @patch('endpoints.invoke_endpoint.validate_api_key')
    def test_explicit_inputs_false_chatflow_dynamic(self, mock_validate_api_key, mock_apply_middleware):
        """Tests /chatflow/<app_id> with explicit_inputs=False.
        Ensures all additional parameters are used as inputs with explicit_inputs disabled."""
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        self.mock_request.get_json.return_value = {
            "query": "What is the weather?",
            "conversation_id": "123",
            "param1": "value1"
        }
        self.mock_request.path = "/chatflow/test-app-id"
        
        # Remove static_app_id to allow dynamic app_id routes
        settings_without_static_app_id = dict(self.default_settings)
        settings_without_static_app_id.pop("static_app_id")
        settings_without_static_app_id["explicit_inputs"] = False
        
        response = self.endpoint._invoke(
            self.mock_request, {"app_id": "test-app-id"}, settings_without_static_app_id)

        # Assert chatflow was invoked with correct parameters
        self.mock_session.app.chat.invoke.assert_called_once_with(
            app_id="test-app-id",
            query="What is the weather?",
            conversation_id="123",
            inputs={"param1": "value1"},
            response_mode="blocking"
        )


if __name__ == '__main__':
    unittest.main()