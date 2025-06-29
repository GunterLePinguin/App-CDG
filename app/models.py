from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ARRAY, ForeignKey, TIMESTAMP, JSON, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Flight(Base):
    __tablename__ = "flights"
    
    id = Column(Integer, primary_key=True, index=True)
    flight_number = Column(String(10), unique=True, nullable=False, index=True)
    airline = Column(String(100), nullable=False)
    origin = Column(String(100), nullable=False)
    destination = Column(String(100), nullable=False, index=True)
    departure_time = Column(TIMESTAMP, nullable=False, index=True)
    arrival_time = Column(TIMESTAMP, nullable=False)
    status = Column(String(20), default="SCHEDULED", index=True)
    aircraft_type = Column(String(50))
    gate = Column(String(10))
    terminal = Column(String(5))
    capacity = Column(Integer, default=180)
    occupied_seats = Column(Integer, default=0)
    price = Column(Numeric(10, 2))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relations
    bookings = relationship("Booking", back_populates="flight")
    recommendations = relationship("Recommendation", back_populates="flight")
    events = relationship("Event", back_populates="flight")

class Passenger(Base):
    __tablename__ = "passengers"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20))
    nationality = Column(String(50), index=True)
    date_of_birth = Column(DateTime)
    frequent_flyer_id = Column(String(20))
    preferred_destinations = Column(ARRAY(String))
    travel_class_preference = Column(String(20), default="ECONOMY")
    total_flights = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relations
    bookings = relationship("Booking", back_populates="passenger")
    recommendations = relationship("Recommendation", back_populates="passenger")

class Service(Base):
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False, index=True)
    description = Column(Text)
    location = Column(String(100))
    terminal = Column(String(5), index=True)
    status = Column(String(20), default="ACTIVE")
    capacity = Column(Integer)
    current_usage = Column(Integer, default=0)
    opening_hours = Column(String(50))
    rating = Column(Numeric(3, 2), default=0.0)
    price_range = Column(String(20))
    created_at = Column(TIMESTAMP, server_default=func.now())

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    passenger_id = Column(Integer, ForeignKey("passengers.id"), nullable=False, index=True)
    flight_id = Column(Integer, ForeignKey("flights.id"), nullable=False, index=True)
    booking_reference = Column(String(10), unique=True, nullable=False)
    seat_number = Column(String(5))
    travel_class = Column(String(20), default="ECONOMY")
    status = Column(String(20), default="CONFIRMED")
    booking_date = Column(TIMESTAMP, server_default=func.now())
    check_in_time = Column(TIMESTAMP)
    baggage_count = Column(Integer, default=0)
    special_requirements = Column(Text)
    price = Column(Numeric(10, 2))
    
    # Relations
    passenger = relationship("Passenger", back_populates="bookings")
    flight = relationship("Flight", back_populates="bookings")

class Recommendation(Base):
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    passenger_id = Column(Integer, ForeignKey("passengers.id"), nullable=False, index=True)
    flight_id = Column(Integer, ForeignKey("flights.id"), nullable=False, index=True)
    recommendation_type = Column(String(50))
    score = Column(Numeric(5, 2))
    reason = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    is_sent = Column(Boolean, default=False)
    
    # Relations
    passenger = relationship("Passenger", back_populates="recommendations")
    flight = relationship("Flight", back_populates="recommendations")

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    flight_id = Column(Integer, ForeignKey("flights.id"))
    passenger_id = Column(Integer)
    description = Column(Text)
    timestamp = Column(TIMESTAMP, server_default=func.now(), index=True)
    event_metadata = Column("event_metadata", JSON)
    
    # Relations
    flight = relationship("Flight", back_populates="events")
