import os
import json
from typing import Dict, Any, List, Optional

# Import local utility modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.prompt_template_utils import PromptTemplate

# Define the reading comprehension question generator prompt
COMPREHENSION_QUESTION_PROMPT = """
You are an educational assistant specializing in reading comprehension. Based on the following paragraph, generate a multiple-choice question that checks comprehension.

Text Passage:
${paragraph}

Reading Level: ${grade_level}
Question Type: ${question_type}

Generate a multiple-choice question that:
1. Tests understanding of the main idea, key details, vocabulary, inference, or author's purpose
2. Is appropriate for the specified grade level
3. Has one clearly correct answer and three plausible distractors
4. Includes an explanation for why each option is correct or incorrect

Respond with a structured question in JSON format:

```json
{
    "question": "The comprehensive question text",
    "options": [
        "Option A",
        "Option B",
        "Option C",
        "Option D"
    ],
    "correct_option_index": 0,
    "skill_tested": "main_idea|key_detail|vocabulary|inference|authors_purpose",
    "explanations": {
        "A": "Explanation for why option A is correct/incorrect",
        "B": "Explanation for why option B is correct/incorrect",
        "C": "Explanation for why option C is correct/incorrect",
        "D": "Explanation for why option D is correct/incorrect"
    },
    "follow_up_question": "An open-ended follow-up question to extend thinking"
}
```
"""

# Create the prompt template
comprehension_question_template = PromptTemplate(COMPREHENSION_QUESTION_PROMPT)

# Define question types
QUESTION_TYPES = [
    "main_idea",
    "key_detail",
    "vocabulary",
    "inference",
    "authors_purpose",
    "character_analysis",
    "cause_effect",
    "compare_contrast",
    "sequence",
    "text_structure"
]

def generate_comprehension_question(
    paragraph: str, 
    grade_level: str = "middle", 
    question_type: str = "main_idea",
    model_fn = None
) -> Dict[str, Any]:
    """
    Generate a reading comprehension question based on a paragraph
    
    Args:
        paragraph: The text passage to generate a question for
        grade_level: The target grade level (elementary, middle, high, college)
        question_type: The type of question to generate
        model_fn: Function that takes a prompt and returns a response
        
    Returns:
        Dict with comprehension question data
    """
    # Validate question_type
    if question_type not in QUESTION_TYPES:
        question_type = "main_idea"  # Default to main idea if invalid type
    
    # Render the prompt
    prompt = comprehension_question_template.render(
        paragraph=paragraph,
        grade_level=grade_level,
        question_type=question_type
    )
    
    # If no model function provided, return template
    if model_fn is None:
        return {
            "question": f"[Question about {question_type} would be generated here]",
            "options": [
                "[Option A]",
                "[Option B]",
                "[Option C]",
                "[Option D]"
            ],
            "correct_option_index": 0,
            "skill_tested": question_type,
            "explanations": {
                "A": "[Explanation A]",
                "B": "[Explanation B]",
                "C": "[Explanation C]",
                "D": "[Explanation D]"
            },
            "follow_up_question": "[Follow-up question]"
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
                question_data = json.loads(json_str)
            else:
                # Try to parse the entire response as JSON
                question_data = json.loads(response)
        elif isinstance(response, dict):
            # Response is already a dictionary
            question_data = response
        else:
            raise ValueError(f"Unexpected response format: {type(response)}")
        
        # Ensure required fields
        required_fields = ["question", "options", "correct_option_index"]
        for field in required_fields:
            if field not in question_data:
                if field == "options":
                    question_data[field] = ["[Option A]", "[Option B]", "[Option C]", "[Option D]"]
                elif field == "correct_option_index":
                    question_data[field] = 0
                else:
                    question_data[field] = f"[Missing {field}]"
        
        return question_data
        
    except Exception as e:
        # Fallback if parsing fails
        return {
            "question": "Error generating question",
            "options": [
                "Option A",
                "Option B",
                "Option C",
                "Option D"
            ],
            "correct_option_index": 0,
            "skill_tested": question_type,
            "explanations": {
                "A": "Error explanation",
                "B": "Error explanation",
                "C": "Error explanation",
                "D": "Error explanation"
            },
            "follow_up_question": f"Error generating follow-up: {str(e)}"
        } 