import os
import json
from typing import Dict, Any, Optional

# Import local utility modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.prompt_template_utils import PromptTemplate

# Define the reading difficulty classification prompt
READING_DIFFICULTY_PROMPT = """
You are an educational assistant specializing in reading comprehension. Your task is to analyze a text passage and determine its reading difficulty level.

Text Passage:
${passage}

Analyze the passage for:
1. Lexile level range (if possible to determine)
2. Grade level appropriateness
3. Vocabulary complexity
4. Sentence structure complexity
5. Conceptual difficulty
6. Background knowledge requirements

Respond with a structured analysis in JSON format:

```json
{
    "lexile_range": "XXL-YYL or 'unable to determine'",
    "grade_level": "elementary (K-5)|middle (6-8)|high (9-12)|college",
    "vocabulary_complexity": "simple|moderate|advanced",
    "sentence_complexity": "simple|moderate|complex",
    "conceptual_difficulty": "concrete|moderate|abstract",
    "background_knowledge_required": "minimal|moderate|extensive",
    "overall_difficulty": "beginner|basic|intermediate|advanced|expert",
    "challenging_vocabulary": ["list", "of", "potentially", "challenging", "words"],
    "notes": "Additional observations about the text"
}
```
"""

# Create the prompt template
reading_difficulty_template = PromptTemplate(READING_DIFFICULTY_PROMPT)

def classify_reading_difficulty(passage: str, model_fn) -> Dict[str, Any]:
    """
    Classify the difficulty level of a reading passage
    
    Args:
        passage: The text passage to analyze
        model_fn: Function that takes a prompt and returns a response
        
    Returns:
        Dict with reading difficulty classification
    """
    # Render the prompt with the passage
    prompt = reading_difficulty_template.render(passage=passage)
    
    # Get response from model
    response = model_fn(prompt)
    
    # Parse JSON from response
    try:
        # Check response format
        if isinstance(response, str):
            # Try to extract JSON from the string
            import re
            json_match = re.search(r"```json(.*?)```", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
                difficulty_data = json.loads(json_str)
            else:
                # Try to parse the entire response as JSON
                difficulty_data = json.loads(response)
        elif isinstance(response, dict):
            # Response is already a dictionary
            difficulty_data = response
        else:
            raise ValueError(f"Unexpected response format: {type(response)}")
        
        # Ensure required fields
        required_fields = ["grade_level", "vocabulary_complexity", "overall_difficulty"]
        for field in required_fields:
            if field not in difficulty_data:
                difficulty_data[field] = "unknown"
        
        return difficulty_data
        
    except Exception as e:
        # Fallback classification if parsing fails
        return {
            "lexile_range": "unable to determine",
            "grade_level": "unknown",
            "vocabulary_complexity": "unknown",
            "sentence_complexity": "unknown",
            "conceptual_difficulty": "unknown",
            "background_knowledge_required": "unknown",
            "overall_difficulty": "unknown",
            "challenging_vocabulary": [],
            "notes": f"Error analyzing passage: {str(e)}"
        } 