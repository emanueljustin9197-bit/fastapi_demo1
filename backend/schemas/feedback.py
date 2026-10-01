from typing import Literal, Optional

from pydantic import BaseModel, Field


class FeedbackCreateRequest(BaseModel):
    publicCode: str = Field(min_length=1, max_length=64)
    questionnaireId: int = Field(ge=1)
    responseId: int = Field(ge=1)
    rating: int = Field(ge=1, le=5)
    issueType: Literal[
        "none",
        "usability",
        "content",
        "performance",
        "other",
    ] = "none"
    content: Optional[str] = Field(default=None, max_length=500)