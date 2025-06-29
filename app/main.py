from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
import logging
from datetime import datetime
import os

from database import get_db
from models import Flight, Passenger, Service, Booking, Recommendation
from schemas import (
    FlightCreate, FlightResponse, FlightUpdate,
    PassengerCreate, PassengerResponse, PassengerUpdate,
    ServiceCreate, ServiceResponse, ServiceUpdate,
    BookingCreate, BookingResponse,
    RecommendationResponse
)
from services.flight_service import FlightService
from services.passenger_service import PassengerService
from services.service_service import ServiceService
from services.booking_service import BookingService
from services.recommendation_service import AdvancedRecommendationService
from services.email_service import EmailService
from services.data_consistency_service import DataConsistencyService

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Création de l'application FastAPI
app = FastAPI(
    title="✈️ CDG Airport Management System",
    description="API complète pour la gestion des vols, passagers et services de l'aéroport Charles de Gaulle",
    version="2.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://frontend:8501", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir les fichiers statiques
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Services
flight_service = FlightService()
passenger_service = PassengerService()
service_service = ServiceService()
booking_service = BookingService()
recommendation_service = AdvancedRecommendationService()
email_service = EmailService()
data_consistency_service = DataConsistencyService()

@app.get("/")
async def root():
    """Page d'accueil web moderne"""
    static_file = os.path.join(static_dir, "index.html")
    if os.path.exists(static_file):
        return FileResponse(static_file)
    else:
        # Fallback API response
        return {
            "message": "✈️ CDG Airport Management System API",
            "version": "2.0.0",
            "description": "API complète de gestion de l'aéroport Charles de Gaulle",
            "features": [
                "🛫 Gestion des vols en temps réel",
                "👥 Gestion des passagers",
                "🏪 Services de l'aéroport", 
                "📊 Tableau de bord temps réel",
                "🤖 Recommandations intelligentes",
                "📧 Génération d'emails par IA"
            ],
            "endpoints": {
                "health": "/health",
                "documentation": "/docs",
                "flights": "/flights/",
                "passengers": "/passengers/",
                "services": "/services/",
                "realtime": "/realtime/dashboard",
                "recommendations": "/recommendations/passenger/{id}",
                "emails": "/emails/generate-travel-suggestion"
            },
            "dashboard_url": "http://localhost:8501",
            "timestamp": datetime.now(),
            "status": "🟢 Opérationnel"
        }

@app.get("/api")
async def api_info():
    """Informations de l'API en format JSON"""
    return {
        "message": "✈️ CDG Airport Management System API",
        "version": "2.0.0",
        "description": "API complète de gestion de l'aéroport Charles de Gaulle",
        "features": [
            "🛫 Gestion des vols en temps réel",
            "👥 Gestion des passagers",
            "🏪 Services de l'aéroport", 
            "📊 Tableau de bord temps réel",
            "🤖 Recommandations intelligentes",
            "📧 Génération d'emails par IA"
        ],
        "endpoints": {
            "health": "/health",
            "documentation": "/docs",
            "flights": "/flights/",
            "passengers": "/passengers/",
            "services": "/services/",
            "realtime": "/realtime/dashboard",
            "recommendations": "/recommendations/passenger/{id}",
            "emails": "/emails/generate-travel-suggestion"
        },
        "dashboard_url": "http://localhost:8501",
        "timestamp": datetime.now(),
        "status": "🟢 Opérationnel"
    }

@app.get("/health")
async def health_check():
    """Vérification de santé de l'API avec métriques détaillées"""
    try:
        # Test de connexion base de données
        db = next(get_db())
        test_query = db.execute(text("SELECT COUNT(*) FROM flights")).scalar()
        db_status = "🟢 Connectée"
        flight_count = test_query
    except Exception as e:
        db_status = f"🔴 Erreur: {str(e)}"
        flight_count = 0
    
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "database": db_status,
        "metrics": {
            "total_flights": flight_count,
            "api_version": "2.0.0",
            "uptime": "Opérationnel"
        },
        "services": {
            "api": "🟢 Actif",
            "database": db_status,
            "generator": "🟢 Actif",
            "dashboard": "🟢 Accessible sur :8501"
        }
    }

# === ENDPOINTS VOLS ===

