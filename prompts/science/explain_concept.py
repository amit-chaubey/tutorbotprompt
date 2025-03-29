import os
import json
from typing import Dict, Any, List, Optional

# Import local utility modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.prompt_template_utils import PromptTemplate

# Define the science concept explanation prompt
EXPLAIN_SCIENCE_CONCEPT_PROMPT = """
You are a science teacher explaining a concept to a student. Your goal is to create a clear, accurate, and engaging explanation tailored to the student's grade level.

Concept to explain: ${concept}
Student grade level: ${grade_level}
Difficulty level: ${difficulty}
Student's prior knowledge: ${prior_knowledge}

Your explanation should:
1. Start with a brief, accessible overview of the concept
2. Use grade-appropriate vocabulary and examples
3. Connect to real-world applications or experiences
4. Include analogies or visualizations when helpful
5. Break down complex ideas into manageable parts
6. Anticipate common misconceptions and address them
7. End with a simple check for understanding

Respond with a structured explanation in JSON format:

```json
{
    "concept_name": "The name of the concept",
    "brief_definition": "A one-sentence definition",
    "detailed_explanation": "The main explanation broken into paragraphs",
    "real_world_examples": ["Example 1", "Example 2"],
    "helpful_analogies": ["Analogy 1", "Analogy 2"],
    "common_misconceptions": ["Misconception 1", "Misconception 2"],
    "key_vocabulary": [
        {"term": "Term 1", "definition": "Definition 1"},
        {"term": "Term 2", "definition": "Definition 2"}
    ],
    "check_understanding": ["Question 1", "Question 2"],
    "further_exploration": ["Resource or activity 1", "Resource or activity 2"]
}
```
"""

# Create the prompt template
explain_science_concept_template = PromptTemplate(EXPLAIN_SCIENCE_CONCEPT_PROMPT)

def explain_science_concept(
    concept: str,
    grade_level: str = "middle",
    difficulty: str = "basic",
    prior_knowledge: str = "basic understanding of the subject",
    model_fn = None
) -> Dict[str, Any]:
    """
    Generate an explanation of a science concept
    
    Args:
        concept: The science concept to explain
        grade_level: The target grade level (elementary, middle, high, college)
        difficulty: The difficulty level of the explanation
        prior_knowledge: Description of student's prior knowledge
        model_fn: Function that takes a prompt and returns a response
        
    Returns:
        Dict with science explanation data
    """
    # Validate grade_level
    valid_grade_levels = ["elementary", "middle", "high", "college"]
    if grade_level not in valid_grade_levels:
        grade_level = "middle"  # Default to middle school if invalid
    
    # Validate difficulty
    valid_difficulties = ["beginner", "basic", "intermediate", "advanced", "expert"]
    if difficulty not in valid_difficulties:
        difficulty = "basic"  # Default to basic if invalid
    
    # Render the prompt
    prompt = explain_science_concept_template.render(
        concept=concept,
        grade_level=grade_level,
        difficulty=difficulty,
        prior_knowledge=prior_knowledge
    )
    
    # If no model function provided, return template
    if model_fn is None:
        return {
            "concept_name": concept,
            "brief_definition": f"[Brief definition of {concept} would be generated here]",
            "detailed_explanation": f"[Detailed explanation of {concept} would be generated here]",
            "real_world_examples": ["[Example 1]", "[Example 2]"],
            "helpful_analogies": ["[Analogy 1]", "[Analogy 2]"],
            "common_misconceptions": ["[Misconception 1]", "[Misconception 2]"],
            "key_vocabulary": [
                {"term": "[Term 1]", "definition": "[Definition 1]"},
                {"term": "[Term 2]", "definition": "[Definition 2]"}
            ],
            "check_understanding": ["[Question 1]", "[Question 2]"],
            "further_exploration": ["[Resource 1]", "[Resource 2]"]
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
                explanation_data = json.loads(json_str)
            else:
                # Try to parse the entire response as JSON
                explanation_data = json.loads(response)
        elif isinstance(response, dict):
            # Response is already a dictionary
            explanation_data = response
        else:
            raise ValueError(f"Unexpected response format: {type(response)}")
        
        # Ensure required fields
        required_fields = ["concept_name", "brief_definition", "detailed_explanation"]
        for field in required_fields:
            if field not in explanation_data:
                explanation_data[field] = f"[Missing {field}]"
        
        return explanation_data
        
    except Exception as e:
        # Fallback if parsing fails
        return {
            "concept_name": concept,
            "brief_definition": "Error generating definition",
            "detailed_explanation": f"Error generating explanation: {str(e)}",
            "real_world_examples": [],
            "helpful_analogies": [],
            "common_misconceptions": [],
            "key_vocabulary": [],
            "check_understanding": [],
            "further_exploration": []
        } 