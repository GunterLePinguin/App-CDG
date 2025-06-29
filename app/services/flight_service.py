from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from models import Flight, Booking, Event
from schemas import FlightCreate, FlightUpdate

logger = logging.getLogger(__name__)

class FlightService:
    
    async def get_flights(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[str] = None,
        destination: Optional[str] = None
    ) -> List[Flight]:
        """Récupérer les vols avec filtres optionnels"""
        query = db.query(Flight)
        
        if status:
            query = query.filter(Flight.status == status)
        if destination:
            query = query.filter(Flight.destination.ilike(f"%{destination}%"))
            
        return query.offset(skip).limit(limit).all()
    
    async def get_flight(self, db: Session, flight_id: int) -> Optional[Flight]:
        """Récupérer un vol par ID"""
        return db.query(Flight).filter(Flight.id == flight_id).first()
    
    async def create_flight(self, db: Session, flight_data: FlightCreate) -> Flight:
        """Créer un nouveau vol"""
        db_flight = Flight(**flight_data.dict())
        db.add(db_flight)
        db.commit()
        db.refresh(db_flight)
        
        # Créer un événement
        await self._create_flight_event(db, db_flight.id, "FLIGHT_CREATED", "Nouveau vol créé")
        
        logger.info(f"Vol créé: {db_flight.flight_number}")
        return db_flight
    
    async def update_flight(self, db: Session, flight_id: int, flight_update: FlightUpdate) -> Optional[Flight]:
        """Mettre à jour un vol"""
        db_flight = await self.get_flight(db, flight_id)
        if not db_flight:
            return None
            
        update_data = flight_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_flight, field, value)
        
        db.commit()
        db.refresh(db_flight)
        
        # Créer un événement pour les changements importants
        if 'status' in update_data:
            await self._create_flight_event(
                db, flight_id, "STATUS_CHANGE", 
                f"Statut changé vers {update_data['status']}"
            )
        if 'gate' in update_data:
            await self._create_flight_event(
                db, flight_id, "GATE_CHANGE", 
                f"Porte changée vers {update_data['gate']}"
            )
            
        logger.info(f"Vol mis à jour: {db_flight.flight_number}")
        return db_flight
    
    async def delete_flight(self, db: Session, flight_id: int) -> bool:
        """Supprimer un vol"""
        db_flight = await self.get_flight(db, flight_id)
        if not db_flight:
            return False
            
        db.delete(db_flight)
        db.commit()
        
        logger.info(f"Vol supprimé: {db_flight.flight_number}")
        return True
    
    async def get_dashboard_stats(self, db: Session) -> dict:
        """Statistiques pour le dashboard"""
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        # Vols du jour
        daily_flights = db.query(Flight).filter(
            func.date(Flight.departure_time) == today
        ).count()
        
        # Vols par statut
        status_counts = db.query(
            Flight.status, func.count(Flight.id)
        ).filter(
            func.date(Flight.departure_time) == today
        ).group_by(Flight.status).all()
        
        # Taux d'occupation moyen
        avg_occupation = db.query(
            func.avg(Flight.occupied_seats * 100.0 / Flight.capacity)
        ).filter(
            func.date(Flight.departure_time) == today
        ).scalar() or 0
        
        # Destinations populaires
        popular_destinations = db.query(
            Flight.destination, func.count(Flight.id)
        ).filter(
            Flight.departure_time >= datetime.now()
        ).group_by(Flight.destination).order_by(
            func.count(Flight.id).desc()
        ).limit(5).all()
        
        return {
            "daily_flights": daily_flights,
            "status_distribution": dict(status_counts),
            "average_occupation_rate": round(avg_occupation, 2),
            "popular_destinations": [
                {"destination": dest, "count": count} 
                for dest, count in popular_destinations
            ]
        }
    
    async def get_realtime_data(self, db: Session) -> dict:
        """Données temps réel des vols"""
        now = datetime.now()
        
        # Vols des prochaines 24 heures
        upcoming_flights = db.query(Flight).filter(
            and_(
                Flight.departure_time >= now,
                Flight.departure_time <= now + timedelta(hours=24)
            )
        ).order_by(Flight.departure_time).limit(20).all()
        
        # Événements récents
        recent_events = db.query(Event).filter(
            Event.timestamp >= now - timedelta(hours=2)
        ).order_by(Event.timestamp.desc()).limit(10).all()
        
        return {
            "upcoming_flights": [
                {
                    "id": flight.id,
                    "flight_number": flight.flight_number,
                    "destination": flight.destination,
                    "departure_time": flight.departure_time,
                    "status": flight.status,
                    "gate": flight.gate,
                    "occupied_seats": flight.occupied_seats,
                    "capacity": flight.capacity
                }
                for flight in upcoming_flights
            ],
            "recent_events": [
                {
                    "id": event.id,
                    "type": event.event_type,
                    "description": event.description,
                    "timestamp": event.timestamp
                }
                for event in recent_events
            ]
        }
    
    async def _create_flight_event(self, db: Session, flight_id: int, event_type: str, description: str):
        """Créer un événement de vol"""
        event = Event(
            event_type=event_type,
            flight_id=flight_id,
            description=description
        )
        db.add(event)
        db.commit()
