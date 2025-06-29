from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# === SCHÉMAS VOLS ===

class FlightBase(BaseModel):
    flight_number: str
    airline: str
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    aircraft_type: Optional[str] = None
    gate: Optional[str] = None
    terminal: Optional[str] = None
    capacity: int = 180
    price: Optional[Decimal] = None

class FlightCreate(FlightBase):
    pass

class FlightUpdate(BaseModel):
    flight_number: Optional[str] = None
    airline: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None
    status: Optional[str] = None
    aircraft_type: Optional[str] = None
    gate: Optional[str] = None
    terminal: Optional[str] = None
    capacity: Optional[int] = None
    occupied_seats: Optional[int] = None
    price: Optional[Decimal] = None

class FlightResponse(FlightBase):
    id: int
    status: str
    occupied_seats: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# === SCHÉMAS PASSAGERS ===

class PassengerBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    nationality: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    frequent_flyer_id: Optional[str] = None
    preferred_destinations: Optional[List[str]] = []
    travel_class_preference: str = "ECONOMY"

class PassengerCreate(PassengerBase):
    pass

class PassengerUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    nationality: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    frequent_flyer_id: Optional[str] = None
    preferred_destinations: Optional[List[str]] = None
    travel_class_preference: Optional[str] = None

class PassengerResponse(PassengerBase):
    id: int
    total_flights: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# === SCHÉMAS SERVICES ===

class ServiceBase(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    location: Optional[str] = None
    terminal: Optional[str] = None
    capacity: Optional[int] = None
    opening_hours: Optional[str] = None
    rating: Optional[Decimal] = None
    price_range: Optional[str] = None

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    terminal: Optional[str] = None
    status: Optional[str] = None
    capacity: Optional[int] = None
    current_usage: Optional[int] = None
    opening_hours: Optional[str] = None
    rating: Optional[Decimal] = None
    price_range: Optional[str] = None

class ServiceResponse(ServiceBase):
    id: int
    status: str
    current_usage: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# === SCHÉMAS RÉSERVATIONS ===

class BookingBase(BaseModel):
    passenger_id: int
    flight_id: int
    seat_number: Optional[str] = None
    travel_class: str = "ECONOMY"
    baggage_count: int = 0
    special_requirements: Optional[str] = None
    price: Optional[Decimal] = None

class BookingCreate(BookingBase):
    pass

class BookingResponse(BookingBase):
    id: int
    booking_reference: str
    status: str
    booking_date: datetime
    check_in_time: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# === SCHÉMAS RECOMMANDATIONS ===

class RecommendationResponse(BaseModel):
    id: int
    passenger_id: int
    flight_id: int
    recommendation_type: Optional[str] = None
    score: Optional[Decimal] = None
    reason: Optional[str] = None
    created_at: datetime
    is_sent: bool
    
    # Relations
    flight: Optional[FlightResponse] = None
    
    class Config:
        from_attributes = True

# === SCHÉMAS ÉVÉNEMENTS ===

class EventCreate(BaseModel):
    event_type: str
    flight_id: Optional[int] = None
    passenger_id: Optional[int] = None
    description: Optional[str] = None
    event_metadata: Optional[dict] = None

class EventResponse(BaseModel):
    id: int
    event_type: str
    flight_id: Optional[int] = None
    passenger_id: Optional[int] = None
    description: Optional[str] = None
    timestamp: datetime
    event_metadata: Optional[dict] = None
    
    class Config:
        from_attributes = True

# === SCHÉMAS EMAILS ===

class EmailContent(BaseModel):
    subject: str
    body: str
    html_body: Optional[str] = None
    recipient_email: str
    recipient_name: str

class EmailTemplate(BaseModel):
    template_type: str
    passenger_data: dict
    flight_data: Optional[dict] = None
    personalization: dict
