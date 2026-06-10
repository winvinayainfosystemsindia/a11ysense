import json
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_json(text: str):
    raw_text = text
    try:
        text = text.strip()
        start_idx = text.find('{')
        if start_idx == -1:
            return {"error": "No JSON found"}

        end_idx = text.rfind('}') + 1
        
        if end_idx == 0:
            logger.warning(f"JSON appears truncated. Attempting recovery...")
            json_candidate = text[start_idx:]
            
            # Repair logic
            quotes = re.findall(r'(?<!\\)"', json_candidate)
            if len(quotes) % 2 != 0:
                json_candidate += '"'
            json_candidate += "}"
            
            try:
                return json.loads(json_candidate, strict=False)
            except Exception as e:
                return {"error": f"Recovery failed: {str(e)}"}

        json_str = text[start_idx:end_idx]
        try:
            return json.loads(json_str, strict=False)
        except json.JSONDecodeError:
            cleaned = re.sub(r':\s*`([^`]*)`(\s*[,}])', r': "\1"\2', json_str)
            cleaned = re.sub(r',\s*}', '}', cleaned)
            cleaned = re.sub(r',\s*\]', ']', cleaned)
            try:
                return json.loads(cleaned, strict=False)
            except:
                return {"error": "Deep cleaning failed"}
    except Exception as e:
        return {"error": str(e)}

# Test cases
test_cases = [
    ('{"name": "test", "value": "truncated', 'Truncated string'),
    ('{"name": "test", "value": 123', 'Truncated object after value'),
    ('```json {"name": "markdown"} ```', 'Markdown block'),
    ('Some text before {"name": "middle"} and after', 'Embedded JSON'),
]

for case, desc in test_cases:
    print(f"\n--- Testing: {desc} ---")
    print(f"Input: {case}")
    result = parse_json(case)
    print(f"Result: {result}")
