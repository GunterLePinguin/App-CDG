from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import random
import string

from models import Booking, Flight, Passenger
from schemas import BookingCreate

logger = logging.getLogger(__name__)

class BookingService:
    
    async def get_bookings(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        passenger_id: Optional[int] = None,
        flight_id: Optional[int] = None
    ) -> List[Booking]:
        """Récupérer les réservations avec filtres optionnels"""
        query = db.query(Booking)
        
        if passenger_id:
            query = query.filter(Booking.passenger_id == passenger_id)
        if flight_id:
            query = query.filter(Booking.flight_id == flight_id)
            
        return query.offset(skip).limit(limit).all()
    
    async def get_booking(self, db: Session, booking_id: int) -> Optional[Booking]:
        """Récupérer une réservation par ID"""
        return db.query(Booking).filter(Booking.id == booking_id).first()
    
    async def get_booking_by_reference(self, db: Session, booking_reference: str) -> Optional[Booking]:
        """Récupérer une réservation par référence"""
        return db.query(Booking).filter(Booking.booking_reference == booking_reference).first()
    
    async def create_booking(self, db: Session, booking_data: BookingCreate) -> Booking:
        """Créer une nouvelle réservation"""
        # Vérifier que le vol existe et a de la place
        flight = db.query(Flight).filter(Flight.id == booking_data.flight_id).first()
        if not flight:
            raise ValueError("Vol non trouvé")
            
        if flight.occupied_seats >= flight.capacity:
            raise ValueError("Vol complet")
            
        # Vérifier que le passager existe
        passenger = db.query(Passenger).filter(Passenger.id == booking_data.passenger_id).first()
        if not passenger:
            raise ValueError("Passager non trouvé")
        
        # Générer une référence de réservation unique
        booking_reference = await self._generate_booking_reference(db)
        
        # Assigner un siège si non spécifié
        seat_number = booking_data.seat_number or await self._assign_seat(db, flight, booking_data.travel_class)
        
        # Créer la réservation
        db_booking = Booking(
            **booking_data.dict(),
            booking_reference=booking_reference,
            seat_number=seat_number
        )
        db.add(db_booking)
        
        # Mettre à jour le nombre de sièges occupés
        flight.occupied_seats += 1
        
        db.commit()
        db.refresh(db_booking)
        
        # Mettre à jour le nombre total de vols du passager
        from services.passenger_service import PassengerService
        passenger_service = PassengerService()
        await passenger_service.update_flight_count(db, booking_data.passenger_id)
        
        logger.info(f"Réservation créée: {booking_reference}")
        return db_booking
    
    async def delete_booking(self, db: Session, booking_id: int) -> bool:
        """Supprimer une réservation"""
        db_booking = await self.get_booking(db, booking_id)
        if not db_booking:
            return False
        
        # Libérer le siège dans le vol
        flight = db.query(Flight).filter(Flight.id == db_booking.flight_id).first()
        if flight and flight.occupied_seats > 0:
            flight.occupied_seats -= 1
            
        db.delete(db_booking)
        db.commit()
        
        logger.info(f"Réservation supprimée: {db_booking.booking_reference}")
        return True
    
    async def check_in_passenger(self, db: Session, booking_id: int) -> Optional[Booking]:
        """Enregistrer un passager"""
        booking = await self.get_booking(db, booking_id)
        if not booking:
            return None
            
        from datetime import datetime
        booking.check_in_time = datetime.now()
        booking.status = "CHECKED_IN"
        
        db.commit()
        db.refresh(booking)
        
        logger.info(f"Passager enregistré: {booking.booking_reference}")
        return booking
    
    async def get_passenger_bookings(self, db: Session, passenger_id: int) -> List[Booking]:
        """Récupérer toutes les réservations d'un passager"""
        return db.query(Booking).filter(Booking.passenger_id == passenger_id).all()
    
    async def get_flight_bookings(self, db: Session, flight_id: int) -> List[Booking]:
        """Récupérer toutes les réservations d'un vol"""
        return db.query(Booking).filter(Booking.flight_id == flight_id).all()
    
    async def _generate_booking_reference(self, db: Session) -> str:
        """Générer une référence de réservation unique"""
        while True:
            reference = 'CDG' + ''.join(random.choices(string.digits, k=6))
            existing = await self.get_booking_by_reference(db, reference)
            if not existing:
                return reference
    
    async def _assign_seat(self, db: Session, flight: Flight, travel_class: str) -> str:
        """Assigner automatiquement un siège"""
        # Récupérer les sièges déjà pris pour ce vol
        taken_seats = db.query(Booking.seat_number).filter(
            Booking.flight_id == flight.id,
            Booking.seat_number.isnot(None)
        ).all()
        taken_seats = {seat[0] for seat in taken_seats}
        
        # Générer les sièges selon la classe
        if travel_class == "BUSINESS":
            rows = range(1, 6)  # Rangées 1-5 pour business
            letters = "ABCD"
        elif travel_class == "FIRST":
            rows = range(1, 3)  # Rangées 1-2 pour première
            letters = "AB"
        else:  # ECONOMY
            rows = range(6, 41)  # Rangées 6-40 pour économique
            letters = "ABCDEF"
        
        # Trouver le premier siège disponible
        for row in rows:
            for letter in letters:
                seat = f"{row}{letter}"
                if seat not in taken_seats:
                    return seat
        
        # Si aucun siège n'est trouvé, assigner un siège générique
        return f"{flight.occupied_seats + 1}A"
