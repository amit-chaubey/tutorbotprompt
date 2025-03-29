import os
import json
from typing import Dict, Any, Optional, List

# Import local utility modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.prompt_template_utils import PromptTemplate

# Define the intent classification prompt
INTENT_CLASSIFIER_PROMPT = """
You are an educational assistant that helps students with various subjects. Given a student's question, your task is to:
1. Identify the subject the question relates to (Reading, Science, Math, or Other)
2. Determine the specific type of question
3. Assess the complexity level
4. Decide if this needs human teacher intervention

Student Query: "${query}"

Please classify the intent and respond in JSON format:

```json
{
    "subject": "reading|science|math|other",
    "query_type": "explanation|question|problem_solving|factual|comprehension|other",
    "grade_level": "elementary|middle|high|college|unknown",
    "complexity": "basic|intermediate|advanced",
    "needs_human_teacher": false,
    "reason": "Brief explanation of your classification"
}
```
"""

# Create a prompt template for the intent classifier
intent_classifier_template = PromptTemplate(INTENT_CLASSIFIER_PROMPT)

# Define patterns for quickly identifying subjects based on keywords
SUBJECT_PATTERNS = {
    "reading": [
        "read", "book", "story", "paragraph", "passage", "character", "plot", "author",
        "comprehension", "summary", "theme", "literacy", "literature", "fiction", "nonfiction"
    ],
    "science": [
        "science", "biology", "chemistry", "physics", "atom", "molecule", "cell", "orbit",
        "energy", "force", "experiment", "reaction", "ecosystem", "organism", "planet",
        "solar", "element", "compound", "theory", "hypothesis"
    ],
    "math": [
        "math", "equation", "number", "algebra", "geometry", "calculus", "fraction",
        "decimal", "percent", "addition", "subtraction", "multiplication", "division",
        "formula", "function", "graph", "variable", "solve", "calculation"
    ]
}

def quick_subject_classifier(query: str) -> str:
    """
    Quickly classify a query's subject based on keywords
    
    Args:
        query: The student's query text
        
    Returns:
        Subject classification (reading, science, math, or other)
    """
    query_lower = query.lower()
    
    # Check for each subject's keywords
    subject_scores = {subject: 0 for subject in SUBJECT_PATTERNS}
    
    for subject, patterns in SUBJECT_PATTERNS.items():
        for pattern in patterns:
            if pattern in query_lower:
                subject_scores[subject] += 1
    
    # Get the subject with the highest score
    max_score = max(subject_scores.values())
    if max_score > 0:
        for subject, score in subject_scores.items():
            if score == max_score:
                return subject
    
    # Default to other if no keywords match
    return "other"

def classify_educational_intent(query: str, model_fn=None) -> Dict[str, Any]:
    """
    Classify the educational intent of a student query
    
    Args:
        query: The student's query text
        model_fn: Function that takes a prompt and returns a response
        
    Returns:
        Dict with intent classification
    """
    # Fall back to quick classifier if no model function is provided
    if model_fn is None:
        subject = quick_subject_classifier(query)
        return {
            "subject": subject,
            "query_type": "unknown",
            "grade_level": "unknown",
            "complexity": "unknown",
            "needs_human_teacher": False,
            "reason": "Classification based on keyword matching only"
        }
    
    # Render the prompt with the query
    prompt = intent_classifier_template.render(query=query)
    
    # Call the model function to get a response
    response = model_fn(prompt)
    
    # Try to parse JSON from the response
    try:
        # Check if we need to extract JSON from text
        if hasattr(response, "json") and callable(getattr(response, "json")):
            # Some model APIs return a response object with a json method
            intent_data = response.json()
        elif isinstance(response, dict):
            # Response is already a dictionary
            intent_data = response
        elif isinstance(response, str):
            # Response is a string, try to extract JSON
            import re
            json_match = re.search(r"```json(.*?)```", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1).strip()
                intent_data = json.loads(json_str)
            else:
                # Try to parse the entire response as JSON
                intent_data = json.loads(response)
        else:
            # Unexpected response format
            raise ValueError(f"Unexpected response format: {type(response)}")
        
        # Validate required fields
        required_fields = ["subject", "query_type", "complexity"]
        for field in required_fields:
            if field not in intent_data:
                intent_data[field] = "unknown"
        
        return intent_data
    
    except Exception as e:
        # Fallback to quick classification if JSON parsing fails
        subject = quick_subject_classifier(query)
        return {
            "subject": subject,
            "query_type": "unknown",
            "grade_level": "unknown",
            "complexity": "unknown",
            "needs_human_teacher": False,
            "reason": f"Error parsing response: {str(e)}"
        } 