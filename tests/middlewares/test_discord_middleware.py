import json
import unittest
from unittest.mock import Mock, patch, PropertyMock
from werkzeug import Request
from nacl.exceptions import BadSignatureError
from middlewares.discord_middleware import DiscordMiddleware

class TestDiscordMiddleware(unittest.TestCase):
    def setUp(self):
        self.valid_signature_key = '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef'
        self.middleware = DiscordMiddleware(signature_verification_key=self.valid_signature_key)
        self.valid_request_body = json.dumps({"type": 1}).encode('utf-8')

    @patch('nacl.signing.VerifyKey.verify')
    def test_valid_request_signature(self, mock_verify):
        """
        Tests that a valid request is successfully verified.
        Ensures the correct response is returned when the signature is valid.
        """
        mock_verify.return_value = None  # Simulate successful verification

        # Create a mock request
        request = Mock(spec=Request)
        request.method = 'POST'
        request.headers = {
            'X-Signature-Ed25519': '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef',
            'X-Signature-Timestamp': 'timestamp'
        }
        request.data = self.valid_request_body
        # Mock the JSON property
        request.json = json.loads(self.valid_request_body)

        response = self.middleware.invoke(request)

        # Assert that the correct response is returned for a webhook event
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 200)  # For type 1 events we return a 200 with {"type": 1}
        self.assertEqual(json.loads(response.data), {"type": 1})
        mock_verify.assert_called_once()

    @patch('nacl.signing.VerifyKey.verify')
    def test_invalid_request_signature(self, mock_verify):
        """
        Tests that an invalid request signature results in a 401 response.
        Ensures the middleware correctly handles failed signature verification.
        """
        mock_verify.side_effect = BadSignatureError  # Simulate signature verification failure

        # Create a mock request
        request = Mock(spec=Request)
        request.method = 'POST'
        request.headers = {
            'X-Signature-Ed25519': '0123456789abcdef',  # Invalid but hex to pass conversion
            'X-Signature-Timestamp': 'timestamp'
        }
        request.data = self.valid_request_body

        response = self.middleware.invoke(request)

        # Assert that a 401 error response is returned
        self.assertEqual(response.status_code, 401)
        self.assertEqual(json.loads(response.data), {"error": "invalid request signature"})
        mock_verify.assert_called_once()

    @patch('nacl.signing.VerifyKey.verify')
    def test_ping_event(self, mock_verify):
        """
        Tests that a ping event is processed and responds correctly.
        Confirms the middleware identifies and handles ping events.
        """
        mock_verify.return_value = None  # Simulate successful verification
        
        # Create a mock ping request
        request = Mock(spec=Request)
        request.method = 'POST'
        request.headers = {
            'X-Signature-Ed25519': '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef',
            'X-Signature-Timestamp': 'timestamp'
        }
        ping_data = json.dumps({"type": 0}).encode('utf-8')  # Type 0 indicates a ping
        request.data = ping_data
        # Mock the JSON property correctly
        request.json = json.loads(ping_data)

        response = self.middleware.invoke(request)

        # Assert that a 204 status response is returned for ping events
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 204)
        mock_verify.assert_called_once()

    @patch('nacl.signing.VerifyKey.verify')
    def test_webhook_event(self, mock_verify):
        """
        Tests that a webhook event is detected and processed correctly.
        Ensures the middleware recognizes valid webhook events.
        """
        mock_verify.return_value = None  # Simulate successful verification
        
        # Create a mock webhook event request
        request = Mock(spec=Request)
        request.method = 'POST'
        request.headers = {
            'X-Signature-Ed25519': '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef',
            'X-Signature-Timestamp': 'timestamp'
        }
        webhook_data = json.dumps({"type": 1}).encode('utf-8')  # Type 1 indicates a webhook event
        request.data = webhook_data
        # Mock the JSON property correctly
        request.json = json.loads(webhook_data)

        response = self.middleware.invoke(request)

        # Assert that the correct response is returned for webhook events
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data), {"type": 1})
        mock_verify.assert_called_once()

    @patch('nacl.signing.VerifyKey.verify')
    def test_invalid_request_body(self, mock_verify):
        """
        Tests that if the request body cannot be parsed, it gracefully returns a 401.
        This ensures that malformed JSON requests are handled properly.
        """
        mock_verify.return_value = None  # Simulate successful verification
        
        # Create a mock invalid request
        request = Mock(spec=Request)
        request.method = 'POST'
        request.headers = {
            'X-Signature-Ed25519': '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef',
            'X-Signature-Timestamp': 'timestamp'
        }
        request.data = b'invalid_json'  # Malformed JSON
        
        # Properly mock the json property to raise an exception when accessed
        type(request).json = PropertyMock(side_effect=TypeError("Invalid JSON"))

        response = self.middleware.invoke(request)

        # Since neither ping nor webhook event is triggered due to JSON parsing error,
        # the middleware should return None
        self.assertIsNone(response)
        mock_verify.assert_called_once()

if __name__ == '__main__':
    unittest.main()