# pylint: disable=W0212

import json
import unittest
from unittest.mock import Mock, patch
from werkzeug import Request, Response
from dify_plugin.core.runtime import Session
from endpoints.chatflow import ChatflowEndpoint

class TestChatflowEndpoint(unittest.TestCase):
    def setUp(self):
        # Create a mock session
        self.mock_session = Mock(spec=Session)
        self.mock_session.app = Mock()
        self.mock_session.app.chat = Mock()
        
        # Create the endpoint with the mock session
        self.endpoint = ChatflowEndpoint(session=self.mock_session)
        
        # Create a mock request
        self.mock_request = Mock(spec=Request)
        self.mock_request.get_json = Mock(return_value={})
        
        # Default chatflow response
        self.chatflow_response = {
            "data": {"result": "Chatflow response"}
        }
        self.mock_session.app.chat.invoke.return_value = self.chatflow_response
        
        # Default settings
        self.default_settings = {
            "explicit_inputs": True,
            "api_key_required": False
        }

    @patch('endpoints.chatflow.apply_middleware')
    @patch('endpoints.chatflow.validate_api_key')
    def test_successful_invocation(self, mock_validate_api_key, mock_apply_middleware):
        """
        Tests that a chatflow is successfully invoked when valid inputs are provided.
        Checks that the chatflow is called with the correct parameters and a successful response is returned.
        """
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None
        
        self.mock_request.get_json.return_value = {
            "app_id": "test-app-id",
            "query": "What is the weather?",
            "inputs": {"param1": "value1"}
        }
        
        response = self.endpoint._invoke(
            self.mock_request, 
            {"app_id": "test-app-id"},
            self.default_settings
        )
        
        # Assert chatflow was invoked with correct parameters
        self.mock_session.app.chat.invoke.assert_called_once_with(
            app_id="test-app-id", 
            query="What is the weather?",
            conversation_id=None,
            inputs={"param1": "value1"},
            response_mode="blocking"
        )
        
        # Assert response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), self.chatflow_response)

    @patch('endpoints.chatflow.apply_middleware')
    @patch('endpoints.chatflow.validate_api_key')
    def test_missing_app_id(self, mock_validate_api_key, mock_apply_middleware):
        """
        Tests that an error is returned when the 'app_id' is missing from the request parameters.
        Verifies that the requirement for 'app_id' is enforced.
        """
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None
        
        self.mock_request.get_json.return_value = {
            "query": "What is the weather?"
        }
        
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
        
        # Assert chatflow was not invoked
        self.mock_session.app.chat.invoke.assert_not_called()

    @patch('endpoints.chatflow.apply_middleware')
    @patch('endpoints.chatflow.validate_api_key')
    def test_missing_query(self, mock_validate_api_key, mock_apply_middleware):
        """
        Tests that an error is returned when the 'query' is missing from the request.
        Ensures that the 'query' parameter is mandatory for successful chatflow invocation.
        """
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None
        
        self.mock_request.get_json.return_value = {
            "app_id": "test-app-id",
            "inputs": {}
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
            {"error": "query must be a string"}
        )
        
        # Assert chatflow was not invoked
        self.mock_session.app.chat.invoke.assert_not_called()

    @patch('endpoints.chatflow.apply_middleware')
    @patch('endpoints.chatflow.validate_api_key')
    def test_inputs_not_dictionary(self, mock_validate_api_key, mock_apply_middleware):
        """
        Tests that an error is returned when 'inputs' is not a dictionary object as expected.
        Ensures that any incorrect input format is rejected.
        """
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None
        
        self.mock_request.get_json.return_value = {
            "app_id": "test-app-id",
            "query": "What is the weather?",
            "inputs": "not a dictionary"  # Invalid inputs
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
        
        # Assert chatflow was not invoked
        self.mock_session.app.chat.invoke.assert_not_called()

    @patch('endpoints.chatflow.apply_middleware')
    @patch('endpoints.chatflow.validate_api_key')
    def test_successful_invocation_no_inputs(self, mock_validate_api_key, mock_apply_middleware):
        """
        Tests that a chatflow is successfully invoked with empty inputs when no inputs are provided in the request.
        Verifies that the chatflow is called with an empty inputs dictionary.
        """
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None
        
        self.mock_request.get_json.return_value = {
            "app_id": "test-app-id",
            "query": "What is the weather?"
        }
        
        response = self.endpoint._invoke(
            self.mock_request, 
            {"app_id": "test-app-id"},
            self.default_settings
        )
        
        # Assert chatflow was invoked with empty inputs
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

    @patch('endpoints.chatflow.apply_middleware')
    @patch('endpoints.chatflow.validate_api_key')
    def test_json_parsing_fails(self, mock_validate_api_key, mock_apply_middleware):
        """
        Tests that an error response is returned when JSON parsing of the request fails.
        This ensures the endpoint can detect and handle malformed request payloads.
        """
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None
        self.mock_request.get_json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
        
        response = self.endpoint._invoke(
            self.mock_request, 
            {"app_id": "test-app-id"},
            self.default_settings
        )
        
        # Assert error response
        self.assertEqual(response.status_code, 500)
        self.assertIn("Invalid JSON", json.loads(response.data)["error"])

    @patch('endpoints.chatflow.apply_middleware')
    @patch('endpoints.chatflow.validate_api_key')
    def test_invalid_conversation_id(self, mock_validate_api_key, mock_apply_middleware):
        """
        Tests that an error is returned when 'conversation_id' is not a string.
        Ensures that the conversation_id parameter is correctly validated before invocation.
        """
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None
        
        self.mock_request.get_json.return_value = {
            "app_id": "test-app-id",
            "query": "What is the weather?",
            "inputs": {},
            "conversation_id": 100  # Invalid conversation_id
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
            {"error": "conversation_id must be a string"}
        )

    @patch('endpoints.chatflow.apply_middleware')
    @patch('endpoints.chatflow.validate_api_key')
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
        
        self.mock_request.get_json.return_value = {
            "app_id": "test-app-id",
            "query": "What is the weather?"
        }
        
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
        
        # Assert chatflow was not invoked
        self.mock_session.app.chat.invoke.assert_not_called()

    @patch('endpoints.chatflow.apply_middleware')
    @patch('endpoints.chatflow.validate_api_key')
    def correct_input_with_explicit_inputs_false(self, mock_validate_api_key, mock_apply_middleware):
        """
        Tests that the entire request body is used as inputs when 'explicit_inputs' is set to False.
        Ensures the chatflow is correctly invoked with the non-wrapped request data.
        """
        mock_apply_middleware.return_value = None
        mock_validate_api_key.return_value = None
        
        # Set explicit_inputs to False in the settings
        settings_with_no_explicit_inputs = {
            # The entire req.body should be passed as inputs dict to the chatflow
            "explicit_inputs": False,
            "api_key_required": False
        }
        
        self.mock_request.get_json.return_value = {
            "query": "What is the weather?",
            "conversation_id": "123",
            "some_param": "foo"
        }
        
        self.endpoint._invoke(
            self.mock_request, 
            {"app_id": "test-app-id"},
            settings_with_no_explicit_inputs
        )
        
        expected_inputs = {
            "some_param": "foo"
        }
        
        # Assert chatflow was invoked with correct parameters including inputs
        self.mock_session.app.chat.invoke.assert_called_with(
            app_id="test-app-id",
            query="What is the weather?",
            conversation_id="123",
            inputs=expected_inputs,
            response_mode="blocking"
        )
        
        
if __name__ == '__main__':
    unittest.main()