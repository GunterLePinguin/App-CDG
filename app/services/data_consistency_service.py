"""
Service de consolidation des données pour assurer la cohérence
entre la génération, l'API et l'affichage dashboard
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

class DataConsistencyService:
    """Service pour assurer la cohérence des données dans tout le système"""
    
    @staticmethod
    def normalize_flight_data(db: Session) -> Dict[str, Any]:
        """Normaliser les données de vols avec structure cohérente"""
        try:
            flights_query = text("""
                SELECT 
                    id,
                    flight_number,
                    airline,
                    departure_time,
                    arrival_time,
                    destination,
                    origin,
                    gate,
                    terminal,
                    status,
                    capacity,
                    occupied_seats,
                    ROUND(CAST(occupied_seats AS FLOAT) / NULLIF(capacity, 0) * 100, 1) as occupation_rate,
                    aircraft_type,
                    created_at,
                    updated_at
                FROM flights 
                ORDER BY departure_time ASC
            """)
            
            result = db.execute(flights_query).fetchall()
            
            flights = []
            for row in result:
                flight = {
                    'id': row[0],
                    'flight_number': row[1],
                    'airline': row[2],
                    'departure_time': row[3].isoformat() if row[3] else None,
                    'arrival_time': row[4].isoformat() if row[4] else None,
                    'destination': row[5],
                    'origin': row[6],
                    'gate': row[7],
                    'terminal': row[8],
                    'status': row[9],
                    'capacity': row[10],
                    'occupied_seats': row[11],
                    'occupation_rate': float(row[12]) if row[12] else 0.0,
                    'aircraft_type': row[13],
                    'created_at': row[14].isoformat() if row[14] else None,
                    'updated_at': row[15].isoformat() if row[15] else None
                }
                flights.append(flight)
            
            return {
                'flights': flights,
                'total_count': len(flights),
                'status_summary': DataConsistencyService._get_status_summary(flights)
            }
            
        except Exception as e:
            logger.error(f"Erreur normalisation vols: {e}")
            return {'flights': [], 'total_count': 0, 'status_summary': {}}
    
    @staticmethod
    def normalize_passenger_data(db: Session, limit: int = 100) -> Dict[str, Any]:
        """Normaliser les données passagers avec structure cohérente"""
        try:
            passengers_query = text("""
                SELECT 
                    id,
                    first_name,
                    last_name,
                    email,
                    phone,
                    date_of_birth,
                    nationality,
                    created_at
                FROM passengers 
                ORDER BY created_at DESC
                LIMIT :limit
            """)
            
            result = db.execute(passengers_query, {'limit': limit}).fetchall()
            
            passengers = []
            for row in result:
                passenger = {
                    'id': row[0],
                    'first_name': row[1],
                    'last_name': row[2],
                    'email': row[3],
                    'phone': row[4],
                    'date_of_birth': row[5].isoformat() if row[5] else None,
                    'nationality': row[6],
                    'created_at': row[7].isoformat() if row[7] else None,
                    'full_name': f"{row[1]} {row[2]}"
                }
                passengers.append(passenger)
            
            return {
                'passengers': passengers,
                'total_count': len(passengers),
                'nationality_stats': DataConsistencyService._get_nationality_stats(passengers)
            }
            
        except Exception as e:
            logger.error(f"Erreur normalisation passagers: {e}")
            return {'passengers': [], 'total_count': 0, 'nationality_stats': {}}
    
    @staticmethod
    def normalize_service_data(db: Session) -> Dict[str, Any]:
        """Normaliser les données services avec structure cohérente"""
        try:
            services_query = text("""
                SELECT 
                    id,
                    name,
                    type,
                    location,
                    terminal,
                    capacity,
                    current_usage,
                    ROUND(CAST(current_usage AS FLOAT) / NULLIF(capacity, 0) * 100, 1) as usage_rate,
                    rating,
                    price_range,
                    created_at,
                    updated_at
                FROM services 
                ORDER BY terminal, type, name
            """)
            
            result = db.execute(services_query).fetchall()
            
            services = []
            for row in result:
                service = {
                    'id': row[0],
                    'name': row[1],
                    'type': row[2],
                    'location': row[3],
                    'terminal': row[4],
                    'capacity': row[5],
                    'current_usage': row[6],
                    'usage_rate': float(row[7]) if row[7] else 0.0,
                    'rating': float(row[8]) if row[8] else 0.0,
                    'price_range': row[9],
                    'status': DataConsistencyService._get_service_status(row[7], row[5]),
                    'created_at': row[10].isoformat() if row[10] else None,
                    'updated_at': row[11].isoformat() if row[11] else None
                }
                services.append(service)
            
            return {
                'services': services,
                'total_count': len(services),
                'type_distribution': DataConsistencyService._get_service_type_distribution(services),
                'high_usage_services': [s for s in services if s['usage_rate'] >= 80],
                'terminal_distribution': DataConsistencyService._get_terminal_distribution(services)
            }
            
        except Exception as e:
            logger.error(f"Erreur normalisation services: {e}")
            return {'services': [], 'total_count': 0, 'type_distribution': {}, 'high_usage_services': [], 'terminal_distribution': {}}
    
    @staticmethod
    def normalize_event_data(db: Session, limit: int = 50) -> Dict[str, Any]:
        """Normaliser les données événements avec structure cohérente"""
        try:
            events_query = text("""
                SELECT 
                    e.id,
                    e.event_type,
                    e.description,
                    e.timestamp,
                    e.flight_id,
                    f.flight_number,
                    f.destination,
                    f.status as flight_status
                FROM events e
                LEFT JOIN flights f ON e.flight_id = f.id
                ORDER BY e.timestamp DESC
                LIMIT :limit
            """)
            
            result = db.execute(events_query, {'limit': limit}).fetchall()
            
            events = []
            for row in result:
                event = {
                    'id': row[0],
                    'event_type': row[1],
                    'description': row[2],
                    'timestamp': row[3].isoformat() if row[3] else None,
                    'flight_id': row[4],
                    'flight_number': row[5],
                    'destination': row[6],
                    'flight_status': row[7],
                    'formatted_time': row[3].strftime('%H:%M:%S') if row[3] else None,
                    'category': DataConsistencyService._categorize_event(row[1])
                }
                events.append(event)
            
            return {
                'events': events,
                'total_count': len(events),
                'recent_count': len([e for e in events if DataConsistencyService._is_recent_event(e['timestamp'])]),
                'event_type_stats': DataConsistencyService._get_event_type_stats(events)
            }
            
        except Exception as e:
            logger.error(f"Erreur normalisation événements: {e}")
            return {'events': [], 'total_count': 0, 'recent_count': 0, 'event_type_stats': {}}
    
    @staticmethod
    def get_consolidated_dashboard_data(db: Session) -> Dict[str, Any]:
        """Obtenir toutes les données consolidées pour le dashboard"""
        try:
            flight_data = DataConsistencyService.normalize_flight_data(db)
            passenger_data = DataConsistencyService.normalize_passenger_data(db)
            service_data = DataConsistencyService.normalize_service_data(db)
            event_data = DataConsistencyService.normalize_event_data(db)
            
            # Calcul des métriques globales
            stats = {
                'total_flights': flight_data['total_count'],
                'daily_flights': len([f for f in flight_data['flights'] 
                                    if f['departure_time'] and 
                                    datetime.fromisoformat(f['departure_time']).date() == datetime.now().date()]),
                'total_passengers': passenger_data['total_count'],
                'total_services': service_data['total_count'],
                'recent_events': event_data['recent_count'],
                'average_occupation_rate': sum(f['occupation_rate'] for f in flight_data['flights']) / max(len(flight_data['flights']), 1),
                'high_usage_services_count': len(service_data['high_usage_services']),
                'status_distribution': flight_data['status_summary'],
                'last_updated': datetime.now().isoformat()
            }
            
            return {
                'flights': flight_data,
                'passengers': passenger_data,
                'services': service_data,
                'events': event_data,
                'stats': stats,
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'data_freshness': 'real-time',
                    'api_version': '2.0.0'
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur consolidation données dashboard: {e}")
            return DataConsistencyService._get_empty_dashboard_data()
    
    # Méthodes utilitaires privées
    @staticmethod
    def _get_status_summary(flights: List[Dict]) -> Dict[str, int]:
        """Calculer la répartition des statuts"""
        status_count = {}
        for flight in flights:
            status = flight['status']
            status_count[status] = status_count.get(status, 0) + 1
        return status_count
    
    @staticmethod
    def _get_nationality_stats(passengers: List[Dict]) -> Dict[str, int]:
        """Calculer les statistiques de nationalité"""
        nationality_count = {}
        for passenger in passengers:
            nationality = passenger['nationality']
            nationality_count[nationality] = nationality_count.get(nationality, 0) + 1
        return nationality_count
    
    @staticmethod
    def _get_service_status(current_usage: int, capacity: int) -> str:
        """Déterminer le statut d'un service"""
        if capacity == 0:
            return 'INACTIVE'
        usage_rate = (current_usage / capacity) * 100
        if usage_rate >= 90:
            return 'FULL'
        elif usage_rate >= 70:
            return 'BUSY'
        elif usage_rate >= 30:
            return 'NORMAL'
        else:
            return 'LOW'
    
    @staticmethod
    def _get_service_type_distribution(services: List[Dict]) -> Dict[str, int]:
        """Calculer la distribution des types de services"""
        type_count = {}
        for service in services:
            service_type = service['type']
            type_count[service_type] = type_count.get(service_type, 0) + 1
        return type_count
    
    @staticmethod
    def _get_terminal_distribution(services: List[Dict]) -> Dict[str, int]:
        """Calculer la distribution par terminal"""
        terminal_count = {}
        for service in services:
            terminal = service['terminal']
            terminal_count[terminal] = terminal_count.get(terminal, 0) + 1
        return terminal_count
    
    @staticmethod
    def _categorize_event(event_type: str) -> str:
        """Catégoriser un événement"""
        if event_type in ['BOARDING_STARTED', 'FLIGHT_DEPARTED', 'FLIGHT_ARRIVED']:
            return 'FLIGHT_OPS'
        elif event_type in ['PASSENGER_CHECKIN', 'BAGGAGE_LOADED']:
            return 'PASSENGER'
        elif event_type in ['GATE_CLEANING', 'EQUIPMENT_CHECK', 'SYSTEM_UPDATE']:
            return 'MAINTENANCE'
        elif event_type in ['SECURITY_ALERT', 'SECURITY_PATROL']:
            return 'SECURITY'
        else:
            return 'OTHER'
    
    @staticmethod
    def _is_recent_event(timestamp_str: str) -> bool:
        """Vérifier si un événement est récent (moins de 5 minutes)"""
        if not timestamp_str:
            return False
        try:
            event_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return (datetime.now() - event_time.replace(tzinfo=None)) < timedelta(minutes=5)
        except:
            return False
    
    @staticmethod
    def _get_event_type_stats(events: List[Dict]) -> Dict[str, int]:
        """Calculer les statistiques des types d'événements"""
        type_count = {}
        for event in events:
            event_type = event['event_type']
            type_count[event_type] = type_count.get(event_type, 0) + 1
        return type_count
    
    @staticmethod
    def _get_empty_dashboard_data() -> Dict[str, Any]:
        """Retourner une structure vide en cas d'erreur"""
        return {
            'flights': {'flights': [], 'total_count': 0, 'status_summary': {}},
            'passengers': {'passengers': [], 'total_count': 0, 'nationality_stats': {}},
            'services': {'services': [], 'total_count': 0, 'type_distribution': {}, 'high_usage_services': [], 'terminal_distribution': {}},
            'events': {'events': [], 'total_count': 0, 'recent_count': 0, 'event_type_stats': {}},
            'stats': {
                'total_flights': 0, 'daily_flights': 0, 'total_passengers': 0,
                'total_services': 0, 'recent_events': 0, 'average_occupation_rate': 0,
                'high_usage_services_count': 0, 'status_distribution': {},
                'last_updated': datetime.now().isoformat()
            },
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'data_freshness': 'no-data',
                'api_version': '2.0.0'
            }
        }
