import os
import json
import time
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime

# Import local utility modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.prompt_template_utils import PromptTemplate
from utils.json_handler import parse_json_response

# Define a prompt template for self-improvement based on feedback
FEEDBACK_IMPROVEMENT_PROMPT = """
You are an AI educational assistant that is analyzing your previous responses to improve future explanations.

Original Student Question: "${student_question}"

Your Previous Response:
${previous_response}

Student's Feedback/Follow-up: "${student_feedback}"

Based on the student's feedback, analyze what could be improved:
1. Was your explanation clear and at the appropriate level?
2. Did you miss any key concepts the student was asking about?
3. Was your language appropriate for the student's grade level (${grade_level})?
4. How can you better explain this concept next time?

Provide a self-improvement analysis in JSON format:

```json
{
    "clarity_issues": ["List any clarity issues identified"],
    "missing_information": ["Key concepts that were missed"],
    "language_appropriateness": "too_simple|appropriate|too_complex",
    "improvement_strategies": ["Specific strategies to improve future responses"],
    "revised_explanation": "A revised, improved explanation that addresses the issues"
}
```
"""

# Create a prompt template for feedback improvement
feedback_improvement_template = PromptTemplate(FEEDBACK_IMPROVEMENT_PROMPT)

# Feedback understanding check template
UNDERSTANDING_CHECK_PROMPT = """
You are an AI educational assistant helping a student. After providing an explanation about ${topic}, 
check the student's understanding by asking a thoughtful follow-up question.

The explanation you provided was:
${explanation}

Generate a follow-up question that:
1. Tests comprehension of the key concept
2. Is appropriate for ${grade_level} grade level
3. Encourages critical thinking
4. Is brief and clearly worded

Your response should:
1. Express interest in the student's understanding
2. Ask a single, focused follow-up question
3. Be encouraging and supportive

Example: "Does that explanation make sense? To check your understanding, could you tell me what would happen if we increased the temperature in this experiment?"
"""

# Create a prompt template for understanding checks
understanding_check_template = PromptTemplate(UNDERSTANDING_CHECK_PROMPT)

def generate_understanding_check(
    explanation: str,
    topic: str,
    grade_level: str,
    model_fn: Callable
) -> str:
    """
    Generate a follow-up question to check student understanding
    
    Args:
        explanation: The explanation that was provided to the student
        topic: The topic being discussed
        grade_level: The student's grade level
        model_fn: Function that takes a prompt and returns a response
        
    Returns:
        A follow-up question to check understanding
    """
    # Render the prompt with the required variables
    prompt = understanding_check_template.render(
        topic=topic,
        explanation=explanation,
        grade_level=grade_level
    )
    
    # Get response from model
    response = model_fn(prompt)
    
    # No need to parse JSON here since we expect a direct text response
    if isinstance(response, dict) and "text" in response:
        return response["text"]
    elif isinstance(response, str):
        return response
    else:
        return "Does that explanation make sense to you? Do you have any questions about what I've explained?"

def analyze_feedback(
    student_question: str,
    previous_response: str,
    student_feedback: str,
    grade_level: str,
    model_fn: Callable
) -> Dict[str, Any]:
    """
    Analyze student feedback to improve future responses
    
    Args:
        student_question: The original student question
        previous_response: The assistant's previous response
        student_feedback: The student's feedback or follow-up question
        grade_level: The student's grade level
        model_fn: Function that takes a prompt and returns a response
        
    Returns:
        Dict with analysis and improvement suggestions
    """
    # Render the prompt with the required variables
    prompt = feedback_improvement_template.render(
        student_question=student_question,
        previous_response=previous_response,
        student_feedback=student_feedback,
        grade_level=grade_level
    )
    
    # Get response from model
    response = model_fn(prompt)
    
    # Parse JSON response
    feedback_data = parse_json_response(response)
    
    if not feedback_data:
        # Fallback if JSON parsing fails
        return {
            "clarity_issues": ["Unable to parse feedback analysis"],
            "missing_information": [],
            "language_appropriateness": "unknown",
            "improvement_strategies": ["Review response format"],
            "revised_explanation": ""
        }
    
    return feedback_data

