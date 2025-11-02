"""Pydantic schemas for API requests and responses"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class CredentialBase(BaseModel):
    url: Optional[str] = None
    domain: Optional[str] = None
    tld: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    browser: Optional[str] = None
    stealer_name: Optional[str] = None
    file_path: Optional[str] = None

class CredentialResponse(CredentialBase):
    id: int
    device_id: str
    created_at: datetime
    is_duplicate: Optional[bool] = False
    duplicate_count: Optional[int] = 0
    duplicate_ids: Optional[List[int]] = []
    
    class Config:
        from_attributes = True

class SystemBase(BaseModel):
    machine_id: Optional[str] = None
    computer_name: Optional[str] = None
    hardware_id: Optional[str] = None
    machine_user: Optional[str] = None
    ip_address: Optional[str] = None
    country: Optional[str] = None
    log_date: Optional[str] = None

class SystemResponse(SystemBase):
    id: int
    upload_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class StatisticsResponse(BaseModel):
    total_credentials: int
    total_systems: int
    total_uploads: int
    unique_domains: int
    unique_countries: int
    unique_stealers: int

class DomainStatistic(BaseModel):
    domain: str
    count: int

class CountryStatistic(BaseModel):
    country: str
    count: int

class StealerStatistic(BaseModel):
    stealer_name: str
    count: int


class WalletBase(BaseModel):
    wallet_type: str
    address: Optional[str] = None
    password: Optional[str] = None
    path: Optional[str] = None
    source_file: Optional[str] = None


class WalletResponse(WalletBase):
    id: int
    device_id: int
    balance: Optional[float] = None
    balance_usd: Optional[float] = None
    has_balance: bool
    last_checked: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class WalletStats(BaseModel):
    total_wallets: int
    wallets_with_balance: int
    total_value_usd: float
    breakdown_by_type: dict
    top_wallets: List[dict]
