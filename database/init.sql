-- Création de la base de données CDG
-- Tables : flights, passengers, services, bookings, recommendations

-- Table des vols
CREATE TABLE IF NOT EXISTS flights (
    id SERIAL PRIMARY KEY,
    flight_number VARCHAR(10) NOT NULL UNIQUE,
    airline VARCHAR(100) NOT NULL,
    origin VARCHAR(100) NOT NULL,
    destination VARCHAR(100) NOT NULL,
    departure_time TIMESTAMP NOT NULL,
    arrival_time TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'SCHEDULED',
    aircraft_type VARCHAR(50),
    gate VARCHAR(10),
    terminal VARCHAR(5),
    capacity INTEGER DEFAULT 180,
    occupied_seats INTEGER DEFAULT 0,
    price DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des passagers
CREATE TABLE IF NOT EXISTS passengers (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    nationality VARCHAR(50),
    date_of_birth DATE,
    frequent_flyer_id VARCHAR(20),
    preferred_destinations TEXT[], -- Array de destinations préférées
    travel_class_preference VARCHAR(20) DEFAULT 'ECONOMY',
    total_flights INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des services
CREATE TABLE IF NOT EXISTS services (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL, -- RESTAURANT, SHOP, LOUNGE, TRANSPORT, etc.
    description TEXT,
    location VARCHAR(100),
    terminal VARCHAR(5),
    status VARCHAR(20) DEFAULT 'ACTIVE',
    capacity INTEGER,
    current_usage INTEGER DEFAULT 0,
    opening_hours VARCHAR(50),
    rating DECIMAL(3,2) DEFAULT 0.0,
    price_range VARCHAR(20), -- €, €€, €€€
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des réservations/billets
CREATE TABLE IF NOT EXISTS bookings (
    id SERIAL PRIMARY KEY,
    passenger_id INTEGER REFERENCES passengers(id) ON DELETE CASCADE,
    flight_id INTEGER REFERENCES flights(id) ON DELETE CASCADE,
    booking_reference VARCHAR(10) UNIQUE NOT NULL,
    seat_number VARCHAR(5),
    travel_class VARCHAR(20) DEFAULT 'ECONOMY',
    status VARCHAR(20) DEFAULT 'CONFIRMED',
    booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    check_in_time TIMESTAMP,
    baggage_count INTEGER DEFAULT 0,
    special_requirements TEXT,
    price DECIMAL(10,2)
);

-- Table des recommandations
CREATE TABLE IF NOT EXISTS recommendations (
    id SERIAL PRIMARY KEY,
    passenger_id INTEGER REFERENCES passengers(id) ON DELETE CASCADE,
    flight_id INTEGER REFERENCES flights(id) ON DELETE CASCADE,
    recommendation_type VARCHAR(50), -- SIMILAR_PASSENGERS, DESTINATION_BASED, etc.
    score DECIMAL(5,2),
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_sent BOOLEAN DEFAULT FALSE
);

-- Table des événements (pour le suivi temps réel)
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL, -- BOARDING, DELAY, GATE_CHANGE, etc.
    flight_id INTEGER REFERENCES flights(id),
    passenger_id INTEGER,
    description TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_metadata JSONB -- Données additionnelles
);

-- Indexes pour optimiser les requêtes
CREATE INDEX IF NOT EXISTS idx_flights_departure ON flights(departure_time);
CREATE INDEX IF NOT EXISTS idx_flights_status ON flights(status);
CREATE INDEX IF NOT EXISTS idx_passengers_email ON passengers(email);
CREATE INDEX IF NOT EXISTS idx_bookings_passenger ON bookings(passenger_id);
CREATE INDEX IF NOT EXISTS idx_bookings_flight ON bookings(flight_id);
CREATE INDEX IF NOT EXISTS idx_events_type_time ON events(event_type, timestamp);

-- Trigger pour mettre à jour updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_flights_updated_at BEFORE UPDATE ON flights
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_passengers_updated_at BEFORE UPDATE ON passengers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Données d'exemple
INSERT INTO flights (flight_number, airline, origin, destination, departure_time, arrival_time, aircraft_type, gate, terminal, capacity, price) VALUES
('AF1234', 'Air France', 'Paris CDG', 'New York JFK', CURRENT_TIMESTAMP + INTERVAL '2 hours', CURRENT_TIMESTAMP + INTERVAL '10 hours', 'Boeing 777', 'A12', '2E', 350, 650.00),
('LH5678', 'Lufthansa', 'Paris CDG', 'Frankfurt', CURRENT_TIMESTAMP + INTERVAL '3 hours', CURRENT_TIMESTAMP + INTERVAL '4 hours 30 minutes', 'Airbus A320', 'B05', '1', 180, 250.00),
('BA9012', 'British Airways', 'Paris CDG', 'London Heathrow', CURRENT_TIMESTAMP + INTERVAL '1 hour', CURRENT_TIMESTAMP + INTERVAL '2 hours 15 minutes', 'Airbus A319', 'C22', '2A', 150, 180.00);

INSERT INTO passengers (first_name, last_name, email, nationality, date_of_birth, frequent_flyer_id, preferred_destinations, travel_class_preference) VALUES
('Jean', 'Dupont', 'jean.dupont@email.com', 'French', '1985-03-15', 'AF123456', ARRAY['New York', 'London', 'Tokyo'], 'BUSINESS'),
('Marie', 'Martin', 'marie.martin@email.com', 'French', '1990-07-22', 'LH789012', ARRAY['Berlin', 'Munich', 'Vienna'], 'ECONOMY'),
('Pierre', 'Durand', 'pierre.durand@email.com', 'French', '1978-11-08', NULL, ARRAY['Madrid', 'Barcelona'], 'ECONOMY');

INSERT INTO services (name, type, description, location, terminal, capacity, opening_hours, rating, price_range) VALUES
('Le Grand Comptoir', 'RESTAURANT', 'Restaurant gastronomique français', 'Terminal 2E, Niveau 3', '2E', 80, '06:00-23:00', 4.2, '€€€'),
('Paul Boulangerie', 'RESTAURANT', 'Boulangerie traditionnelle', 'Terminal 1, Hall A', '1', 40, '05:00-22:00', 3.8, '€'),
('Air France Lounge', 'LOUNGE', 'Salon business class', 'Terminal 2E, Satellite', '2E', 200, '05:00-01:00', 4.5, '€€€'),
('Relay', 'SHOP', 'Presse et souvenirs', 'Terminal 2A, Zone publique', '2A', 20, '05:30-23:30', 3.5, '€€');

-- Quelques réservations d'exemple
INSERT INTO bookings (passenger_id, flight_id, booking_reference, seat_number, travel_class, price) VALUES
(1, 1, 'CDG001', '12A', 'BUSINESS', 1200.00),
(2, 2, 'CDG002', '23C', 'ECONOMY', 250.00),
(3, 3, 'CDG003', '15F', 'ECONOMY', 180.00);
