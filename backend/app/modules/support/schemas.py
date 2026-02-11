from pydantic import BaseModel, Field
from typing import Optional

class SupportRequest(BaseModel):
    subject: str = Field(..., max_length=200, description="Resume breve del problema")
    message: str = Field(..., max_length=5000, description="Detalle completo de la solicitud")
    category: str = Field(..., description="e.g., bug, question, feedback")
    email_confirmation: bool = Field(True, description="Send a copy to the user")
