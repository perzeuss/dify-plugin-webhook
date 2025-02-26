import json
import logging
from werkzeug import Request, Response
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

logger = logging.getLogger(__name__)

class DiscordMiddleware:
    """
    Middleware for handling Discord interaction webhooks.
    
    This middleware verifies the authenticity of Discord requests using Ed25519 signatures,
    and provides appropriate responses for different Discord interaction types.
    """
    
    def __init__(self, signature_verification_key=None):
        """
        Initialize the Discord middleware with a signature verification key.
        
        Args:
            signature_verification_key (str): The hexadecimal public key for verifying
                                              Discord's request signatures.
                                              
        Raises:
            ValueError: If signature_verification_key is None.
        """
        if signature_verification_key is None:
            logger.error("Signature verification key is required")
            raise ValueError("signature_verification_key is required")

        self.verify_key = VerifyKey(bytes.fromhex(signature_verification_key))
        logger.info("DiscordMiddleware initialized with verification key")

    def invoke(self, r: Request) -> Response:
        """
        Process an incoming request from Discord.
        
        This method verifies the request signature, then determines the type of
        Discord interaction and returns the appropriate response.
        
        Args:
            r (Request): The incoming request to process.
            
        Returns:
            Response: A response to send back to Discord, or None if the request
                     doesn't match any expected interaction type.
        """
        logger.debug("Request received with body: %s", r.data)

        if not self.verify_request(r):
            logger.warning("Invalid request signature")
            return Response(json.dumps({"error": "invalid request signature"}), status=401, content_type="application/json")

        logger.info("Request signature verified")

        if r.method == 'POST' and self.is_ping(r):
            logger.info("Ping received, sending ping response")
            return Response(status=204)
        elif r.method == 'POST' and self.is_webhook_event(r):
            logger.info("Webhook event received, sending acknowledgment")
            return Response(json.dumps({"type": 1}), content_type="application/json")

        logger.info("No specific handler for this request")
        return None

    def is_webhook_event(self, request: Request) -> bool:
        """
        Check if the request is a Discord webhook event (type 1).
        
        Args:
            request (Request): The request to check.
            
        Returns:
            bool: True if the request is a webhook event, False otherwise.
        """
        try:
            logger.debug("Checking if request is a webhook event")
            return request.json.get('type') == 1
        except (TypeError, ValueError) as e:
            logger.error("Failed to parse request JSON for webhook event check: %s", e)
            return False

    def is_ping(self, request: Request) -> bool:
        """
        Check if the request is a Discord ping (type 0).
        
        Discord sends this when registering a new webhook to verify it's working.
        
        Args:
            request (Request): The request to check.
            
        Returns:
            bool: True if the request is a ping, False otherwise.
        """
        try:
            logger.debug("Checking if request is a ping")
            return request.json.get('type') == 0
        except (TypeError, ValueError) as e:
            logger.error("Failed to parse request JSON for ping check: %s", e)
            return False

    def verify_request(self, request: Request) -> bool:
        """
        Verify the authenticity of a Discord request using Ed25519 signatures.
        
        Args:
            request (Request): The request to verify.
            
        Returns:
            bool: True if the request signature is valid, False otherwise.
        """
        try:
            logger.debug("Verifying request with headers: %s", request.headers)
            signature = request.headers['X-Signature-Ed25519']
            timestamp = request.headers['X-Signature-Timestamp']
            body = request.data.decode('utf-8')

            logger.debug("Signature: %s, Timestamp: %s, Body: %s", signature, timestamp, body)
            self.verify_key.verify(
                f'{timestamp}{body}'.encode(), bytes.fromhex(signature))
            logger.info("Request signature successfully verified")
            return True
        except (BadSignatureError, KeyError) as e:
            logger.error("Signature verification failed: %s", e)
            return False