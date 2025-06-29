import asyncio
import os
import logging
import random
import psycopg2
from datetime import datetime, timedelta
from data_generator import FlightDataGenerator, PassengerDataGenerator, ServiceDataGenerator, EventGenerator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def generate_realtime_metrics(database_url: str):
    """Générer des métriques temps réel pour dashboard ultra-fluide"""
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    logger.info("📈 Générateur de métriques temps réel démarré")
    
    while True:
        try:
            with SessionLocal() as session:
                # Mise à jour des taux d'occupation des services de façon réaliste
                services_query = text("""
                    UPDATE services 
                    SET current_usage = LEAST(
                        capacity,
                        GREATEST(0, 
                            current_usage + (RANDOM() * 6 - 3)::INTEGER
                        )
                    )
                    WHERE capacity > 0
                """)
                session.execute(services_query)
                
                # Simulation de changements d'occupation des vols
                flights_query = text("""
                    UPDATE flights 
                    SET occupied_seats = LEAST(
                        capacity,
                        GREATEST(0,
                            occupied_seats + (RANDOM() * 4 - 2)::INTEGER
                        )
                    )
                    WHERE status IN ('SCHEDULED', 'BOARDING')
                """)
                session.execute(flights_query)
                
                session.commit()
                logger.debug("📊 Métriques temps réel mises à jour")
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de la mise à jour des métriques: {e}")            # Attendre 0.5 seconde pour un effet ultra fluide
        await asyncio.sleep(0.5)

async def simulate_boarding_process(database_url: str):
    """Simuler le processus d'embarquement réaliste"""
    logger.info("🛫 Démarrage de la simulation d'embarquement")
    
    while True:
        try:
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            # Trouver des vols qui peuvent commencer l'embarquement
            cursor.execute("""
                SELECT id, flight_number, destination 
                FROM flights 
                WHERE status = 'SCHEDULED' 
                AND departure_time BETWEEN NOW() + INTERVAL '30 minutes' AND NOW() + INTERVAL '2 hours'
                AND RANDOM() > 0.85
                LIMIT 1
            """)
            
            flight = cursor.fetchone()
            if flight:
                flight_id, flight_number, destination = flight
                
                # Changer le statut vers BOARDING
                cursor.execute("""
                    UPDATE flights 
                    SET status = 'BOARDING' 
                    WHERE id = %s
                """, (flight_id,))
                
                # Créer un événement d'embarquement
                cursor.execute("""
                    INSERT INTO events (event_type, flight_id, description, timestamp)
                    VALUES ('BOARDING_STARTED', %s, %s, NOW())
                """, (flight_id, f"Embarquement commencé pour le vol {flight_number} vers {destination}"))
                
                logger.info(f"🛫 Embarquement commencé: {flight_number} → {destination}")
            
            # Simuler fin d'embarquement (BOARDING → DEPARTED)
            cursor.execute("""
                SELECT id, flight_number, destination 
                FROM flights 
                WHERE status = 'BOARDING' 
                AND departure_time < NOW() + INTERVAL '15 minutes'
                AND RANDOM() > 0.7
                LIMIT 1
            """)
            
            departing_flight = cursor.fetchone()
            if departing_flight:
                flight_id, flight_number, destination = departing_flight
                
                cursor.execute("""
                    UPDATE flights 
                    SET status = 'DEPARTED' 
                    WHERE id = %s
                """, (flight_id,))
                
                cursor.execute("""
                    INSERT INTO events (event_type, flight_id, description, timestamp)
                    VALUES ('FLIGHT_DEPARTED', %s, %s, NOW())
                """, (flight_id, f"Vol {flight_number} parti vers {destination}"))
                
                logger.info(f"🚀 Vol parti: {flight_number} → {destination}")
            
            conn.commit()
            conn.close()
            
            await asyncio.sleep(3)  # Processus d'embarquement toutes les 3s
            
        except Exception as e:
            logger.error(f"❌ Erreur simulation embarquement: {e}")
            await asyncio.sleep(30)

