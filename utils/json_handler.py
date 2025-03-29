import json
import re
from typing import Dict, Any, Optional, Union, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_json_from_text(text: str) -> Optional[str]:
    """
    Extract JSON string from text that might contain additional content
    
    Args:
        text: Text that might contain JSON
        
    Returns:
        Extracted JSON string or None if not found
    """
    # Try to find JSON within triple backticks (```json ... ```)
    json_pattern = r'```(?:json)?\s*([\s\S]*?)```'
    match = re.search(json_pattern, text)
    if match:
        return match.group(1).strip()
    
    # Try to find JSON between curly braces
    braces_pattern = r'({[\s\S]*?})'
    match = re.search(braces_pattern, text)
    if match:
        return match.group(1).strip()
    
    return None

def parse_json_response(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse JSON from a text response that might contain additional content
    
    Args:
        text: Response text that might contain JSON
        
    Returns:
        Parsed JSON as dictionary or None if parsing failed
    """
    json_str = extract_json_from_text(text)
    if not json_str:
        logger.warning("No JSON found in response")
        return None
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {str(e)}")
        # Try to clean the JSON string by fixing common issues
        fixed_json = fix_common_json_errors(json_str)
        try:
            return json.loads(fixed_json)
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON even after attempting fixes")
            return None

def fix_common_json_errors(json_str: str) -> str:
    """
    Attempt to fix common JSON syntax errors
    
    Args:
        json_str: JSON string that might contain syntax errors
        
    Returns:
        Fixed JSON string
    """
    # Replace single quotes with double quotes
    fixed = re.sub(r"'([^']*)':", r'"\1":', json_str)
    fixed = re.sub(r":\s*'([^']*)'", r': "\1"', fixed)
    
    # Add missing quotes around property names
    fixed = re.sub(r'([{,]\s*)([a-zA-Z0-9_]+)(\s*:)', r'\1"\2"\3', fixed)
    
    # Remove trailing commas
    fixed = re.sub(r',\s*([}\]])', r'\1', fixed)
    
    return fixed

def format_json_for_prompt(data: Dict[str, Any], indent: int = 2) -> str:
    """
    Format a JSON object for inclusion in a prompt
    
    Args:
        data: Dictionary to format as JSON
        indent: Number of spaces for indentation
        
    Returns:
        Formatted JSON string
    """
    return json.dumps(data, indent=indent)

def create_structured_output(data: Dict[str, Any], schema_name: str) -> str:
    """
    Create a structured output instruction for LLM prompting
    
    Args:
        data: Example data
        schema_name: Name of the schema
        
    Returns:
        Formatted instruction for structured output
    """
    json_str = format_json_for_prompt(data, indent=2)
    return f"""
You must respond with a valid JSON object matching the following schema for {schema_name}:

```json
{json_str}
```

Your response must be properly formatted JSON that can be parsed by a JSON parser.
"""

def merge_json_objects(obj1: Dict[str, Any], obj2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge two JSON objects
    
    Args:
        obj1: First JSON object
        obj2: Second JSON object (takes precedence for duplicate keys)
        
    Returns:
        Merged JSON object
    """
    result = obj1.copy()
    
    for key, value in obj2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_json_objects(result[key], value)
        elif key in result and isinstance(result[key], list) and isinstance(value, list):
            result[key] = result[key] + value
        else:
            result[key] = value
            
    return result 