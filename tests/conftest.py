import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

from app.main import app
from app.database import get_db, Base
from app.models import Flight, Passenger, Service, Booking

# Base de données de test en mémoire
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override de la dépendance
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_flight_data():
    return {
        "flight_number": "AF1234",
        "airline": "Air France",
        "origin": "Paris CDG",
        "destination": "New York JFK",
        "departure_time": (datetime.now() + timedelta(hours=2)).isoformat(),
        "arrival_time": (datetime.now() + timedelta(hours=10)).isoformat(),
        "aircraft_type": "Boeing 777",
        "gate": "A12",
        "terminal": "2E",
        "capacity": 350,
        "price": 650.00
    }

@pytest.fixture
def sample_passenger_data():
    return {
        "first_name": "Jean",
        "last_name": "Dupont",
        "email": "jean.dupont@test.com",
        "nationality": "French",
        "preferred_destinations": ["New York", "London"],
        "travel_class_preference": "BUSINESS"
    }

@pytest.fixture
def sample_service_data():
    return {
        "name": "Restaurant Test",
        "type": "RESTAURANT",
        "description": "Restaurant de test",
        "location": "Terminal 2E",
        "terminal": "2E",
        "capacity": 100,
        "opening_hours": "06:00-23:00"
    }
