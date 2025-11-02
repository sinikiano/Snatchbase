"""Service for searching and filtering stealer log data"""
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, desc
from typing import List, Optional
from app.models import Credential, System, Upload, Device, Software, PasswordStat
from app.schemas import CredentialResponse, SystemResponse, StatisticsResponse, DomainStatistic, CountryStatistic, StealerStatistic

class SearchService:
    """Service for searching stealer log data"""
    
    def search_credentials(
        self,
        db: Session,
        query: Optional[str] = None,
        domain: Optional[str] = None,
        username: Optional[str] = None,
        browser: Optional[str] = None,
        tld: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[CredentialResponse]:
        """Search credentials with filters (enhanced with browser and TLD)"""
        
        # Start with base query
        query_obj = db.query(Credential)
        
        # Apply filters
        filters = []
        
        if query:
            # Full-text search across multiple fields
            search_filter = or_(
                Credential.username.ilike(f"%{query}%"),
                Credential.domain.ilike(f"%{query}%"),
                Credential.url.ilike(f"%{query}%"),
                Credential.browser.ilike(f"%{query}%")
            )
            filters.append(search_filter)
        
        if domain:
            filters.append(Credential.domain.ilike(f"%{domain}%"))
        
        if username:
            filters.append(Credential.username.ilike(f"%{username}%"))
        
        if browser:
            filters.append(Credential.browser.ilike(f"%{browser}%"))
        
        if tld:
            filters.append(Credential.tld.ilike(f"%{tld}%"))
        
        # Apply all filters
        if filters:
            query_obj = query_obj.filter(and_(*filters))
        
        # Order by creation date (newest first)
        query_obj = query_obj.order_by(desc(Credential.created_at))
        
        # Apply pagination
        credentials = query_obj.offset(offset).limit(limit).all()
        
        return [CredentialResponse.from_orm(cred) for cred in credentials]
    
    def search_credentials_with_count(
        self,
        db: Session,
        query: Optional[str] = None,
        domain: Optional[str] = None,
        username: Optional[str] = None,
        browser: Optional[str] = None,
        tld: Optional[str] = None,
        stealer_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[CredentialResponse], int]:
        """Search credentials with filters and return total count"""
        
        # Start with base query
        base_query = db.query(Credential)
        
        # Apply filters
        filters = []
        
        if query:
            # Full-text search across multiple fields
            search_filter = or_(
                Credential.username.ilike(f"%{query}%"),
                Credential.domain.ilike(f"%{query}%"),
                Credential.url.ilike(f"%{query}%"),
                Credential.browser.ilike(f"%{query}%")
            )
            filters.append(search_filter)
        
        if domain:
            filters.append(Credential.domain.ilike(f"%{domain}%"))
        
        if username:
            filters.append(Credential.username.ilike(f"%{username}%"))
        
        if browser:
            filters.append(Credential.browser.ilike(f"%{browser}%"))
        
        if tld:
            filters.append(Credential.tld.ilike(f"%{tld}%"))
        
        if stealer_name:
            filters.append(Credential.stealer_name.ilike(f"%{stealer_name}%"))
        
        # Apply all filters
        if filters:
            base_query = base_query.filter(and_(*filters))
        
        # Get total count
        total = base_query.count()
        
        # Apply ordering and pagination for results
        credentials = base_query.order_by(desc(Credential.created_at)).offset(offset).limit(limit).all()
        
        # Enrich with duplicate information
        enriched_credentials = self._enrich_credentials_with_duplicates(db, credentials)
        
        return enriched_credentials, total
    
    def search_systems(
        self,
        db: Session,
        query: Optional[str] = None,
        country: Optional[str] = None,
        ip_address: Optional[str] = None,
        computer_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[SystemResponse]:
        """Search systems with filters"""
        
        # Start with base query
        query_obj = db.query(System)
        
        # Apply filters
        filters = []
        
        if query:
            # Full-text search across multiple fields
            search_filter = or_(
                System.computer_name.ilike(f"%{query}%"),
                System.machine_user.ilike(f"%{query}%"),
                System.ip_address.ilike(f"%{query}%"),
                System.country.ilike(f"%{query}%"),
                System.machine_id.ilike(f"%{query}%")
            )
            filters.append(search_filter)
        
        if country:
            filters.append(System.country.ilike(f"%{country}%"))
        
        if ip_address:
            filters.append(System.ip_address.ilike(f"%{ip_address}%"))
        
        if computer_name:
            filters.append(System.computer_name.ilike(f"%{computer_name}%"))
        
        # Apply all filters
        if filters:
            query_obj = query_obj.filter(and_(*filters))
        
        # Order by creation date (newest first)
        query_obj = query_obj.order_by(desc(System.created_at))
        
        # Apply pagination
        systems = query_obj.offset(offset).limit(limit).all()
        
        return [SystemResponse.from_orm(sys) for sys in systems]
    
    def search_systems_with_count(
        self,
        db: Session,
        query: Optional[str] = None,
        country: Optional[str] = None,
        ip_address: Optional[str] = None,
        computer_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[SystemResponse], int]:
        """Search systems with filters and return total count"""
        
        # Start with base query
        base_query = db.query(System)
        
        # Apply filters
        filters = []
        
        if query:
            # Full-text search across multiple fields
            search_filter = or_(
                System.computer_name.ilike(f"%{query}%"),
                System.machine_user.ilike(f"%{query}%"),
                System.ip_address.ilike(f"%{query}%"),
                System.country.ilike(f"%{query}%"),
                System.machine_id.ilike(f"%{query}%")
            )
            filters.append(search_filter)
        
        if country:
            filters.append(System.country.ilike(f"%{country}%"))
        
        if ip_address:
            filters.append(System.ip_address.ilike(f"%{ip_address}%"))
        
        if computer_name:
            filters.append(System.computer_name.ilike(f"%{computer_name}%"))
        
        # Apply all filters
        if filters:
            base_query = base_query.filter(and_(*filters))
        
        # Get total count
        total = base_query.count()
        
        # Apply ordering and pagination for results
        systems = base_query.order_by(desc(System.created_at)).offset(offset).limit(limit).all()
        
        return [SystemResponse.from_orm(sys) for sys in systems], total
    
    def get_statistics(self, db: Session) -> StatisticsResponse:
        """Get overall database statistics"""
        
        total_credentials = db.query(func.count(Credential.id)).scalar()
        total_systems = db.query(func.count(Device.id)).scalar()  # Changed from System to Device
        total_uploads = db.query(func.count(Upload.id)).scalar()
        
        unique_domains = db.query(func.count(func.distinct(Credential.domain))).scalar()
        unique_countries = db.query(func.count(func.distinct(System.country))).scalar() if db.query(System).first() else 0
        unique_stealers = db.query(func.count(func.distinct(Credential.stealer_name))).scalar()
        
        return StatisticsResponse(
            total_credentials=total_credentials or 0,
            total_systems=total_systems or 0,
            total_uploads=total_uploads or 0,
            unique_domains=unique_domains or 0,
            unique_countries=unique_countries or 0,
            unique_stealers=unique_stealers or 0
        )
    
    def get_domain_statistics(self, db: Session, limit: int = 20) -> List[DomainStatistic]:
        """Get top domains by credential count"""
        
        results = db.query(
            Credential.domain,
            func.count(Credential.id).label('count')
        ).filter(
            Credential.domain.isnot(None),
            Credential.domain != ''
        ).group_by(
            Credential.domain
        ).order_by(
            desc('count')
        ).limit(limit).all()
        
        return [DomainStatistic(domain=domain, count=count) for domain, count in results]
    
    def get_country_statistics(self, db: Session, limit: int = 20) -> List[CountryStatistic]:
        """Get top countries by system count"""
        
        results = db.query(
            System.country,
            func.count(System.id).label('count')
        ).filter(
            System.country.isnot(None),
            System.country != ''
        ).group_by(
            System.country
        ).order_by(
            desc('count')
        ).limit(limit).all()
        
        return [CountryStatistic(country=country, count=count) for country, count in results]
    
    def get_stealer_statistics(self, db: Session, limit: int = 20) -> List[StealerStatistic]:
        """Get top stealers by credential count"""
        
        results = db.query(
            Credential.stealer_name,
            func.count(Credential.id).label('count')
        ).filter(
            Credential.stealer_name.isnot(None),
            Credential.stealer_name != ''
        ).group_by(
            Credential.stealer_name
        ).order_by(
            desc('count')
        ).limit(limit).all()
        
        return [StealerStatistic(stealer_name=stealer_name, count=count) for stealer_name, count in results]
    
    # New methods for Device model
    
    def search_devices(
        self,
        db: Session,
        query: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[Device], int]:
        """Search devices with filters - exclude devices with no credentials and no domains"""
        base_query = db.query(Device)
        
        # Filter out devices with 0 credentials AND 0 domains
        base_query = base_query.filter(
            or_(
                Device.total_credentials > 0,
                Device.total_domains > 0
            )
        )
        
        if query:
            search_filter = Device.device_name.ilike(f"%{query}%")
            base_query = base_query.filter(search_filter)
        
        total = base_query.count()
        devices = base_query.order_by(desc(Device.created_at)).offset(offset).limit(limit).all()
        
        return devices, total
    
    def get_device_by_id(self, db: Session, device_id: str) -> Optional[Device]:
        """Get device by ID"""
        return db.query(Device).filter(Device.device_id == device_id).first()
    
    def get_browser_statistics(self, db: Session, limit: int = 20):
        """Get top browsers by credential count"""
        results = db.query(
            Credential.browser,
            func.count(Credential.id).label('count')
        ).filter(
            Credential.browser.isnot(None),
            Credential.browser != ''
        ).group_by(
            Credential.browser
        ).order_by(
            desc('count')
        ).limit(limit).all()
        
        return [{"browser": browser, "count": count} for browser, count in results]
    
    def get_tld_statistics(self, db: Session, limit: int = 20):
        """Get top TLDs by credential count"""
        results = db.query(
            Credential.tld,
            func.count(Credential.id).label('count')
        ).filter(
            Credential.tld.isnot(None),
            Credential.tld != ''
        ).group_by(
            Credential.tld
        ).order_by(
            desc('count')
        ).limit(limit).all()
        
        return [{"tld": tld, "count": count} for tld, count in results]
    
    def get_password_statistics(self, db: Session, limit: int = 20):
        """Get top passwords across all devices"""
        results = db.query(
            PasswordStat.password,
            func.sum(PasswordStat.count).label('total_count')
        ).group_by(
            PasswordStat.password
        ).order_by(
            desc('total_count')
        ).limit(limit).all()
        
        return [{"password": password, "count": count} for password, count in results]
    
    def get_software_statistics(self, db: Session, limit: int = 20):
        """Get most common software across all devices"""
        results = db.query(
            Software.software_name,
            func.count(func.distinct(Software.device_id)).label('device_count')
        ).group_by(
            Software.software_name
        ).order_by(
            desc('device_count')
        ).limit(limit).all()
        
        return [{"software_name": name, "device_count": count} for name, count in results]
    
    def _enrich_credentials_with_duplicates(self, db: Session, credentials: List[Credential]) -> List[CredentialResponse]:
        """Enrich credentials with duplicate detection information"""
        enriched = []
        
        for cred in credentials:
            # Find duplicates: same username + password in the same device
            duplicates = db.query(Credential).filter(
                and_(
                    Credential.device_id == cred.device_id,
                    Credential.username == cred.username,
                    Credential.password == cred.password,
                    Credential.id != cred.id  # Exclude self
                )
            ).all()
            
            # Convert to response model
            cred_response = CredentialResponse.from_orm(cred)
            
            # Add duplicate information
            if duplicates:
                cred_response.is_duplicate = True
                cred_response.duplicate_count = len(duplicates)
                cred_response.duplicate_ids = [d.id for d in duplicates]
            
            enriched.append(cred_response)
        
        return enriched
