from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from uuid import UUID

class TierBase(BaseModel):
    name: str
    price_usd: float
    included_credits: float
    ocr_pages_included: int

class TierCreate(TierBase):
    pass

class TierUpdate(BaseModel):
    name: Optional[str] = None
    price_usd: Optional[float] = None
    included_credits: Optional[float] = None
    ocr_pages_included: Optional[int] = None

class TierResponse(TierBase):
    id: UUID
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

class SystemConfigBase(BaseModel):
    usd_to_credits_rate: float

class SystemConfigUpdate(BaseModel):
    usd_to_credits_rate: float

class SystemConfigResponse(SystemConfigBase):
    pass

class ModelRateBase(BaseModel):
    model_name: str
    credits_per_token: Optional[float] = 0.0
    credits_per_page: Optional[float] = 0.0

class ModelRateCreate(ModelRateBase):
    pass

class ModelRateUpdate(BaseModel):
    credits_per_token: Optional[float] = None
    credits_per_page: Optional[float] = None

class ModelRateResponse(ModelRateBase):
    id: UUID
    is_active: bool
    model_config = ConfigDict(from_attributes=True)
