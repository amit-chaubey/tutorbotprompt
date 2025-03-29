from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class SubjectEnum(str, Enum):
    READING = "reading"
    SCIENCE = "science"
    MATH = "math"
    GENERAL = "general"


class DifficultyEnum(str, Enum):
    BEGINNER = "beginner"
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class PromptMeta(BaseModel):
    """Metadata for prompt templates"""
    subject: SubjectEnum
    creator: str
    date_created: datetime = Field(default_factory=datetime.now)
    grade_level: str
    difficulty: DifficultyEnum
    tags: List[str] = []
    description: str = ""


class ReadingQuestion(BaseModel):
    """Schema for reading comprehension questions"""
    question: str
    options: List[str]
    correct_answer_index: int
    explanation: str


class ScienceExplanation(BaseModel):
    """Schema for science explanations"""
    concept: str
    explanation: str
    examples: List[str]
    follow_up_questions: List[str] = []
    diagrams: Optional[List[str]] = None


class EscalationRequest(BaseModel):
    """Schema for escalation to human tutor"""
    action: str = "connect_human_tutor"
    reason: str
    suggested_time: Optional[str] = None
    topic: str
    student_responses: List[str] = []
    attempts_made: int


class FeedbackData(BaseModel):
    """Schema for capturing feedback about prompt effectiveness"""
    prompt_id: str
    user_satisfaction: int = Field(ge=1, le=5)
    was_helpful: bool
    time_to_respond: float  # seconds
    follow_up_needed: bool
    comments: Optional[str] = None


def validate_prompt_response(response: Dict[str, Any], schema_type: str) -> Dict[str, Any]:
    """
    Validates a response against the specified schema type
    
    Args:
        response: The response dictionary to validate
        schema_type: Type of schema to validate against ('reading_question', 'science_explanation', etc.)
    
    Returns:
        Validated response object
    """
    schema_map = {
        "reading_question": ReadingQuestion,
        "science_explanation": ScienceExplanation,
        "escalation": EscalationRequest,
        "feedback": FeedbackData
    }
    
    if schema_type not in schema_map:
        raise ValueError(f"Unknown schema type: {schema_type}")
    
    schema_class = schema_map[schema_type]
    validated = schema_class(**response)
    return validated.dict() 