from pydantic import BaseModel

class CompanySchema(BaseModel):
    company_name: str
    ceo_name: str
    address: str
    phone: str
    business_number: str
    bank_account: str
