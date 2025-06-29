import asyncio
import asyncpg
import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from faker import Faker
import numpy as np

fake = Faker('fr_FR')
logger = logging.getLogger(__name__)

class BaseDataGenerator:
    """Classe de base pour tous les générateurs de données"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.connection = None
    
    async def connect(self):
        """Se connecter à la base de données"""
        if not self.connection:
            self.connection = await asyncpg.connect(self.database_url)
    
    async def close(self):
        """Fermer la connexion"""
        if self.connection:
            await self.connection.close()
    
    async def execute_query(self, query: str, *args):
        """Exécuter une requête"""
        await self.connect()
        return await self.connection.execute(query, *args)
    
    async def fetch_query(self, query: str, *args):
        """Récupérer des données"""
        await self.connect()
        return await self.connection.fetch(query, *args)


class FlightDataGenerator(BaseDataGenerator):
    """Générateur de données pour les vols"""
    
    def __init__(self, database_url: str):
        super().__init__(database_url)
        self.airlines = ["Air France", "Lufthansa", "British Airways", "Emirates", "KLM", "Delta", "United"]
        self.aircraft_types = ["Boeing 777", "Airbus A320", "Airbus A380", "Boeing 737", "Airbus A350"]
        self.destinations = [
            "New York JFK", "London Heathrow", "Tokyo Narita", "Dubai", "Frankfurt",
            "Amsterdam", "Madrid", "Barcelona", "Rome", "Berlin", "Munich",
            "Singapore", "Hong Kong", "Sydney", "Montreal", "Los Angeles"
        ]
        self.terminals = ["1", "2A", "2B", "2C", "2D", "2E", "2F", "2G", "3"]
        self.gates = [f"{random.choice(['A', 'B', 'C', 'D', 'E'])}{i:02d}" for i in range(1, 51)]
    
    async def generate_new_flight(self) -> Dict[str, Any]:
        """Générer un nouveau vol"""
        departure_time = datetime.now() + timedelta(
            hours=random.randint(1, 72),
            minutes=random.choice([0, 15, 30, 45])
        )
        
        flight_duration = random.randint(60, 720)  # 1h à 12h
        arrival_time = departure_time + timedelta(minutes=flight_duration)
        
        destination = random.choice(self.destinations)
        airline = random.choice(self.airlines)
        aircraft = random.choice(self.aircraft_types)
        
        # Générer le numéro de vol
        airline_code = airline[:2].upper()
        flight_number = f"{airline_code}{random.randint(1000, 9999)}"
        
        capacity = random.choice([150, 180, 220, 350, 400])
        occupied_seats = random.randint(50, min(capacity, capacity - 20))
        
        return {
            "flight_number": flight_number,
            "airline": airline,
            "origin": "Paris CDG",
            "destination": destination,
            "departure_time": departure_time,
            "arrival_time": arrival_time,
            "aircraft_type": aircraft,
            "gate": random.choice(self.gates),
            "terminal": random.choice(self.terminals),
            "capacity": capacity,
            "occupied_seats": occupied_seats,
            "price": round(random.uniform(150.0, 1500.0), 2),
            "status": "SCHEDULED"
        }
    
    async def update_flight_status(self):
        """Mettre à jour les statuts des vols existants"""
        now = datetime.now()
        
        # Récupérer les vols des prochaines 24 heures
        flights = await self.fetch_query("""
            SELECT id, departure_time, status, occupied_seats, capacity 
            FROM flights 
            WHERE departure_time BETWEEN $1 AND $2
        """, now, now + timedelta(hours=24))
        
        for flight in flights:
            flight_id = flight['id']
            current_status = flight['status']
            departure_time = flight['departure_time']
            
            # Calculer le nouveau statut basé sur l'heure
            time_to_departure = (departure_time - now).total_seconds() / 3600  # heures
            
            new_status = current_status
            
            if time_to_departure <= 0 and current_status != "DEPARTED":
                new_status = "DEPARTED"
            elif time_to_departure <= 0.5 and current_status == "BOARDING":
                new_status = "DEPARTED"
            elif time_to_departure <= 1 and current_status in ["ON_TIME", "DELAYED"]:
                new_status = "BOARDING"
            elif time_to_departure <= 2 and random.random() < 0.1:  # 10% de chance de retard
                new_status = "DELAYED"
            elif time_to_departure <= 3 and random.random() < 0.02:  # 2% de chance d'annulation
                new_status = "CANCELLED"
            
            # Mettre à jour occasionnellement le nombre de passagers
            new_occupied_seats = flight['occupied_seats']
            if random.random() < 0.3:  # 30% de chance de changement
                change = random.randint(-5, 10)
                new_occupied_seats = max(0, min(flight['capacity'], flight['occupied_seats'] + change))
            
            if new_status != current_status or new_occupied_seats != flight['occupied_seats']:
                await self.execute_query("""
                    UPDATE flights 
                    SET status = $1, occupied_seats = $2, updated_at = CURRENT_TIMESTAMP
                    WHERE id = $3
                """, new_status, new_occupied_seats, flight_id)
                
                logger.info(f"Vol {flight_id} mis à jour: {current_status} -> {new_status}")
    
    async def run_continuous_updates(self, interval: int):
        """Lancer la mise à jour continue"""
        logger.info(f"Démarrage des mises à jour de vols (interval: {interval}s)")
        
        while True:
            try:
                # Générer un nouveau vol occasionnellement
                if random.random() < 0.1:  # 10% de chance
                    flight_data = await self.generate_new_flight()
                    await self.execute_query("""
                        INSERT INTO flights (flight_number, airline, origin, destination, 
                                           departure_time, arrival_time, aircraft_type, gate, 
                                           terminal, capacity, occupied_seats, price, status)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    """, *flight_data.values())
                    logger.info(f"Nouveau vol créé: {flight_data['flight_number']}")
                
                # Mettre à jour les statuts
                await self.update_flight_status()
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Erreur dans la mise à jour des vols: {e}")
                await asyncio.sleep(interval)


class PassengerDataGenerator(BaseDataGenerator):
    """Générateur de données pour les passagers"""
    
    def __init__(self, database_url: str):
        super().__init__(database_url)
        self.nationalities = ["French", "German", "British", "American", "Italian", "Spanish", "Japanese"]
        self.destinations = [
            "New York", "London", "Tokyo", "Dubai", "Frankfurt", "Amsterdam", 
            "Madrid", "Barcelona", "Rome", "Berlin", "Singapore"
        ]
        self.travel_classes = ["ECONOMY", "BUSINESS", "FIRST"]
    
    async def generate_passenger(self) -> Dict[str, Any]:
        """Générer un nouveau passager"""
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = f"{first_name.lower()}.{last_name.lower()}@{fake.domain_name()}"
        
        preferred_destinations = random.sample(self.destinations, random.randint(1, 4))
        
        return {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": fake.phone_number(),
            "nationality": random.choice(self.nationalities),
            "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=80),
            "preferred_destinations": preferred_destinations,
            "travel_class_preference": random.choice(self.travel_classes)
        }
    
    async def generate_booking(self):
        """Générer une réservation aléatoire"""
        # Récupérer des vols et passagers existants
        flights = await self.fetch_query("SELECT id FROM flights WHERE status = 'SCHEDULED' LIMIT 50")
        passengers = await self.fetch_query("SELECT id FROM passengers ORDER BY RANDOM() LIMIT 20")
        
        if flights and passengers:
            flight_id = random.choice(flights)['id']
            passenger_id = random.choice(passengers)['id']
            
            # Vérifier si la réservation n'existe pas déjà
            existing = await self.fetch_query("""
                SELECT id FROM bookings WHERE passenger_id = $1 AND flight_id = $2
            """, passenger_id, flight_id)
            
            if not existing:
                booking_ref = f"CDG{random.randint(100000, 999999)}"
                travel_class = random.choice(self.travel_classes)
                seat_number = f"{random.randint(1, 40)}{random.choice('ABCDEF')}"
                
                await self.execute_query("""
                    INSERT INTO bookings (passenger_id, flight_id, booking_reference, 
                                        seat_number, travel_class, price)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, passenger_id, flight_id, booking_ref, seat_number, travel_class, 
                    round(random.uniform(100.0, 2000.0), 2))
                
                logger.info(f"Nouvelle réservation créée: {booking_ref}")
    
    async def run_continuous_generation(self, interval: int):
        """Génération continue de passagers et réservations"""
        logger.info(f"Démarrage de la génération de passagers (interval: {interval}s)")
        
        while True:
            try:
                # Générer un nouveau passager occasionnellement
                if random.random() < 0.3:  # 30% de chance
                    passenger_data = await self.generate_passenger()
                    try:
                        await self.execute_query("""
                            INSERT INTO passengers (first_name, last_name, email, phone, 
                                                  nationality, date_of_birth, preferred_destinations, 
                                                  travel_class_preference)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        """, *passenger_data.values())
                        logger.info(f"Nouveau passager créé: {passenger_data['email']}")
                    except Exception as e:
                        # Ignorer les erreurs de doublons d'email
                        pass
                
                # Générer une réservation occasionnellement
                if random.random() < 0.4:  # 40% de chance
                    await self.generate_booking()
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Erreur dans la génération de passagers: {e}")
                await asyncio.sleep(interval)


