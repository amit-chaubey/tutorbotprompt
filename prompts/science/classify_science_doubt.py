import os
import json
from typing import Dict, Any, List, Optional

# Import local utility modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.prompt_template_utils import PromptTemplate

# Define the science doubt classification prompt
CLASSIFY_SCIENCE_DOUBT_PROMPT = """
You are a science teacher analyzing a student's question or doubt. Your task is to classify the question to better address the student's learning needs.

Student Question: "${student_question}"

Please analyze the question for:
1. Science subject area (physics, chemistry, biology, earth science, etc.)
2. Specific topic within that subject
3. Type of question (factual, conceptual, procedural, application, analytical)
4. Misconceptions or knowledge gaps that might be present
5. Grade level appropriate for the question
6. Complexity level
7. Prior knowledge needed to understand the answer

Respond with a structured analysis in JSON format:

```json
{
    "subject": "physics|chemistry|biology|earth_science|astronomy|environmental_science|other",
    "specific_topic": "The specific scientific topic",
    "question_type": "factual|conceptual|procedural|application|analytical",
    "potential_misconceptions": ["Potential misconception 1", "Potential misconception 2"],
    "grade_level": "elementary|middle|high|college",
    "complexity": "basic|intermediate|advanced",
    "prior_knowledge_needed": ["Concept 1", "Concept 2"],
    "concepts_to_explain": ["Key concept 1", "Key concept 2"],
    "suggested_visual_aids": ["Diagram type 1", "Diagram type 2"],
    "real_world_connection": "How this connects to everyday experience"
}
```
"""

# Create the prompt template
classify_science_doubt_template = PromptTemplate(CLASSIFY_SCIENCE_DOUBT_PROMPT)

def classify_science_doubt(student_question: str, model_fn = None) -> Dict[str, Any]:
    """
    Classify a student's science question or doubt
    
    Args:
        student_question: The student's science question
        model_fn: Function that takes a prompt and returns a response
        
    Returns:
        Dict with science question classification
    """
    # Render the prompt
    prompt = classify_science_doubt_template.render(student_question=student_question)
    
    # If no model function provided, perform basic classification
    if model_fn is None:
        # Simple keyword-based subject detection
        student_question_lower = student_question.lower()
        
        # Simple subject detection
        if any(term in student_question_lower for term in ["force", "motion", "energy", "gravity", "light", "wave", "electricity", "magnet"]):
            subject = "physics"
        elif any(term in student_question_lower for term in ["element", "compound", "reaction", "molecule", "atom", "acid", "base", "solution"]):
            subject = "chemistry"
        elif any(term in student_question_lower for term in ["cell", "organism", "animal", "plant", "dna", "evolution", "ecosystem", "body", "organ"]):
            subject = "biology"
        elif any(term in student_question_lower for term in ["earth", "rock", "mineral", "volcano", "earthquake", "weather", "climate"]):
            subject = "earth_science"
        elif any(term in student_question_lower for term in ["star", "planet", "galaxy", "universe", "solar", "space"]):
            subject = "astronomy"
        else:
            subject = "other"
        
        return {
            "subject": subject,
            "specific_topic": "unknown",
            "question_type": "unknown",
            "potential_misconceptions": [],
            "grade_level": "unknown",
            "complexity": "unknown",
            "prior_knowledge_needed": [],
            "concepts_to_explain": [],
            "suggested_visual_aids": [],
            "real_world_connection": ""
        }
    
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
                classification_data = json.loads(json_str)
            else:
                # Try to parse the entire response as JSON
                classification_data = json.loads(response)
        elif isinstance(response, dict):
            # Response is already a dictionary
            classification_data = response
        else:
            raise ValueError(f"Unexpected response format: {type(response)}")
        
        # Ensure required fields
        required_fields = ["subject", "specific_topic", "question_type", "grade_level", "complexity"]
        for field in required_fields:
            if field not in classification_data:
                classification_data[field] = "unknown"
        
        return classification_data
        
    except Exception as e:
        # Fallback if parsing fails
        return {
            "subject": "unknown",
            "specific_topic": "unknown",
            "question_type": "unknown",
            "potential_misconceptions": [],
            "grade_level": "unknown",
            "complexity": "unknown",
            "prior_knowledge_needed": [],
            "concepts_to_explain": [],
            "suggested_visual_aids": [],
            "real_world_connection": f"Error: {str(e)}"
        } 