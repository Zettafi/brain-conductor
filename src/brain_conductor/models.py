"""pydantic models"""
from pydantic import BaseModel, EmailStr, ConstrainedStr


class Name(ConstrainedStr):
    """Name type"""

    min_length = 3
    max_length = 100


class Comments(ConstrainedStr):
    """Comments type"""

    min_length = 3
    max_length = 2_000


class ContactUs(BaseModel):
    """Contact us form model"""

    name: str
    name_honeypot: Name
    email_honeypot: EmailStr
    comments: Comments


class Feedback(BaseModel):
    """Feedback form model"""

    question: str
    answer: str
    message: str
    chat_history: list
