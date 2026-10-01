"""Data-export request bodies."""

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel


class ExportRequest(BaseModel):
    questionnaireId: int
    format: Literal["xlsx", "csv", "json"] = "csv"
    range: Literal["all", "week", "custom"] = "all"
    startDate: Optional[date] = None
    endDate: Optional[date] = None
    includeMetadata: bool = True


__all__ = ["ExportRequest"]
