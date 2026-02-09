from pydantic import BaseModel, Field
from typing import Optional

class SupportRequest(BaseModel):
    subject: str = Field(..., max_length=200, description="Resume breve del problema")
    message: str = Field(..., max_length=5000, description="Detalle completo de la solicitud")
    category: str  # e.g., "bug", "question", "feedback"
    email_confirmation: bool = True
