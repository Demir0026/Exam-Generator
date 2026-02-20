from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class Question:
    id: Optional[int]
    text: str
    subject: str
    difficulty: str  # 'Easy', 'Medium', 'Hard'
    q_type: str      # 'Multiple Choice', 'Classic'
    options: Optional[str] = None # JSON string or comma-separated for MC options
    answer: Optional[str] = None

@dataclass
class Exam:
    id: Optional[int]
    created_at: datetime
    title: str
    questions: List[Question]
