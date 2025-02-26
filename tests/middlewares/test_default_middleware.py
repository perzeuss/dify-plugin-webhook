# pylint: disable=assignment-from-none
import json
import logging
import unittest
from unittest.mock import MagicMock
from werkzeug import Request
from middlewares.default_middleware import DefaultMiddleware

logger = logging.getLogger(__name__)


class TestDefaultMiddleware(unittest.TestCase):
    """
    Unit tests for the DefaultMiddleware class to ensure correct functionality 
    in transforming request bodies and handling requests.
    """

    def setUp(self):
        """
        Set up the necessary components for testing, including creating an instance 
        of DefaultMiddleware.
        """
        self.middleware = DefaultMiddleware()

    def test_transform_request_body_valid_json(self):
        """
        Test transforming a valid JSON request body into a JSON string.
        """
        request = MagicMock(spec=Request)
        request.get_json.return_value = {"key": "value"}

        self.middleware.transform_request_body(request)

        expected_json_string = json.dumps({"key": "value"})
        self.assertEqual(
            request.default_middleware_json['json_string'], expected_json_string)

    def test_transform_request_body_invalid_json(self):
        """
        Test handling of an invalid JSON request body that raises an exception.
        """
        request = MagicMock(spec=Request)
        request.get_json.side_effect = ValueError("Error parsing JSON")
        
        self.middleware.transform_request_body(request)

        # Expect the default_middleware_json to not be set due to an error
        self.assertFalse(hasattr(request, 'default_middleware_json'))

    def test_invoke_with_json_string_input_enabled(self):
        """
        Test the invoke method when json_string_input setting is enabled.
        """
        settings = {"json_string_input": True}
        request = MagicMock(spec=Request)
        request.data = b'{}'
        request.get_json.return_value = {}

        response = self.middleware.invoke(request, settings)

        self.assertIsNone(response)  # Expect no response to be returned
        self.assertIn('json_string', request.default_middleware_json)

    def test_invoke_with_json_string_input_disabled(self):
        """
        Test the invoke method when json_string_input setting is disabled.
        """
        settings = {"json_string_input": False}
        request = MagicMock(spec=Request)
        request.data = b'{}'
        request.get_json.return_value = {}

        response = self.middleware.invoke(request, settings)

        self.assertIsNone(response)  # Expect no response to be returned
        self.assertFalse(hasattr(request, 'default_middleware_json'))


if __name__ == '__main__':
    unittest.main()
