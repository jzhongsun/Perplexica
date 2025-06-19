def parse_json_response(response: str) -> dict:
    import json
    import re

    # First try direct JSON parsing
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code blocks
        patterns = [
            r"```json\n(.*?)\n```",  # JSON code block
            r"```\n(.*?)\n```",      # Generic code block
            r"{[\s\S]*}",            # Bare JSON object
            r"\[[\s\S]*\]"           # Bare JSON array
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1) if "```" in pattern else match.group(0))
                except json.JSONDecodeError:
                    continue

        # If no valid JSON found, return original response
        return response