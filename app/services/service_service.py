from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import logging
from datetime import datetime, timedelta

from models import Service
from schemas import ServiceCreate, ServiceUpdate

logger = logging.getLogger(__name__)

class ServiceService:
    
    async def get_services(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        service_type: Optional[str] = None,
        terminal: Optional[str] = None
    ) -> List[Service]:
        """Récupérer les services avec filtres optionnels"""
        query = db.query(Service)
        
        if service_type:
            query = query.filter(Service.type == service_type)
        if terminal:
            query = query.filter(Service.terminal == terminal)
            
        return query.offset(skip).limit(limit).all()
    
    async def get_service(self, db: Session, service_id: int) -> Optional[Service]:
        """Récupérer un service par ID"""
        return db.query(Service).filter(Service.id == service_id).first()
    
    async def create_service(self, db: Session, service_data: ServiceCreate) -> Service:
        """Créer un nouveau service"""
        db_service = Service(**service_data.dict())
        db.add(db_service)
        db.commit()
        db.refresh(db_service)
        
        logger.info(f"Service créé: {db_service.name}")
        return db_service
    
    async def update_service(self, db: Session, service_id: int, service_update: ServiceUpdate) -> Optional[Service]:
        """Mettre à jour un service"""
        db_service = await self.get_service(db, service_id)
        if not db_service:
            return None
            
        update_data = service_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_service, field, value)
        
        db.commit()
        db.refresh(db_service)
        
        logger.info(f"Service mis à jour: {db_service.name}")
        return db_service
    
    async def delete_service(self, db: Session, service_id: int) -> bool:
        """Supprimer un service"""
        db_service = await self.get_service(db, service_id)
        if not db_service:
            return False
            
        db.delete(db_service)
        db.commit()
        
        logger.info(f"Service supprimé: {db_service.name}")
        return True
    
    async def get_services_by_type(self, db: Session, service_type: str) -> List[Service]:
        """Récupérer les services par type"""
        return db.query(Service).filter(Service.type == service_type).all()
    
    async def get_services_by_terminal(self, db: Session, terminal: str) -> List[Service]:
        """Récupérer les services par terminal"""
        return db.query(Service).filter(Service.terminal == terminal).all()
    
    async def update_service_usage(self, db: Session, service_id: int, usage_change: int):
        """Mettre à jour l'utilisation d'un service"""
        service = await self.get_service(db, service_id)
        if service:
            new_usage = max(0, service.current_usage + usage_change)
            service.current_usage = min(new_usage, service.capacity or new_usage)
            db.commit()
    
    async def get_service_stats(self, db: Session) -> dict:
        """Statistiques des services"""
        # Services par type
        services_by_type = db.query(
            Service.type, func.count(Service.id)
        ).group_by(Service.type).all()
        
        # Taux d'utilisation moyen
        avg_usage = db.query(
            func.avg(Service.current_usage * 100.0 / Service.capacity)
        ).filter(Service.capacity > 0).scalar() or 0
        
        # Services les plus utilisés
        top_services = db.query(Service).filter(
            Service.capacity > 0
        ).order_by(
            (Service.current_usage * 100.0 / Service.capacity).desc()
        ).limit(5).all()
        
        return {
            "services_by_type": dict(services_by_type),
            "average_usage_rate": round(avg_usage, 2),
            "top_utilized_services": [
                {
                    "name": service.name,
                    "type": service.type,
                    "usage_rate": round((service.current_usage / service.capacity) * 100, 2) if service.capacity else 0
                }
                for service in top_services
            ]
        }
    
    async def get_realtime_data(self, db: Session) -> dict:
        """Données temps réel des services"""
        # Services avec forte utilisation
        high_usage_services = db.query(Service).filter(
            Service.capacity > 0,
            Service.current_usage / Service.capacity > 0.8
        ).all()
        
        # Services fermés ou en maintenance
        inactive_services = db.query(Service).filter(
            Service.status != "ACTIVE"
        ).all()
        
        return {
            "high_usage_services": [
                {
                    "id": service.id,
                    "name": service.name,
                    "type": service.type,
                    "terminal": service.terminal,
                    "usage_rate": round((service.current_usage / service.capacity) * 100, 2),
                    "current_usage": service.current_usage,
                    "capacity": service.capacity
                }
                for service in high_usage_services
            ],
            "inactive_services": [
                {
                    "id": service.id,
                    "name": service.name,
                    "type": service.type,
                    "status": service.status,
                    "terminal": service.terminal
                }
                for service in inactive_services
            ]
        }