def is_positive_feedback(feedback: str) -> bool:
    """
    Determine if student feedback is positive
    
    Args:
        feedback: The student's feedback text
        
    Returns:
        True if the feedback appears positive, False otherwise
    """
    feedback_lower = feedback.lower()
    
    positive_patterns = [
        "thank", "thanks", "got it", "understand", "makes sense", 
        "helpful", "clear", "good explanation", "i see", "that works",
        "great", "excellent", "perfect", "awesome", "cool"
    ]
    
    negative_patterns = [
        "don't understand", "confused", "not clear", "doesn't make sense",
        "still don't get it", "i'm lost", "too complicated", "too complex",
        "what do you mean", "explain again", "i'm not following"
    ]
    
    # Check for positive patterns
    positive_count = sum(1 for pattern in positive_patterns if pattern in feedback_lower)
    
    # Check for negative patterns
    negative_count = sum(1 for pattern in negative_patterns if pattern in feedback_lower)
    
    # If there are more positive patterns than negative, consider it positive feedback
    return positive_count > negative_count

def track_feedback(
    student_id: str,
    prompt_id: str,
    response_id: str,
    feedback: str,
    feedback_type: str = "implicit",
    response_time_ms: Optional[int] = None,
    save_to_file: bool = True
) -> Dict[str, Any]:
    """
    Track feedback data for analytics and improvement
    
    Args:
        student_id: Identifier for the student
        prompt_id: Identifier for the prompt used
        response_id: Identifier for the response
        feedback: The student's feedback text
        feedback_type: Type of feedback ("implicit" or "explicit")
        response_time_ms: Response time in milliseconds
        save_to_file: Whether to save feedback to a file
        
    Returns:
        Dict with feedback data
    """
    # Create feedback data structure
    feedback_data = {
        "student_id": student_id,
        "prompt_id": prompt_id,
        "response_id": response_id,
        "feedback": feedback,
        "feedback_type": feedback_type,
        "is_positive": is_positive_feedback(feedback),
        "timestamp": datetime.utcnow().isoformat(),
        "response_time_ms": response_time_ms
    }
    
    # Save feedback to file if requested
    if save_to_file:
        feedback_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "feedback")
        os.makedirs(feedback_dir, exist_ok=True)
        
        feedback_file = os.path.join(feedback_dir, f"feedback_{datetime.utcnow().strftime('%Y%m%d')}.jsonl")
        
        try:
            with open(feedback_file, 'a') as f:
                f.write(json.dumps(feedback_data) + '\n')
        except Exception as e:
            print(f"Error saving feedback: {str(e)}")
    
    return feedback_data

def process_feedback_and_improve_response(
    student_question: str,
    previous_response: str,
    student_feedback: str,
    grade_level: str,
    subject: str,
    model_fn: Callable,
    student_id: Optional[str] = None,
    prompt_id: Optional[str] = None,
    response_id: Optional[str] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Process student feedback and generate an improved response
    
    Args:
        student_question: The original student question
        previous_response: The assistant's previous response
        student_feedback: The student's feedback or follow-up
        grade_level: The student's grade level
        subject: The subject being discussed
        model_fn: Function that takes a prompt and returns a response
        student_id: Optional identifier for the student
        prompt_id: Optional identifier for the prompt
        response_id: Optional identifier for the response
        
    Returns:
        Tuple of (improved_response, feedback_analysis)
    """
    # Start timing
    start_time = time.time()
    
    # Analyze feedback
    feedback_analysis = analyze_feedback(
        student_question=student_question,
        previous_response=previous_response,
        student_feedback=student_feedback,
        grade_level=grade_level,
        model_fn=model_fn
    )
    
    # Track feedback if IDs are provided
    if student_id and prompt_id and response_id:
        response_time_ms = int((time.time() - start_time) * 1000)
        track_feedback(
            student_id=student_id,
            prompt_id=prompt_id,
            response_id=response_id,
            feedback=student_feedback,
            response_time_ms=response_time_ms
        )
    
    # Get the improved explanation
    improved_response = feedback_analysis.get("revised_explanation", "")
    
    # If no improved explanation was provided, maintain the previous response
    if not improved_response:
        improved_response = previous_response
    
    return improved_response, feedback_analysis 