async def generate_high_volume_data(database_url: str):
    """Générer un grand volume de données pour effet impressionnant"""
    logger.info("📊 Démarrage du générateur haute volume")
    
    while True:
        try:
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            # Générer plusieurs passagers en lot
            passenger_count = random.randint(3, 8)
            for _ in range(passenger_count):
                from faker import Faker
                fake = Faker('fr_FR')
                
                first_name = fake.first_name()
                last_name = fake.last_name()
                email = f"{first_name.lower()}.{last_name.lower()}@{fake.domain_name()}"
                phone = fake.phone_number()
                nationality = random.choice(['FR', 'DE', 'GB', 'ES', 'IT', 'US', 'JP', 'CA'])
                
                cursor.execute("""
                    INSERT INTO passengers (first_name, last_name, email, phone, date_of_birth, nationality)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (first_name, last_name, email, phone, fake.date_of_birth(minimum_age=18, maximum_age=80), nationality))
            
            # Générer des services variés
            service_types = ['RESTAURANT', 'SHOP', 'LOUNGE', 'SECURITY', 'CUSTOMS', 'BAGGAGE']
            if random.random() > 0.7:  # 30% de chance
                service_type = random.choice(service_types)
                terminal = random.choice(['A', 'B', 'C', 'D', 'E'])
                
                cursor.execute("""
                    INSERT INTO services (name, type, location, terminal, capacity, current_usage, rating, price_range)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    f"{service_type} {random.randint(1, 20):02d}",
                    service_type,
                    f"Terminal {terminal}",
                    terminal,
                    random.randint(50, 300),
                    random.randint(0, 50),
                    round(random.uniform(3.0, 5.0), 1),
                    random.choice(['€', '€€', '€€€'])
                ))
            
            # Générer des événements variés
            event_types = [
                'PASSENGER_CHECKIN', 'BAGGAGE_LOADED', 'CREW_BOARDING', 'CATERING_COMPLETE',
                'FUEL_COMPLETE', 'PUSHBACK_READY', 'TAXI_OUT', 'WHEELS_UP', 'CRUISE_ALTITUDE',
                'DESCENT_STARTED', 'APPROACH', 'TOUCHDOWN', 'TAXI_IN', 'GATE_ARRIVAL',
                'PASSENGERS_DISEMBARKED', 'CLEANING_STARTED', 'CLEANING_COMPLETE'
            ]
            
            for _ in range(random.randint(2, 5)):
                cursor.execute("""
                    SELECT id FROM flights ORDER BY RANDOM() LIMIT 1
                """)
                flight_result = cursor.fetchone()
                
                if flight_result:
                    flight_id = flight_result[0]
                    event_type = random.choice(event_types)
                    description = f"Événement {event_type.lower().replace('_', ' ')} - Vol {flight_id}"
                    
                    cursor.execute("""
                        INSERT INTO events (event_type, flight_id, description, timestamp)
                        VALUES (%s, %s, %s, NOW() - INTERVAL '%s seconds')
                    """, (event_type, flight_id, description, random.randint(0, 300)))
            
            conn.commit()
            conn.close()
            
            logger.info(f"📈 Lot haute volume généré: {passenger_count} passagers, événements multiples")
            await asyncio.sleep(1)  # Génération en lot toutes les 1 seconde pour maximum fluidité
            
        except Exception as e:
            logger.error(f"❌ Erreur génération haute volume: {e}")
            await asyncio.sleep(5)

async def generate_capacity_fluctuations(database_url: str):
    """Générer des fluctuations de capacité réalistes"""
    logger.info("🏪 Démarrage des fluctuations de capacité")
    
    while True:
        try:
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            # Simulation de changements de porte
            if random.random() > 0.9:  # 10% de chance
                cursor.execute("""
                    SELECT id, flight_number, gate 
                    FROM flights 
                    WHERE status = 'SCHEDULED' 
                    AND departure_time > NOW() + INTERVAL '1 hour'
                    ORDER BY RANDOM() 
                    LIMIT 1
                """)
                
                flight = cursor.fetchone()
                if flight:
                    flight_id, flight_number, old_gate = flight
                    # Générer une nouvelle porte
                    terminals = ['A', 'B', 'C', 'D', 'E']
                    new_gate = f"{random.choice(terminals)}{random.randint(1, 50):02d}"
                    
                    cursor.execute("""
                        UPDATE flights 
                        SET gate = %s 
                        WHERE id = %s
                    """, (new_gate, flight_id))
                    
                    cursor.execute("""
                        INSERT INTO events (event_type, flight_id, description, timestamp)
                        VALUES ('GATE_CHANGE', %s, %s, NOW())
                    """, (flight_id, f"Changement de porte pour le vol {flight_number}: {old_gate} → {new_gate}"))
                    
                    logger.info(f"🚪 Changement de porte: {flight_number} {old_gate} → {new_gate}")
            
            # Simulation de retards aléatoires
            if random.random() > 0.95:  # 5% de chance
                cursor.execute("""
                    SELECT id, flight_number, destination 
                    FROM flights 
                    WHERE status = 'SCHEDULED' 
                    AND departure_time > NOW()
                    ORDER BY RANDOM() 
                    LIMIT 1
                """)
                
                flight = cursor.fetchone()
                if flight:
                    flight_id, flight_number, destination = flight
                    
                    cursor.execute("""
                        UPDATE flights 
                        SET status = 'DELAYED' 
                        WHERE id = %s
                    """, (flight_id,))
                    
                    delay_reasons = [
                        "Conditions météorologiques défavorables",
                        "Problème technique mineur détecté",
                        "Retard du vol précédent",
                        "Contrôle de sécurité renforcé"
                    ]
                    
                    reason = random.choice(delay_reasons)
                    cursor.execute("""
                        INSERT INTO events (event_type, flight_id, description, timestamp)
                        VALUES ('FLIGHT_DELAYED', %s, %s, NOW())
                    """, (flight_id, f"Vol {flight_number} retardé: {reason}"))
                    
                    logger.info(f"⏰ Vol retardé: {flight_number} - {reason}")
            
            conn.commit()
            conn.close()
            
            await asyncio.sleep(3)  # Fluctuations toutes les 3 secondes
            
        except Exception as e:
            logger.error(f"❌ Erreur fluctuations capacité: {e}")
            await asyncio.sleep(20)

