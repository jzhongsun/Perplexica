import json
import os
import re


def parse_json_response(response: str) -> dict:
    # First try direct JSON parsing
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code blocks
        patterns = [
            r"```json\n(.*?)\n```",  # JSON code block
            r"```\n(.*?)\n```",  # Generic code block
            r"{[\s\S]*}",  # Bare JSON object
            r"\[[\s\S]*\]",  # Bare JSON array
        ]

        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                try:
                    return json.loads(
                        match.group(1) if "```" in pattern else match.group(0)
                    )
                except json.JSONDecodeError:
                    continue

        # If no valid JSON found, return original response
        return response

async def save_image_file(image_bytes: bytes, folder_path: str, file_name: str):
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, file_name)
    with open(file_path, "wb") as f:
        f.write(image_bytes)
    return file_path