class ServiceDataGenerator(BaseDataGenerator):
    """Générateur de mise à jour des services"""
    
    async def update_service_usage(self):
        """Mettre à jour l'utilisation des services"""
        services = await self.fetch_query("SELECT id, capacity, current_usage FROM services")
        
        for service in services:
            service_id = service['id']
            capacity = service['capacity'] or 100
            current_usage = service['current_usage']
            
            # Variation réaliste de l'utilisation
            change = random.randint(-10, 15)
            new_usage = max(0, min(capacity, current_usage + change))
            
            if new_usage != current_usage:
                await self.execute_query("""
                    UPDATE services SET current_usage = $1 WHERE id = $2
                """, new_usage, service_id)
    
    async def run_continuous_updates(self, interval: int):
        """Mise à jour continue des services"""
        logger.info(f"Démarrage des mises à jour de services (interval: {interval}s)")
        
        while True:
            try:
                await self.update_service_usage()
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Erreur dans la mise à jour des services: {e}")
                await asyncio.sleep(interval)


class EventGenerator(BaseDataGenerator):
    """Générateur d'événements temps réel"""
    
    def __init__(self, database_url: str):
        super().__init__(database_url)
        self.event_types = [
            "BOARDING_STARTED", "GATE_CHANGE", "DELAY_ANNOUNCED", 
            "CHECK_IN_OPENED", "BAGGAGE_LOADED", "SECURITY_ALERT",
            "WEATHER_DELAY", "TECHNICAL_ISSUE"
        ]
    
    async def generate_random_event(self):
        """Générer un événement aléatoire"""
        # Récupérer des vols actifs
        flights = await self.fetch_query("""
            SELECT id, flight_number FROM flights 
            WHERE status IN ('SCHEDULED', 'BOARDING', 'DELAYED')
            ORDER BY RANDOM() LIMIT 10
        """)
        
        if flights:
            flight = random.choice(flights)
            event_type = random.choice(self.event_types)
            
            descriptions = {
                "BOARDING_STARTED": f"Embarquement commencé pour le vol {flight['flight_number']}",
                "GATE_CHANGE": f"Changement de porte pour le vol {flight['flight_number']}",
                "DELAY_ANNOUNCED": f"Retard annoncé pour le vol {flight['flight_number']}",
                "CHECK_IN_OPENED": f"Enregistrement ouvert pour le vol {flight['flight_number']}",
                "BAGGAGE_LOADED": f"Chargement des bagages pour le vol {flight['flight_number']}",
                "SECURITY_ALERT": f"Alerte sécurité - procédures renforcées",
                "WEATHER_DELAY": f"Retard météorologique pour le vol {flight['flight_number']}",
                "TECHNICAL_ISSUE": f"Problème technique signalé pour le vol {flight['flight_number']}"
            }
            
            await self.execute_query("""
                INSERT INTO events (event_type, flight_id, description)
                VALUES ($1, $2, $3)
            """, event_type, flight['id'], descriptions[event_type])
            
            logger.info(f"Événement généré: {event_type} pour vol {flight['flight_number']}")
    
    async def run_continuous_generation(self, interval: int):
        """Génération continue d'événements"""
        logger.info(f"Démarrage de la génération d'événements (interval: {interval}s)")
        
        while True:
            try:
                if random.random() < 0.7:  # 70% de chance
                    await self.generate_random_event()
                
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Erreur dans la génération d'événements: {e}")
                await asyncio.sleep(interval)