async def generate_ultra_fast_microdata(database_url: str):
    """Générateur de micro-données ultra-rapide pour effet de fluidité maximale"""
    logger.info("⚡ Démarrage du générateur de micro-données ultra-rapide")
    
    while True:
        try:
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            # Micro-fluctuations des services toutes les 0.5s
            cursor.execute("""
                UPDATE services 
                SET current_usage = LEAST(
                    capacity,
                    GREATEST(0, 
                        current_usage + (RANDOM() * 2 - 1)::INTEGER
                    )
                )
                WHERE capacity > 0 AND RANDOM() > 0.3
            """)
            
            # Micro-événements de maintenance
            maintenance_events = [
                'GATE_CLEANING', 'EQUIPMENT_CHECK', 'SYSTEM_UPDATE', 'STAFF_CHANGE',
                'BAGGAGE_CART_MOVEMENT', 'FUEL_TRUCK_ARRIVAL', 'CATERING_TRUCK',
                'GROUND_CREW_ACTIVITY', 'PASSENGER_ASSISTANCE', 'SECURITY_PATROL'
            ]
            
            if random.random() > 0.7:  # 30% de chance
                cursor.execute("""SELECT id FROM flights ORDER BY RANDOM() LIMIT 1""")
                flight_result = cursor.fetchone()
                
                if flight_result:
                    event_type = random.choice(maintenance_events)
                    description = f"Activité {event_type.lower().replace('_', ' ')} - Terminal {random.choice(['A', 'B', 'C', 'D', 'E'])}"
                    
                    cursor.execute("""
                        INSERT INTO events (event_type, flight_id, description, timestamp)
                        VALUES (%s, %s, %s, NOW())
                    """, (event_type, flight_result[0], description))
            
            # Simulation de mouvements de passagers temps réel
            cursor.execute("""
                UPDATE passengers 
                SET email = CONCAT(SUBSTRING(email FROM 1 FOR POSITION('@' IN email) - 1), 
                                   CASE WHEN RANDOM() > 0.99 THEN '.updated' ELSE '' END,
                                   SUBSTRING(email FROM POSITION('@' IN email)))
                WHERE RANDOM() > 0.998
            """)
            
            conn.commit()
            conn.close()
            
            await asyncio.sleep(0.5)  # Micro-données toutes les 0.5 secondes
            
        except Exception as e:
            logger.error(f"❌ Erreur micro-données: {e}")
            await asyncio.sleep(2)

