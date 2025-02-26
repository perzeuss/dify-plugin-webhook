# pylint: disable=W0212

import json
import unittest
from unittest.mock import Mock, patch
from werkzeug import Request, Response
from dify_plugin.core.runtime import Session
from endpoints.workflow import WorkflowEndpoint


class TestWorkflowEndpoint(unittest.TestCase):
    def setUp(self):
        # Create a mock session
        self.mock_session = Mock(spec=Session)
        self.mock_session.app = Mock()
        self.mock_session.app.workflow = Mock()

        # Create the endpoint with the mock session
        self.endpoint = WorkflowEndpoint(session=self.mock_session)

        # Create a mock request
        self.mock_request = Mock(spec=Request)
        self.mock_request.get_json = Mock(return_value={})
        self.mock_request.headers = {}
        self.mock_request.default_middleware_json = None

        # Default workflow response
        self.workflow_response = {
            "data": {
                "outputs": {"result": "Test workflow output"}
            }
        }
        self.mock_session.app.workflow.invoke.return_value = self.workflow_response

        # Default settings
        self.default_settings = {
            "explicit_inputs": True,
            "raw_data_output": False,
            "api_key_required": False
        }

    @patch('endpoints.workflow.apply_middleware')
    @patch('endpoints.workflow.validate_api_key')
    def test_successful_invocation(self, mock_validate_api_key, mock_apply_middleware):
        """
        Tests that a workflow is successfully invoked when valid inputs are provided.
        Checks that the workflow is called with the correct parameters and a successful response is returned.
        """
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        self.mock_request.get_json.return_value = {
            "inputs": {"param1": "value1", "param2": "value2"}
        }

        response = self.endpoint._invoke(
            self.mock_request,
            {"app_id": "test-app-id"},
            self.default_settings
        )

        # Assert workflow was invoked with correct parameters
        self.mock_session.app.workflow.invoke.assert_called_once_with(
            app_id="test-app-id",
            inputs={"param1": "value1", "param2": "value2"},
            response_mode="blocking"
        )

        # Assert response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), self.workflow_response)

    @patch('endpoints.workflow.apply_middleware')
    @patch('endpoints.workflow.validate_api_key')
    def test_successful_invocation_no_inputs(self, mock_validate_api_key, mock_apply_middleware):
        """
        Tests that a workflow is successfully invoked with empty inputs when no inputs are provided in the request.
        Verifies that the workflow is called with an empty inputs dictionary.
        """
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        self.mock_request.get_json.return_value = {}

        response = self.endpoint._invoke(
            self.mock_request,
            {"app_id": "test-app-id"},
            self.default_settings
        )

        # Assert workflow was invoked with empty inputs
        self.mock_session.app.workflow.invoke.assert_called_once_with(
            app_id="test-app-id",
            inputs={},
            response_mode="blocking"
        )

        # Assert response
        self.assertEqual(response.status_code, 200)

    @patch('endpoints.workflow.apply_middleware')
    @patch('endpoints.workflow.validate_api_key')
    def test_explicit_inputs_false(self, mock_validate_api_key, mock_apply_middleware):
        """
        Tests that the entire request body is used as inputs when 'explicit_inputs' is set to False.
        Ensures the workflow is correctly invoked with the non-wrapped request data.
        """
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        self.mock_request.get_json.return_value = {
            "param1": "value1",
            "param2": "value2"
        }

        settings = dict(self.default_settings)
        settings["explicit_inputs"] = False

        response = self.endpoint._invoke(
            self.mock_request,
            {"app_id": "test-app-id"},
            settings
        )

        # Assert entire request body was used as inputs
        self.mock_session.app.workflow.invoke.assert_called_once_with(
            app_id="test-app-id",
            inputs={"param1": "value1", "param2": "value2"},
            response_mode="blocking"
        )

        # Assert response
        self.assertEqual(response.status_code, 200)

    @patch('endpoints.workflow.apply_middleware')
    @patch('endpoints.workflow.validate_api_key')
    def test_raw_data_output(self, mock_validate_api_key, mock_apply_middleware):
        """
        Tests that only the 'outputs' part of the workflow response is returned when 'raw_data_output' is enabled.
        This ensures concise data output when this option is selected.
        """
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        settings = dict(self.default_settings)
        settings["raw_data_output"] = True

        response = self.endpoint._invoke(
            self.mock_request,
            {"app_id": "test-app-id"},
            settings
        )

        # Assert only the outputs are returned
        self.assertEqual(
            json.loads(response.data),
            self.workflow_response["data"]["outputs"]
        )

    @patch('endpoints.workflow.apply_middleware')
    @patch('endpoints.workflow.validate_api_key')
    def test_missing_app_id(self, mock_validate_api_key, mock_apply_middleware):
        """
        Tests that an error is returned when the 'app_id' is missing from the request parameters.
        This verifies that the requirement for 'app_id' is enforced.
        """
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        response = self.endpoint._invoke(
            self.mock_request,
            {"app_id": ""},  # Empty app_id
            self.default_settings
        )

        # Assert error response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            json.loads(response.data),
            {"error": "app_id is required"}
        )

        # Assert workflow was not invoked
        self.mock_session.app.workflow.invoke.assert_not_called()

    @patch('endpoints.workflow.apply_middleware')
    @patch('endpoints.workflow.validate_api_key')
    def test_inputs_not_dictionary(self, mock_validate_api_key, mock_apply_middleware):
        """
        Tests that an error is returned when 'inputs' is not a dictionary object as expected.
        Ensures that any incorrect input format is rejected.
        """
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        self.mock_request.get_json.return_value = {
            "inputs": "not a dictionary"
        }

        response = self.endpoint._invoke(
            self.mock_request,
            {"app_id": "test-app-id"},
            self.default_settings
        )

        # Assert error response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            json.loads(response.data),
            {"error": "inputs must be an object"}
        )

        # Assert workflow was not invoked
        self.mock_session.app.workflow.invoke.assert_not_called()

    @patch('endpoints.workflow.apply_middleware')
    def test_middleware_blocks_request(self, mock_apply_middleware):
        """
        Tests that a request is blocked when middleware provides a blocking response.
        Verifies that middleware can preempt workflow invocation.
        """
        # Return a response from middleware, indicating request is blocked
        middleware_response = Response(
            json.dumps({"error": "Blocked by middleware"}),
            status=403,
            content_type="application/json"
        )
        mock_apply_middleware.return_value = middleware_response

        response = self.endpoint._invoke(
            self.mock_request,
            {"app_id": "test-app-id"},
            self.default_settings
        )

        # Assert middleware response is returned
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            json.loads(response.data),
            {"error": "Blocked by middleware"}
        )

        # Assert workflow was not invoked
        self.mock_session.app.workflow.invoke.assert_not_called()

    @patch('endpoints.workflow.apply_middleware')
    @patch('endpoints.workflow.validate_api_key')
    def test_api_key_validation_fails(self, mock_validate_api_key, mock_apply_middleware):
        """
        Tests that a request is blocked due to failing API key validation.
        This ensures that the API key requirement is enforced correctly.
        """
        mock_apply_middleware.return_value = None

        # Return a response from API key validation, indicating validation failed
        validation_response = Response(
            json.dumps({"error": "Invalid API key"}),
            status=401,
            content_type="application/json"
        )
        mock_validate_api_key.return_value = validation_response

        response = self.endpoint._invoke(
            self.mock_request,
            {"app_id": "test-app-id"},
            self.default_settings
        )

        # Assert validation response is returned
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            json.loads(response.data),
            {"error": "Invalid API key"}
        )

        # Assert workflow was not invoked
        self.mock_session.app.workflow.invoke.assert_not_called()

    @patch('endpoints.workflow.apply_middleware')
    @patch('endpoints.workflow.validate_api_key')
    def test_json_parsing_fails(self, mock_validate_api_key, mock_apply_middleware):
        """
        Tests that an error response is returned when the JSON parsing of the request fails.
        This ensures the endpoint can detect and handle malformed request payloads.
        """
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None
        self.mock_request.get_json.side_effect = json.JSONDecodeError(
            "Invalid JSON", "doc", 0)

        response = self.endpoint._invoke(
            self.mock_request,
            {"app_id": "test-app-id"},
            self.default_settings
        )
        self.assertEqual(response.status_code, 500)
        self.assertIn("Invalid JSON", json.loads(response.data)["error"])

    @patch('endpoints.workflow.apply_middleware')
    @patch('endpoints.workflow.validate_api_key')
    def test_workflow_invocation_exception(self, mock_validate_api_key, mock_apply_middleware):
        """
        Tests that an exception is propagated correctly when an error occurs during workflow invocation.
        Ensures that operational failures are surfaced and logged appropriately.
        """
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        # Make workflow.invoke raise an exception
        self.mock_session.app.workflow.invoke.side_effect = Exception(
            "Workflow error")

        with self.assertRaises(Exception) as context:
            self.endpoint._invoke(
                self.mock_request,
                {"app_id": "test-app-id"},
                self.default_settings
            )

        # Assert the exception message
        self.assertEqual(str(context.exception), "Workflow error")

    @patch('endpoints.workflow.apply_middleware')
    @patch('endpoints.workflow.validate_api_key')
    def test_non_dict_input_with_explicit_inputs_false(self, mock_validate_api_key, mock_apply_middleware):
        """
        Tests that an error is returned when the request body, used as inputs due to 'explicit_inputs' being False, is not a dictionary.
        This ensures consistent input validation regardless of configuration.
        """
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        self.mock_request.get_json.return_value = "not a dictionary"

        settings = dict(self.default_settings)
        settings["explicit_inputs"] = False

        response = self.endpoint._invoke(
            self.mock_request,
            {"app_id": "test-app-id"},
            settings
        )

        # Assert error response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            json.loads(response.data),
            {"error": "inputs must be an object"}
        )

        # Assert workflow was not invoked
        self.mock_session.app.workflow.invoke.assert_not_called()

    @patch('endpoints.workflow.apply_middleware')
    @patch('endpoints.workflow.validate_api_key')
    def test_middleware_json_used(self, mock_validate_api_key, mock_apply_middleware):
        """
        Tests that the 'default_middleware_json' is used if present, overriding the usual request JSON parsing.
        This ensures middleware can alter or provide data for further handling directly.
        """
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None

        # Set middleware_json which should be used instead of get_json
        self.mock_request.default_middleware_json = {
            "inputs": {"from_middleware": "middleware value"}
        }

        response = self.endpoint._invoke(
            self.mock_request,
            {"app_id": "test-app-id"},
            self.default_settings
        )

        # Assert workflow was invoked with middleware json
        self.mock_session.app.workflow.invoke.assert_called_once_with(
            app_id="test-app-id",
            inputs={"from_middleware": "middleware value"},
            response_mode="blocking"
        )

        # get_json should not be called
        self.mock_request.get_json.assert_not_called()


if __name__ == '__main__':
    unittest.main()
