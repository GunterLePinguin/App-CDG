from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
import logging
import random
import string

from models import Passenger, Booking, Flight
from schemas import PassengerCreate, PassengerUpdate

logger = logging.getLogger(__name__)

class PassengerService:
    
    async def get_passengers(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        nationality: Optional[str] = None
    ) -> List[Passenger]:
        """Récupérer les passagers avec filtres optionnels"""
        query = db.query(Passenger)
        
        if nationality:
            query = query.filter(Passenger.nationality.ilike(f"%{nationality}%"))
            
        return query.offset(skip).limit(limit).all()
    
    async def get_passenger(self, db: Session, passenger_id: int) -> Optional[Passenger]:
        """Récupérer un passager par ID"""
        return db.query(Passenger).filter(Passenger.id == passenger_id).first()
    
    async def get_passenger_by_email(self, db: Session, email: str) -> Optional[Passenger]:
        """Récupérer un passager par email"""
        return db.query(Passenger).filter(Passenger.email == email).first()
    
    async def create_passenger(self, db: Session, passenger_data: PassengerCreate) -> Passenger:
        """Créer un nouveau passager"""
        # Vérifier si l'email existe déjà
        existing = await self.get_passenger_by_email(db, passenger_data.email)
        if existing:
            raise ValueError("Un passager avec cet email existe déjà")
            
        # Générer un ID frequent flyer si non fourni
        if not passenger_data.frequent_flyer_id:
            passenger_data.frequent_flyer_id = self._generate_frequent_flyer_id()
            
        db_passenger = Passenger(**passenger_data.dict())
        db.add(db_passenger)
        db.commit()
        db.refresh(db_passenger)
        
        logger.info(f"Passager créé: {db_passenger.email}")
        return db_passenger
    
    async def update_passenger(self, db: Session, passenger_id: int, passenger_update: PassengerUpdate) -> Optional[Passenger]:
        """Mettre à jour un passager"""
        db_passenger = await self.get_passenger(db, passenger_id)
        if not db_passenger:
            return None
            
        update_data = passenger_update.dict(exclude_unset=True)
        
        # Vérifier l'unicité de l'email si modifié
        if 'email' in update_data:
            existing = await self.get_passenger_by_email(db, update_data['email'])
            if existing and existing.id != passenger_id:
                raise ValueError("Un passager avec cet email existe déjà")
        
        for field, value in update_data.items():
            setattr(db_passenger, field, value)
        
        db.commit()
        db.refresh(db_passenger)
        
        logger.info(f"Passager mis à jour: {db_passenger.email}")
        return db_passenger
    
    async def delete_passenger(self, db: Session, passenger_id: int) -> bool:
        """Supprimer un passager"""
        db_passenger = await self.get_passenger(db, passenger_id)
        if not db_passenger:
            return False
            
        db.delete(db_passenger)
        db.commit()
        
        logger.info(f"Passager supprimé: {db_passenger.email}")
        return True
    
    async def get_passenger_profile(self, db: Session, passenger_id: int) -> dict:
        """Obtenir le profil complet d'un passager"""
        passenger = await self.get_passenger(db, passenger_id)
        if not passenger:
            return None
            
        # Historique des vols
        bookings = db.query(Booking).filter(Booking.passenger_id == passenger_id).all()
        
        # Destinations visitées
        visited_destinations = db.query(Flight.destination).join(Booking).filter(
            Booking.passenger_id == passenger_id
        ).distinct().all()
        
        # Statistiques
        total_bookings = len(bookings)
        preferred_class = self._get_most_common_class(bookings)
        
        return {
            "passenger": passenger,
            "total_bookings": total_bookings,
            "visited_destinations": [dest[0] for dest in visited_destinations],
            "preferred_class": preferred_class,
            "recent_bookings": bookings[-5:] if bookings else []
        }
    
    async def update_flight_count(self, db: Session, passenger_id: int):
        """Mettre à jour le nombre de vols d'un passager"""
        passenger = await self.get_passenger(db, passenger_id)
        if passenger:
            flight_count = db.query(Booking).filter(
                Booking.passenger_id == passenger_id,
                Booking.status == "CONFIRMED"
            ).count()
            
            passenger.total_flights = flight_count
            db.commit()
    
    def _generate_frequent_flyer_id(self) -> str:
        """Générer un ID frequent flyer unique"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    def _get_most_common_class(self, bookings: List[Booking]) -> str:
        """Obtenir la classe de voyage la plus fréquente"""
        if not bookings:
            return "ECONOMY"
            
        class_counts = {}
        for booking in bookings:
            class_counts[booking.travel_class] = class_counts.get(booking.travel_class, 0) + 1
            
        return max(class_counts, key=class_counts.get)
