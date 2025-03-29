import os
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

# Import local utility modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from utils.prompt_template_utils import PromptTemplate

# Define the escalation prompt template
ESCALATION_PROMPT = """
You are an AI educational assistant deciding whether to escalate a student's question to a human teacher.

Context:
- Subject: ${subject}
- Student Grade Level: ${grade_level}
- Query Type: ${query_type}
- Previous AI Responses: ${previous_responses}
- Student's Initial Question: "${student_question}"
- Student's Follow-up: "${student_followup}"
- Number of back-and-forth exchanges: ${exchange_count}

Reasons to escalate to a human teacher include:
1. Question is too complex for an AI to answer accurately
2. Student shows frustration or confusion after multiple explanation attempts
3. Question requires subjective judgment that only a human teacher can provide
4. Student explicitly requests to speak with a human teacher
5. Topic requires specialized expertise or current information
6. Question may involve sensitive educational topics best handled by a human

Determine if this query should be escalated to a human teacher.
Respond with a JSON object:

```json
{
    "escalate": true/false,
    "reason": "Brief explanation of why escalation is needed or not needed",
    "suggested_action": "connect_to_teacher|provide_alternative_resources|simplify_explanation|other",
    "suggested_time": "immediate|end_of_day|scheduled",
    "priority": "low|medium|high",
    "teacher_note": "Brief note for the teacher about the student's question"
}
```
"""

# Create prompt template
escalation_template = PromptTemplate(ESCALATION_PROMPT)

# Escalation threshold constants
MAX_EXCHANGES_BEFORE_ESCALATION = 5  # Maximum number of back-and-forth exchanges before suggesting escalation
FRUSTRATION_KEYWORDS = [
    "i don't understand", "confused", "not clear", "doesn't make sense", 
    "still don't get it", "i'm lost", "too complicated", "help", "difficult",
    "what do you mean", "explain again", "i'm not following"
]

def check_for_escalation_signals(student_input: str) -> bool:
    """
    Check if the student's input contains signals that indicate 
    they are frustrated or explicitly requesting human assistance
    
    Args:
        student_input: The student's latest input
        
    Returns:
        True if escalation signals are detected, False otherwise
    """
    student_input_lower = student_input.lower()
    
    # Check for explicit requests for human assistance
    human_requests = [
        "can i talk to a human", "can i talk to a teacher", "i want to talk to a teacher",
        "can i speak with a person", "connect me with a teacher", "human teacher",
        "real person", "speak to someone", "talk to someone", "human tutor"
    ]
    
    for request in human_requests:
        if request in student_input_lower:
            return True
    
    # Check for frustration signals
    frustration_count = 0
    for keyword in FRUSTRATION_KEYWORDS:
        if keyword in student_input_lower:
            frustration_count += 1
    
    # If multiple frustration signals are detected, consider escalation
    if frustration_count >= 2:
        return True
    
    return False

def should_escalate(
    student_question: str, 
    student_followup: str, 
    subject: str,
    grade_level: str,
    query_type: str,
    previous_responses: List[str],
    exchange_count: int,
    model_fn: Optional[Callable] = None
) -> Dict[str, Any]:
    """
    Determine whether to escalate a student's question to a human teacher
    
    Args:
        student_question: The student's initial question
        student_followup: The student's latest response/question
        subject: The subject category (e.g., "science", "reading")
        grade_level: The student's grade level
        query_type: The type of query (e.g., "explanation", "problem_solving")
        previous_responses: List of previous AI assistant responses
        exchange_count: Number of back-and-forth exchanges
        model_fn: Function that takes a prompt and returns a response
        
    Returns:
        Dict with escalation decision and details
    """
    # Quick check for escalation signals
    if check_for_escalation_signals(student_followup):
        return {
            "escalate": True,
            "reason": "Student appears frustrated or explicitly requested human assistance",
            "suggested_action": "connect_to_teacher",
            "suggested_time": "immediate",
            "priority": "high",
            "teacher_note": f"Student asked: '{student_question}' and seems unsatisfied with AI responses"
        }
    
    # Escalate after too many exchanges
    if exchange_count >= MAX_EXCHANGES_BEFORE_ESCALATION:
        return {
            "escalate": True,
            "reason": f"Reached maximum of {MAX_EXCHANGES_BEFORE_ESCALATION} exchanges without resolution",
            "suggested_action": "connect_to_teacher",
            "suggested_time": "end_of_day",
            "priority": "medium",
            "teacher_note": f"Multiple attempts to answer: '{student_question}'. Consider reviewing conversation."
        }
    
    # If we have a model function, use it for more advanced escalation decision
    if model_fn is not None:
        # Format previous responses for the prompt
        previous_responses_str = "\n".join([
            f"Response {i+1}: {resp}" for i, resp in enumerate(previous_responses)
        ])
        
        # Render the prompt
        prompt = escalation_template.render(
            subject=subject,
            grade_level=grade_level,
            query_type=query_type,
            previous_responses=previous_responses_str,
            student_question=student_question,
            student_followup=student_followup,
            exchange_count=exchange_count
        )
        
        # Get model response
        response = model_fn(prompt)
        
        # Parse JSON response
        try:
            # Check if we need to extract JSON from text
            if isinstance(response, str):
                import re
                json_match = re.search(r"```json(.*?)```", response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1).strip()
                    decision = json.loads(json_str)
                else:
                    # Try to parse the entire response as JSON
                    decision = json.loads(response)
            elif isinstance(response, dict):
                decision = response
            else:
                raise ValueError(f"Unexpected response format: {type(response)}")
            
            # Ensure required fields
            required_fields = ["escalate", "reason", "suggested_action"]
            for field in required_fields:
                if field not in decision:
                    if field == "escalate":
                        decision[field] = False
                    else:
                        decision[field] = "unknown"
            
            return decision
        except Exception as e:
            # Fallback to rule-based decision if JSON parsing fails
            pass
    
    # Default rule-based decision
    return {
        "escalate": False,
        "reason": "No clear signals for escalation detected",
        "suggested_action": "continue_assistance",
        "suggested_time": "not_applicable",
        "priority": "low",
        "teacher_note": ""
    }

def format_escalation_message(escalation_data: Dict[str, Any]) -> str:
    """
    Format an escalation message to display to the student
    
    Args:
        escalation_data: The escalation decision data
        
    Returns:
        Formatted message to display to the student
    """
    if not escalation_data.get("escalate", False):
        return ""
    
    action = escalation_data.get("suggested_action", "connect_to_teacher")
    
    if action == "connect_to_teacher":
        return """
I think it might be helpful to connect you with one of our teachers who can provide more personalized assistance with this question.

Would you like me to:
1. Connect you with a teacher now (if available)
2. Schedule a time to speak with a teacher later
3. Continue working with me to try a different approach

Please let me know what you prefer.
"""
    elif action == "provide_alternative_resources":
        return """
This is a great question that might benefit from some additional resources.

Would you like me to:
1. Recommend some learning resources on this topic
2. Connect you with a teacher who specializes in this area
3. Try explaining this in a different way

Please let me know how you'd like to proceed.
"""
    else:
        return """
I want to make sure you get the help you need with this question.

Would you like to:
1. Try a different approach to this question
2. Connect with a teacher for more help
3. Take a break and come back to this later

Please let me know what works best for you.
""" 