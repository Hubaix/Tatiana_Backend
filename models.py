from pydantic import BaseModel
from typing import Optional, List

class CompanyInfo(BaseModel):
    context: Optional[str] = None
    company_name: str
    website: str
    wikipedia_link: str
    linkedin_url: str
    uploaded_files : List[str] = []



    