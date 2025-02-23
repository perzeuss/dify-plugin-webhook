import json
import logging
from werkzeug import Request, Response
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

logger = logging.getLogger(__name__)

class DiscordMiddleware:
    def __init__(self, signature_verification_key=None):
        if signature_verification_key is None:
            logger.error("Signature verification key is required")
            raise ValueError("signature_verification_key is required")

        self.verify_key = VerifyKey(bytes.fromhex(signature_verification_key))
        logger.info("DiscordMiddleware initialized with verification key")

    def invoke(self, r: Request) -> Response:
        logger.debug("Request received with body: %s", r.data)

        if not self.verify_request(r):
            logger.warning("Invalid request signature")
            return Response(json.dumps({"error": "invalid request signature"}), status=401, content_type="application/json")

        logger.info("Request signature verified")

        if r.method == 'POST' and self.is_webhook_event(r):
            logger.info("Ping received, sending ping response")
            return Response(json.dumps({"type": 1}), content_type="application/json")

        elif r.method == 'POST' and self.is_ping(r):
            logger.info("Ping received, sending ping response")
            return Response(status=204)

        logger.info("No ping response required")
        return None

    def is_webhook_event(self, request: Request) -> bool:
        try:
            logger.debug("Checking if request is a webhook event")
            return request.json.get('type') == 1
        except (TypeError, ValueError) as e:
            logger.error("Failed to parse request JSON for request check: %s", e)
            return False

    def is_ping(self, request: Request) -> bool:
        try:
            logger.debug("Checking if request is a ping")
            return request.json.get('type') == 0
        except (TypeError, ValueError) as e:
            logger.error("Failed to parse request JSON for request check: %s", e)
            return False

    def verify_request(self, request: Request) -> bool:
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