async def generate_passenger_flow_simulation(database_url: str):
    """Simuler les flux de passagers en temps réel"""
    logger.info("🚶 Démarrage de la simulation de flux de passagers")
    
    while True:
        try:
            conn = psycopg2.connect(database_url)
            cursor = conn.cursor()
            
            # Simuler les arrivées de passagers par vagues
            wave_size = random.randint(5, 15)
            for i in range(wave_size):
                from faker import Faker
                fake = Faker('fr_FR')
                
                # Générer un passager avec des détails réalistes
                first_name = fake.first_name()
                last_name = fake.last_name()
                email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@{random.choice(['gmail.com', 'outlook.fr', 'orange.fr', 'free.fr'])}"
                
                # Simuler différents profils de passagers
                profile = random.choice(['BUSINESS', 'TOURIST', 'FAMILY', 'STUDENT'])
                nationality_weights = {
                    'FR': 0.4, 'DE': 0.1, 'GB': 0.1, 'ES': 0.08, 'IT': 0.08,
                    'US': 0.05, 'JP': 0.03, 'CA': 0.03, 'CN': 0.03, 'BR': 0.02
                }
                nationality = random.choices(list(nationality_weights.keys()), 
                                           weights=list(nationality_weights.values()))[0]
                
                cursor.execute("""
                    INSERT INTO passengers (first_name, last_name, email, phone, date_of_birth, nationality)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    first_name, last_name, email, fake.phone_number(),
                    fake.date_of_birth(minimum_age=16, maximum_age=85), nationality
                ))
                
                # Créer un événement de check-in
                cursor.execute("""
                    INSERT INTO events (event_type, description, timestamp)
                    VALUES ('PASSENGER_CHECKIN', %s, NOW())
                """, (f"Check-in {profile}: {first_name} {last_name} ({nationality})",))
            
            conn.commit()
            conn.close()
            
            logger.info(f"👥 Vague de {wave_size} passagers générée")
            await asyncio.sleep(random.uniform(3, 8))  # Vagues toutes les 3-8 secondes
            
        except Exception as e:
            logger.error(f"❌ Erreur simulation flux: {e}")
            await asyncio.sleep(10)

async def main():
    """Point d'entrée principal du générateur de données avec optimisations temps réel"""
    
    logger.info("🚀 Démarrage du générateur de données CDG - Mode Ultra-Fluide")
    
    # Configuration optimisée pour plus de fluidité
    database_url = os.getenv("DATABASE_URL", "postgresql://cdg_user:cdg_password@localhost:5432/airport")
    
    # Fréquences de génération ultra-rapides pour effet impressionnant (en secondes)
    flight_update_interval = int(os.getenv("FLIGHT_UPDATE_INTERVAL", "1"))    # Ultra rapide
    passenger_generation_interval = int(os.getenv("PASSENGER_GENERATION_INTERVAL", "2"))  # Ultra rapide
    service_update_interval = int(os.getenv("SERVICE_UPDATE_INTERVAL", "1"))  # Ultra rapide
    event_generation_interval = float(os.getenv("EVENT_GENERATION_INTERVAL", "1"))  # Ultra rapide pour l'effet live
    
    logger.info(f"⚡ Configuration Ultra-Fluide:")
    logger.info(f"  - Mise à jour vols: {flight_update_interval}s")
    logger.info(f"  - Génération passagers: {passenger_generation_interval}s")
    logger.info(f"  - Mise à jour services: {service_update_interval}s")
    logger.info(f"  - Génération événements: {event_generation_interval}s")
    
    # Créer les générateurs avec optimisations
    flight_generator = FlightDataGenerator(database_url)
    passenger_generator = PassengerDataGenerator(database_url)
    service_generator = ServiceDataGenerator(database_url)
    event_generator = EventGenerator(database_url)
    
    # Tâches asynchrones avec gestion d'erreur améliorée et nouvelles fonctionnalités
    tasks = [
        asyncio.create_task(flight_generator.run_continuous_updates(flight_update_interval)),
        asyncio.create_task(passenger_generator.run_continuous_generation(passenger_generation_interval)),
        asyncio.create_task(service_generator.run_continuous_updates(service_update_interval)),
        asyncio.create_task(event_generator.run_continuous_generation(event_generation_interval)),
        # Nouvelles tâches pour un effet plus impressionnant
        asyncio.create_task(generate_realtime_metrics(database_url)),
        asyncio.create_task(simulate_boarding_process(database_url)),
        asyncio.create_task(generate_capacity_fluctuations(database_url)),
        # Nouveau générateur haute volume
        asyncio.create_task(generate_high_volume_data(database_url)),
        # Nouvelles micro-données et simulation de flux
        asyncio.create_task(generate_ultra_fast_microdata(database_url)),
        asyncio.create_task(generate_passenger_flow_simulation(database_url))
    ]
    
    logger.info("✅ Tous les générateurs sont démarrés en mode Ultra-Fluide")
    
    try:
        # Attendre toutes les tâches indéfiniment
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("⏹️  Arrêt demandé par l'utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur dans le générateur principal: {e}")
        # Redémarrage automatique en cas d'erreur
        logger.info("🔄 Redémarrage automatique dans 5 secondes...")
        await asyncio.sleep(5)
        await main()

if __name__ == "__main__":
    asyncio.run(main())
