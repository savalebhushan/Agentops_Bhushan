from pydantic import BaseModel
from typing import Optional

class UserIDInput(BaseModel):
    user_id: str

class AccountQueryInput(BaseModel):
    user_id: str
    query: str

class UserQueryInput(BaseModel):
    user_id: str
    query_type: str

# Unified refinance input (supports overrides)
class RefinanceInput(BaseModel):
    user_id: str
    new_interest_rate: Optional[float] = None
    new_income: Optional[float] = None
    new_credit_score: Optional[int] = None
