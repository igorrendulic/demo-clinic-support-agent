from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class User(BaseModel):
    id: Optional[str] = Field(default=None, description="The user's unique identifier")
    name: Optional[str] = Field(default=None, description="The user's full name")
    phone: Optional[str] = Field(default=None, description="The user's phone number")
    date_of_birth: Optional[str] = Field(default=None, description="The user's date of birth")
    ssn_last_4: Optional[str] = Field(default=None, description="The user's last 4 digits of their SSN")