@app.get("/flights/", response_model=List[FlightResponse])
async def get_flights(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    destination: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Récupérer la liste des vols avec filtres optionnels"""
    return await flight_service.get_flights(db, skip=skip, limit=limit, status=status, destination=destination)

@app.get("/flights/{flight_id}", response_model=FlightResponse)
async def get_flight(flight_id: int, db: Session = Depends(get_db)):
    """Récupérer un vol par son ID"""
    flight = await flight_service.get_flight(db, flight_id)
    if not flight:
        raise HTTPException(status_code=404, detail="Vol non trouvé")
    return flight

@app.post("/flights/", response_model=FlightResponse)
async def create_flight(flight: FlightCreate, db: Session = Depends(get_db)):
    """Créer un nouveau vol"""
    return await flight_service.create_flight(db, flight)

@app.put("/flights/{flight_id}", response_model=FlightResponse)
async def update_flight(flight_id: int, flight_update: FlightUpdate, db: Session = Depends(get_db)):
    """Mettre à jour un vol"""
    flight = await flight_service.update_flight(db, flight_id, flight_update)
    if not flight:
        raise HTTPException(status_code=404, detail="Vol non trouvé")
    return flight

@app.delete("/flights/{flight_id}")
async def delete_flight(flight_id: int, db: Session = Depends(get_db)):
    """Supprimer un vol"""
    success = await flight_service.delete_flight(db, flight_id)
    if not success:
        raise HTTPException(status_code=404, detail="Vol non trouvé")
    return {"message": "Vol supprimé avec succès"}

@app.get("/flights/stats/dashboard")
async def get_flight_stats(db: Session = Depends(get_db)):
    """Statistiques pour le dashboard"""
    return await flight_service.get_dashboard_stats(db)

# === ENDPOINTS PASSAGERS ===

@app.get("/passengers/", response_model=List[PassengerResponse])
async def get_passengers(
    skip: int = 0,
    limit: int = 100,
    nationality: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Récupérer la liste des passagers"""
    return await passenger_service.get_passengers(db, skip=skip, limit=limit, nationality=nationality)

@app.get("/passengers/{passenger_id}", response_model=PassengerResponse)
async def get_passenger(passenger_id: int, db: Session = Depends(get_db)):
    """Récupérer un passager par son ID"""
    passenger = await passenger_service.get_passenger(db, passenger_id)
    if not passenger:
        raise HTTPException(status_code=404, detail="Passager non trouvé")
    return passenger

@app.post("/passengers/", response_model=PassengerResponse)
async def create_passenger(passenger: PassengerCreate, db: Session = Depends(get_db)):
    """Créer un nouveau passager"""
    return await passenger_service.create_passenger(db, passenger)

@app.put("/passengers/{passenger_id}", response_model=PassengerResponse)
async def update_passenger(passenger_id: int, passenger_update: PassengerUpdate, db: Session = Depends(get_db)):
    """Mettre à jour un passager"""
    passenger = await passenger_service.update_passenger(db, passenger_id, passenger_update)
    if not passenger:
        raise HTTPException(status_code=404, detail="Passager non trouvé")
    return passenger

@app.delete("/passengers/{passenger_id}")
async def delete_passenger(passenger_id: int, db: Session = Depends(get_db)):
    """Supprimer un passager"""
    success = await passenger_service.delete_passenger(db, passenger_id)
    if not success:
        raise HTTPException(status_code=404, detail="Passager non trouvé")
    return {"message": "Passager supprimé avec succès"}

# === ENDPOINTS SERVICES ===

@app.get("/services/", response_model=List[ServiceResponse])
async def get_services(
    skip: int = 0,
    limit: int = 100,
    service_type: Optional[str] = None,
    terminal: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Récupérer la liste des services"""
    return await service_service.get_services(db, skip=skip, limit=limit, service_type=service_type, terminal=terminal)

@app.get("/services/{service_id}", response_model=ServiceResponse)
async def get_service(service_id: int, db: Session = Depends(get_db)):
    """Récupérer un service par son ID"""
    service = await service_service.get_service(db, service_id)
    if not service:
        raise HTTPException(status_code=404, detail="Service non trouvé")
    return service

@app.post("/services/", response_model=ServiceResponse)
async def create_service(service: ServiceCreate, db: Session = Depends(get_db)):
    """Créer un nouveau service"""
    return await service_service.create_service(db, service)

@app.put("/services/{service_id}", response_model=ServiceResponse)
async def update_service(service_id: int, service_update: ServiceUpdate, db: Session = Depends(get_db)):
    """Mettre à jour un service"""
    service = await service_service.update_service(db, service_id, service_update)
    if not service:
        raise HTTPException(status_code=404, detail="Service non trouvé")
    return service

@app.delete("/services/{service_id}")
async def delete_service(service_id: int, db: Session = Depends(get_db)):
    """Supprimer un service"""
    success = await service_service.delete_service(db, service_id)
    if not success:
        raise HTTPException(status_code=404, detail="Service non trouvé")
    return {"message": "Service supprimé avec succès"}

# === ENDPOINTS RÉSERVATIONS ===

@app.get("/bookings/", response_model=List[BookingResponse])
async def get_bookings(
    skip: int = 0,
    limit: int = 100,
    passenger_id: Optional[int] = None,
    flight_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Récupérer la liste des réservations"""
    return await booking_service.get_bookings(db, skip=skip, limit=limit, passenger_id=passenger_id, flight_id=flight_id)

@app.get("/bookings/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id: int, db: Session = Depends(get_db)):
    """Récupérer une réservation par son ID"""
    booking = await booking_service.get_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Réservation non trouvée")
    return booking

@app.post("/bookings/", response_model=BookingResponse)
async def create_booking(booking: BookingCreate, db: Session = Depends(get_db)):
    """Créer une nouvelle réservation"""
    return await booking_service.create_booking(db, booking)

@app.delete("/bookings/{booking_id}")
async def delete_booking(booking_id: int, db: Session = Depends(get_db)):
    """Supprimer une réservation"""
    success = await booking_service.delete_booking(db, booking_id)
    if not success:
        raise HTTPException(status_code=404, detail="Réservation non trouvée")
    return {"message": "Réservation supprimée avec succès"}

# === ENDPOINTS RECOMMANDATIONS ===

@app.get("/recommendations/passenger/{passenger_id}", response_model=List[RecommendationResponse])
async def get_recommendations_for_passenger(passenger_id: int, db: Session = Depends(get_db)):
    """Obtenir des recommandations pour un passager"""
    recommendations = await recommendation_service.get_recommendations_for_passenger(db, passenger_id)
    return recommendations

@app.post("/recommendations/generate/{passenger_id}")
async def generate_recommendations(passenger_id: int, db: Session = Depends(get_db)):
    """Générer de nouvelles recommandations pour un passager"""
    recommendations = await recommendation_service.generate_recommendations(db, passenger_id)
    return {"message": f"{len(recommendations)} recommandations générées", "recommendations": recommendations}

@app.get("/recommendations/similar-passengers/{passenger_id}")
async def get_similar_passengers(passenger_id: int, db: Session = Depends(get_db)):
    """Trouver des passagers similaires"""
    similar_passengers = await recommendation_service.find_similar_passengers(db, passenger_id)
    return similar_passengers

# === ENDPOINTS EMAIL ===

@app.post("/emails/generate-travel-suggestion")
async def generate_travel_email(
    passenger_id: int,
    flight_id: int,
    email_type: str = "travel_suggestion",
    db: Session = Depends(get_db)
):
    """Générer un email de suggestion de voyage personnalisé"""
    email_content = await email_service.generate_travel_email(db, passenger_id, flight_id, email_type)
    return {"email_content": email_content}

@app.post("/emails/generate-marketing")
async def generate_marketing_email(
    passenger_id: int,
    campaign_type: str = "destination_promotion",
    db: Session = Depends(get_db)
):
    """Générer un email marketing personnalisé"""
    email_content = await email_service.generate_marketing_email(db, passenger_id, campaign_type)
    return {"email_content": email_content}

# === ENDPOINTS TEMPS RÉEL OPTIMISÉS ===

@app.get("/realtime/flights")
async def get_realtime_flights(db: Session = Depends(get_db)):
    """Données temps réel des vols avec optimisations PostgreSQL"""
    return await flight_service.get_realtime_data(db)

@app.get("/realtime/services")
async def get_realtime_services(db: Session = Depends(get_db)):
    """Données temps réel des services avec optimisations"""
    return await service_service.get_realtime_data(db)

@app.get("/realtime/dashboard")
async def get_realtime_dashboard(db: Session = Depends(get_db)):
    """Données temps réel pour le dashboard avec requêtes optimisées"""
    return {
        "flights": await flight_service.get_realtime_data(db),
        "services": await service_service.get_realtime_data(db),
        "stats": await flight_service.get_dashboard_stats(db)
    }

@app.get("/realtime/metrics/live")
async def get_live_metrics(db: Session = Depends(get_db)):
    """Métriques ultra-rapides pour effet temps réel impressionnant"""
    try:
        # Requête optimisée PostgreSQL pour métriques instantanées
        metrics_query = text("""
            WITH flight_stats AS (
                SELECT 
                    COUNT(*) as total_flights,
                    COUNT(*) FILTER (WHERE status = 'SCHEDULED') as scheduled,
                    COUNT(*) FILTER (WHERE status = 'BOARDING') as boarding,
                    COUNT(*) FILTER (WHERE status = 'DELAYED') as delayed,
                    COUNT(*) FILTER (WHERE status = 'DEPARTED') as departed,
                    AVG(CAST(occupied_seats AS FLOAT) / NULLIF(capacity, 0) * 100) as avg_occupation
                FROM flights 
                WHERE departure_time::date = CURRENT_DATE
            ),
            service_stats AS (
                SELECT 
                    COUNT(*) as total_services,
                    COUNT(*) FILTER (WHERE current_usage >= capacity * 0.8) as high_usage,
                    AVG(CAST(current_usage AS FLOAT) / NULLIF(capacity, 0) * 100) as avg_service_usage
                FROM services 
                WHERE capacity > 0
            ),
            recent_events AS (
                SELECT COUNT(*) as event_count
                FROM events 
                WHERE timestamp >= NOW() - INTERVAL '5 minutes'
            )
            SELECT 
                f.total_flights, f.scheduled, f.boarding, f.delayed, f.departed,
                ROUND(f.avg_occupation::numeric, 1) as avg_occupation,
                s.total_services, s.high_usage, 
                ROUND(s.avg_service_usage::numeric, 1) as avg_service_usage,
                e.event_count,
                EXTRACT(epoch FROM NOW()) as timestamp
            FROM flight_stats f, service_stats s, recent_events e
        """)
        
        result = db.execute(metrics_query).fetchone()
        
        if result:
            return {
                "timestamp": datetime.now(),
                "flights": {
                    "total": result[0],
                    "scheduled": result[1],
                    "boarding": result[2],
                    "delayed": result[3],
                    "departed": result[4],
                    "avg_occupation": float(result[5] or 0)
                },
                "services": {
                    "total": result[6],
                    "high_usage": result[7],
                    "avg_usage": float(result[8] or 0)
                },
                "activity": {
                    "recent_events": result[9],
                    "system_load": min(100, (result[2] + result[3]) * 10),  # Simulated load
                    "peak_indicator": "🔴" if result[7] > 3 else "🟡" if result[7] > 1 else "🟢"
                },
                "performance": {
                    "query_time_ms": round((datetime.now().timestamp() - result[10]) * 1000, 2),
                    "status": "🟢 Optimal" if result[9] < 50 else "🟡 Busy" if result[9] < 100 else "🔴 Peak"
                }
            }
        
        return {"error": "No data available", "timestamp": datetime.now()}
        
    except Exception as e:
        logger.error(f"❌ Erreur métriques live: {e}")
        return {"error": str(e), "timestamp": datetime.now()}

@app.get("/realtime/events/stream")
async def get_event_stream(limit: int = 10, db: Session = Depends(get_db)):
    """Stream des événements récents avec optimisation"""
    try:
        # Requête optimisée pour les événements récents
        events_query = text("""
            SELECT 
                e.id,
                e.event_type,
                e.description,
                e.timestamp,
                f.flight_number,
                f.destination,
                EXTRACT(epoch FROM (NOW() - e.timestamp)) as seconds_ago
            FROM events e
            LEFT JOIN flights f ON e.flight_id = f.id
            WHERE e.timestamp >= NOW() - INTERVAL '1 hour'
            ORDER BY e.timestamp DESC
            LIMIT :limit
        """)
        
        results = db.execute(events_query, {"limit": limit}).fetchall()
        
        events = []
        for row in results:
            event_id, event_type, description, timestamp, flight_number, destination, seconds_ago = row
            
            # Formatage avancé des événements
            event_emoji = {
                "BOARDING_STARTED": "🛫",
                "GATE_CHANGE": "🚪", 
                "FLIGHT_DELAYED": "⏰",
                "WEATHER_DELAY": "🌧️",
                "TECHNICAL_ISSUE": "🔧",
                "SECURITY_ALERT": "🚨",
                "FLIGHT_DEPARTED": "🚀"
            }.get(event_type, "📢")
            
            time_ago = f"{int(seconds_ago)}s" if seconds_ago < 60 else f"{int(seconds_ago/60)}m"
            
            events.append({
                "id": event_id,
                "type": event_type,
                "emoji": event_emoji,
                "description": description,
                "flight_number": flight_number,
                "destination": destination,
                "timestamp": timestamp,
                "time_ago": time_ago,
                "urgency": "high" if event_type in ["SECURITY_ALERT", "TECHNICAL_ISSUE"] else "normal"
            })
        
        return {
            "events": events,
            "total_count": len(events),
            "last_updated": datetime.now(),
            "refresh_interval": 3  # Secondes recommandées pour refresh
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur stream événements: {e}")
        return {"error": str(e), "events": []}

@app.get("/realtime/capacity/heatmap")
async def get_capacity_heatmap(db: Session = Depends(get_db)):
    """Heatmap des capacités pour visualisation temps réel"""
    try:
        # Requête pour heatmap des terminaux
        heatmap_query = text("""
            WITH terminal_stats AS (
                SELECT 
                    COALESCE(f.terminal, 'Unknown') as terminal,
                    COUNT(*) as flight_count,
                    AVG(CAST(f.occupied_seats AS FLOAT) / NULLIF(f.capacity, 0)) as avg_occupancy,
                    COUNT(*) FILTER (WHERE f.status = 'BOARDING') as boarding_count
                FROM flights f
                WHERE f.departure_time::date = CURRENT_DATE
                AND f.terminal IS NOT NULL
                GROUP BY f.terminal
            ),
            service_stats AS (
                SELECT 
                    COALESCE(s.terminal, 'Unknown') as terminal,
                    COUNT(*) as service_count,
                    AVG(CAST(s.current_usage AS FLOAT) / NULLIF(s.capacity, 0)) as avg_service_usage
                FROM services s
                WHERE s.capacity > 0
                GROUP BY s.terminal
            )
            SELECT 
                t.terminal,
                t.flight_count,
                ROUND((t.avg_occupancy * 100)::numeric, 1) as flight_occupancy,
                t.boarding_count,
                COALESCE(s.service_count, 0) as service_count,
                ROUND((COALESCE(s.avg_service_usage, 0) * 100)::numeric, 1) as service_usage,
                CASE 
                    WHEN t.avg_occupancy > 0.8 OR COALESCE(s.avg_service_usage, 0) > 0.8 THEN 'high'
                    WHEN t.avg_occupancy > 0.6 OR COALESCE(s.avg_service_usage, 0) > 0.6 THEN 'medium'
                    ELSE 'low'
                END as load_level
            FROM terminal_stats t
            LEFT JOIN service_stats s ON t.terminal = s.terminal
            ORDER BY t.terminal
        """)
        
        results = db.execute(heatmap_query).fetchall()
        
        terminals = []
        for row in results:
            terminal, flight_count, flight_occ, boarding, service_count, service_usage, load_level = row
            
            terminals.append({
                "terminal": terminal,
                "flights": {
                    "count": flight_count,
                    "occupancy": float(flight_occ or 0),
                    "boarding": boarding
                },
                "services": {
                    "count": service_count,
                    "usage": float(service_usage or 0)
                },
                "load_level": load_level,
                "color": {
                    "high": "#FF5722",
                    "medium": "#FF9800", 
                    "low": "#4CAF50"
                }.get(load_level, "#9E9E9E"),
                "status_emoji": {
                    "high": "🔴",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(load_level, "⚫")
            })
        
        return {
            "terminals": terminals,
            "summary": {
                "total_terminals": len(terminals),
                "high_load": sum(1 for t in terminals if t["load_level"] == "high"),
                "medium_load": sum(1 for t in terminals if t["load_level"] == "medium"),
                "low_load": sum(1 for t in terminals if t["load_level"] == "low")
            },
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur heatmap capacité: {e}")
        return {"error": str(e), "terminals": []}

# === ENDPOINTS CONSOLIDÉS ===

@app.get("/api/consolidated/dashboard")
async def get_consolidated_dashboard_data(db: Session = Depends(get_db)):
    """Endpoint consolidé avec données cohérentes pour le dashboard"""
    try:
        consolidated_data = DataConsistencyService.get_consolidated_dashboard_data(db)
        return consolidated_data
    except Exception as e:
        logger.error(f"Erreur endpoint consolidé: {e}")
        return {"error": str(e), "timestamp": datetime.now()}

@app.get("/api/flights/normalized")
async def get_normalized_flights(db: Session = Depends(get_db)):
    """Obtenir les vols avec structure normalisée"""
    return DataConsistencyService.normalize_flight_data(db)

@app.get("/api/passengers/normalized")
async def get_normalized_passengers(limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)):
    """Obtenir les passagers avec structure normalisée"""
    return DataConsistencyService.normalize_passenger_data(db, limit)

@app.get("/api/services/normalized")
async def get_normalized_services(db: Session = Depends(get_db)):
    """Obtenir les services avec structure normalisée"""
    return DataConsistencyService.normalize_service_data(db)

@app.get("/api/events/normalized")
async def get_normalized_events(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    """Obtenir les événements avec structure normalisée"""
    return DataConsistencyService.normalize_event_data(db, limit)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
