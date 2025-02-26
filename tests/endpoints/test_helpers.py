import json
import unittest
from unittest.mock import Mock, patch
from werkzeug import Request, Response
from endpoints.helpers import apply_middleware, validate_api_key

class TestHelpers(unittest.TestCase):
    def setUp(self):
        self.request = Mock(spec=Request)
        self.settings = {
            "middleware": "discord",
            "signature_verification_key": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
            "api_key": "test_api_key",
            "api_key_location": "api_key_header"
        }

    @patch('endpoints.helpers.DiscordMiddleware.invoke')
    def test_apply_middleware_success(self, mock_invoke):
        """
        Tests apply_middleware function when middleware successfully returns a response.
        Ensures the correct response is returned when the middleware processes the request.
        """
        mock_response = Mock(spec=Response)
        mock_response.status_code = 200
        mock_invoke.return_value = mock_response
        
        response = apply_middleware(self.request, self.settings)
        
        self.assertEqual(response, mock_response)
        mock_invoke.assert_called_once_with(self.request)

    @patch('endpoints.helpers.DiscordMiddleware.invoke')
    def test_apply_middleware_error(self, mock_invoke):
        """
        Tests apply_middleware function when an exception occurs within the middleware.
        Ensures the function returns a 500 response with appropriate error message.
        """
        mock_invoke.side_effect = json.JSONDecodeError("Error", "doc", 0)  # Simulates a JSON error

        response = apply_middleware(self.request, self.settings)

        self.assertEqual(response.status_code, 500)
        self.assertIn("Middleware error", response.data.decode())

    @patch('endpoints.helpers.DiscordMiddleware.invoke')
    @patch('endpoints.helpers.DefaultMiddleware.invoke')
    def test_apply_middleware_with_default_middleware(self, mock_default_invoke, mock_discord_invoke):
        """
        Tests apply_middleware function when Discord middleware returns None,
        which should trigger the default middleware.
        """
        # Discord middleware returns None (no response)
        mock_discord_invoke.return_value = None
        
        # Default middleware doesn't return a response
        mock_default_invoke.return_value = None
        
        response = apply_middleware(self.request, self.settings)
        
        self.assertIsNone(response)
        mock_discord_invoke.assert_called_once_with(self.request)
        mock_default_invoke.assert_called_once_with(self.request, self.settings)

    @patch('endpoints.helpers.DiscordMiddleware.invoke')
    @patch('endpoints.helpers.DefaultMiddleware.invoke')
    def test_apply_middleware_default_middleware_error(self, mock_default_invoke, mock_discord_invoke):
        """
        Tests apply_middleware function when an exception occurs within the default middleware.
        Ensures the function returns a 500 response with appropriate error message.
        """
        # Discord middleware returns None (no response)
        mock_discord_invoke.return_value = None
        
        # Default middleware raises an exception
        mock_default_invoke.side_effect = json.JSONDecodeError("Error in default", "doc", 0)
        
        response = apply_middleware(self.request, self.settings)
        
        self.assertEqual(response.status_code, 500)
        self.assertIn("Default Middleware error", response.data.decode())
        mock_discord_invoke.assert_called_once_with(self.request)
        mock_default_invoke.assert_called_once_with(self.request, self.settings)

    @patch('endpoints.helpers.DiscordMiddleware.invoke')
    @patch('endpoints.helpers.DefaultMiddleware')
    def test_apply_middleware_with_different_middleware_type(self, mock_default_middleware_class, mock_discord_invoke):
        """
        Tests apply_middleware function with a non-discord middleware type,
        which should only trigger the default middleware.
        """
        # Change middleware type to something other than discord
        settings = self.settings.copy()
        settings["middleware"] = "something_else"
        
        # Setup the mock for DefaultMiddleware instance
        mock_default_middleware = Mock()
        mock_default_middleware_class.return_value = mock_default_middleware
        mock_default_middleware.invoke.return_value = None
        
        response = apply_middleware(self.request, settings)
        
        self.assertIsNone(response)
        mock_discord_invoke.assert_not_called()
        mock_default_middleware.invoke.assert_called_once_with(self.request, settings)

    def test_validate_api_key_success(self):
        """
        Tests validate_api_key function when the API key is valid.
        Ensures that no response is returned for valid API key requests.
        """
        self.request.headers = {"x-api-key": "test_api_key"}

        response = validate_api_key(self.request, self.settings)

        self.assertIsNone(response)

    def test_validate_api_key_failure_invalid_header(self):
        """
        Tests validate_api_key function when the API key in the header is invalid.
        Ensures it returns a 403 response with the appropriate error message.
        """
        self.request.headers = {"x-api-key": "invalid_api_key"}

        response = validate_api_key(self.request, self.settings)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(json.loads(response.data), {"error": "Invalid API key"})

    def test_validate_api_key_failure_header_missing(self):
        """
        Tests validate_api_key function when the API key header is missing.
        Ensures it returns a 500 response indicating the missing configuration.
        """
        settings_without_key = self.settings.copy()
        settings_without_key["api_key_location"] = "api_key_header"
        settings_without_key["api_key"] = None
        
        response = validate_api_key(self.request, settings_without_key)

        self.assertEqual(response.status_code, 500)
        self.assertIn("Expected API key is not configured.", response.data.decode())

    def test_validate_api_key_failure_invalid_query_param(self):
        """
        Tests validate_api_key function when the API key in the query parameter is invalid.
        Ensures it returns a 403 response with the appropriate error message.
        """
        self.settings["api_key_location"] = "token_query_param"
        self.request.args = {"difyToken": "invalid_api_key"}
        
        response = validate_api_key(self.request, self.settings)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(json.loads(response.data), {"error": "Invalid API key"})

if __name__ == '__main__':
    unittest.main()