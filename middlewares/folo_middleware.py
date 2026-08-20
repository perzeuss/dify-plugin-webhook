import json
import logging
from werkzeug import Request, Response
from typing import Optional

logger = logging.getLogger(__name__)

class FoloMiddleware:
    def __init__(self):
        """
        Initializes the FoloMiddleware.
        Currently, it does not require specific settings from the main config.
        """
        pass

    def invoke(self, r: Request) -> Optional[Response]:
        """
        Processes the request if it's a Folo webhook.
        - Parses the Folo payload.
        - Transforms it into the Dify-expected format with query="start"
          and specific fields mapped to inputs.
        - Stores the transformed payload in r.default_middleware_json.
        
        Returns:
            - A Response object if an error occurs during processing (e.g., invalid payload).
            - None if the transformation is successful, allowing the main handler to proceed
              using r.default_middleware_json.
        """
        logger.debug("FoloMiddleware: Processing request...")
        try:
            folo_payload = r.get_json()
            if not folo_payload or "entry" not in folo_payload:
                logger.error("FoloMiddleware: Invalid or missing 'entry' in Folo payload.")
                return Response(
                    json.dumps({"error": "Folo middleware: Invalid payload, 'entry' field is missing."}),
                    status=400,
                    content_type="application/json"
                )

            entry = folo_payload.get("entry", {})
            
            # Extract required fields from the Folo 'entry' object
            title = entry.get("title")
            content = entry.get("content")
            author = entry.get("author")
            url = entry.get("url")
            published_at = entry.get("publishedAt")
            description = entry.get("description")

            # Construct the new payload for Dify
            dify_inputs = {
                "title": title,
                "content": content,
                "author": author,
                "url": url,
                "publishedAt": published_at,
                "description": description
            }
            
            # Add debug logging for extracted inputs
            logger.debug(f"FoloMiddleware: Extracted inputs for Dify: {dify_inputs}")

            dify_payload = {
                "query": "start",
                "inputs": dify_inputs
            }
            
            # Store the transformed payload in the request object for the main endpoint handler
            r.default_middleware_json = dify_payload 
            logger.info("FoloMiddleware: Payload transformed successfully and stored in r.default_middleware_json.")
            
            return None # Indicate successful transformation

        except json.JSONDecodeError as e:
            logger.error(f"FoloMiddleware: JSONDecodeError while parsing Folo payload - {str(e)}")
            return Response(
                json.dumps({"error": f"Folo middleware: Invalid JSON payload - {str(e)}"}),
                status=400,
                content_type="application/json"
            )
        except Exception as e: 
            logger.error(f"FoloMiddleware: Unexpected error during processing - {str(e)}", exc_info=True)
            return Response(
                json.dumps({"error": f"Folo middleware: Unexpected error - {str(e)}"}),
                status=500,
                content_type="application/json"
            )
