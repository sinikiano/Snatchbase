"""Database models for stealer log data"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Device(Base):
    """Device model - represents a compromised machine"""
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(500), unique=True, nullable=False, index=True)
    device_name = Column(String(500), nullable=False, index=True)
    device_name_hash = Column(String(64), nullable=False, index=True)
    hostname = Column(String(255), index=True)  # Actual hostname from System.txt
    ip_address = Column(String(50), index=True)  # IP Address from System.txt
    country = Column(String(100), index=True)  # Country code from System.txt
    language = Column(String(50))  # Language from System.txt
    os_version = Column(String(255))  # OS Version from System.txt
    username = Column(String(255))  # Username from System.txt
    infection_date = Column(String(100))  # Local Date from System.txt (infection time)
    antivirus = Column(String(255))  # Antivirus from System.txt
    hwid = Column(String(100))  # HWID from System.txt
    upload_batch = Column(String(255), nullable=False, index=True)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    total_files = Column(Integer, default=0)
    total_credentials = Column(Integer, default=0)
    total_domains = Column(Integer, default=0)
    total_urls = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    credentials = relationship("Credential", back_populates="device", cascade="all, delete-orphan")
    files = relationship("File", back_populates="device", cascade="all, delete-orphan")
    password_stats = relationship("PasswordStat", back_populates="device", cascade="all, delete-orphan")
    software = relationship("Software", back_populates="device", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_device_name', 'device_name'),
        Index('idx_device_name_hash', 'device_name_hash'),
        Index('idx_upload_batch', 'upload_batch'),
        Index('idx_upload_date', 'upload_date'),
    )

class File(Base):
    """File model - stores file tree structure from ZIP archives"""
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(255), ForeignKey('devices.device_id', ondelete='CASCADE'), nullable=False, index=True)
    file_path = Column(Text, nullable=False)
    file_name = Column(String(500), nullable=False, index=True)
    parent_path = Column(Text)
    is_directory = Column(Boolean, default=False)
    file_size = Column(Integer, default=0)
    content = Column(Text)  # Text file content stored in DB
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    device = relationship("Device", back_populates="files")
    
    # Indexes
    __table_args__ = (
        Index('idx_file_name', 'file_name'),
        Index('idx_created_at', 'created_at'),
    )

class Credential(Base):
    """Credential model - stores login credentials"""
    __tablename__ = "credentials"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(500), ForeignKey('devices.device_id'), nullable=False, index=True)
    url = Column(Text)
    domain = Column(String(500), index=True)
    tld = Column(String(50), index=True)
    username = Column(String(500), index=True)
    password = Column(Text)
    browser = Column(String(200), index=True)
    stealer_name = Column(String(200), index=True)
    file_path = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    device = relationship("Device", back_populates="credentials")
    
    # Indexes for better search performance
    __table_args__ = (
        Index('idx_credential_device_id', 'device_id'),
        Index('idx_credential_domain', 'domain'),
        Index('idx_credential_tld', 'tld'),
        Index('idx_credential_username', 'username'),
        Index('idx_credential_browser', 'browser'),
        Index('idx_credential_stealer_name', 'stealer_name'),
        Index('idx_credential_created_at', 'created_at'),
    )

class PasswordStat(Base):
    """Password statistics - tracks password frequency per device"""
    __tablename__ = "password_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(255), ForeignKey('devices.device_id', ondelete='CASCADE'), nullable=False, index=True)
    password = Column(Text, nullable=False)
    count = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    device = relationship("Device", back_populates="password_stats")
    
    # Indexes
    __table_args__ = (
        Index('idx_password_device_id', 'device_id'),
        Index('idx_password_count', 'count'),
    )

class Software(Base):
    """Software model - stores installed software detected from logs"""
    __tablename__ = "software"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(255), ForeignKey('devices.device_id', ondelete='CASCADE'), nullable=False, index=True)
    software_name = Column(String(500), nullable=False, index=True)
    version = Column(String(500))
    source_file = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    device = relationship("Device", back_populates="software")
    
    # Indexes
    __table_args__ = (
        Index('idx_software_device_id', 'device_id'),
        Index('idx_software_name', 'software_name'),
        Index('idx_software_version', 'version'),
        Index('idx_software_source_file', 'source_file'),
        Index('idx_software_created_at', 'created_at'),
    )

class Upload(Base):
    """Upload tracking model"""
    __tablename__ = "uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(String(255), unique=True, index=True)
    filename = Column(String(500))
    status = Column(String(50), default="processing")  # processing, completed, failed
    devices_found = Column(Integer, default=0)
    devices_processed = Column(Integer, default=0)
    devices_skipped = Column(Integer, default=0)
    total_credentials = Column(Integer, default=0)
    total_files = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

# Legacy models for backward compatibility (can be removed later)
class System(Base):
    """Legacy system model - kept for backward compatibility"""
    __tablename__ = "systems"
    
    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String(255), index=True)
    computer_name = Column(String(255), index=True)
    hardware_id = Column(String(255), index=True)
    machine_user = Column(String(255), index=True)
    ip_address = Column(String(45), index=True)
    country = Column(String(10), index=True)
    log_date = Column(String(50))
    upload_id = Column(String(255), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
