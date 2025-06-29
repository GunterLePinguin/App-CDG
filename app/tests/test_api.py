import pytest
from datetime import datetime, timedelta

def test_health_check(client):
    """Test du point de santé de l'API"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"

def test_root_endpoint(client):
    """Test de l'endpoint racine"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "CDG Airport Management System API" in data["message"]

class TestFlightEndpoints:
    """Tests pour les endpoints des vols"""
    
    def test_create_flight(self, client, sample_flight_data):
        """Test de création d'un vol"""
        response = client.post("/flights/", json=sample_flight_data)
        assert response.status_code == 200
        data = response.json()
        assert data["flight_number"] == sample_flight_data["flight_number"]
        assert data["airline"] == sample_flight_data["airline"]
        assert data["destination"] == sample_flight_data["destination"]
    
    def test_get_flights(self, client, sample_flight_data):
        """Test de récupération de la liste des vols"""
        # Créer un vol d'abord
        client.post("/flights/", json=sample_flight_data)
        
        # Récupérer la liste
        response = client.get("/flights/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_get_flight_by_id(self, client, sample_flight_data):
        """Test de récupération d'un vol par ID"""
        # Créer un vol
        create_response = client.post("/flights/", json=sample_flight_data)
        flight_id = create_response.json()["id"]
        
        # Récupérer le vol par ID
        response = client.get(f"/flights/{flight_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == flight_id
        assert data["flight_number"] == sample_flight_data["flight_number"]
    
    def test_update_flight(self, client, sample_flight_data):
        """Test de mise à jour d'un vol"""
        # Créer un vol
        create_response = client.post("/flights/", json=sample_flight_data)
        flight_id = create_response.json()["id"]
        
        # Mettre à jour
        update_data = {"status": "DELAYED", "gate": "B15"}
        response = client.put(f"/flights/{flight_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "DELAYED"
        assert data["gate"] == "B15"
    
    def test_delete_flight(self, client, sample_flight_data):
        """Test de suppression d'un vol"""
        # Créer un vol
        create_response = client.post("/flights/", json=sample_flight_data)
        flight_id = create_response.json()["id"]
        
        # Supprimer
        response = client.delete(f"/flights/{flight_id}")
        assert response.status_code == 200
        
        # Vérifier que le vol n'existe plus
        get_response = client.get(f"/flights/{flight_id}")
        assert get_response.status_code == 404
    
    def test_flight_stats(self, client, sample_flight_data):
        """Test des statistiques de vols"""
        # Créer quelques vols
        client.post("/flights/", json=sample_flight_data)
        
        response = client.get("/flights/stats/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "daily_flights" in data
        assert "status_distribution" in data
        assert "average_occupation_rate" in data

class TestPassengerEndpoints:
    """Tests pour les endpoints des passagers"""
    
    def test_create_passenger(self, client, sample_passenger_data):
        """Test de création d'un passager"""
        response = client.post("/passengers/", json=sample_passenger_data)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == sample_passenger_data["email"]
        assert data["first_name"] == sample_passenger_data["first_name"]
    
    def test_get_passengers(self, client, sample_passenger_data):
        """Test de récupération des passagers"""
        # Créer un passager
        client.post("/passengers/", json=sample_passenger_data)
        
        response = client.get("/passengers/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
    
    def test_duplicate_email_passenger(self, client, sample_passenger_data):
        """Test de création d'un passager avec email en doublon"""
        # Créer le premier passager
        client.post("/passengers/", json=sample_passenger_data)
        
        # Essayer de créer un autre avec le même email
        response = client.post("/passengers/", json=sample_passenger_data)
        assert response.status_code == 422 or response.status_code == 400  # Erreur de validation

class TestServiceEndpoints:
    """Tests pour les endpoints des services"""
    
    def test_create_service(self, client, sample_service_data):
        """Test de création d'un service"""
        response = client.post("/services/", json=sample_service_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_service_data["name"]
        assert data["type"] == sample_service_data["type"]
    
    def test_get_services(self, client, sample_service_data):
        """Test de récupération des services"""
        client.post("/services/", json=sample_service_data)
        
        response = client.get("/services/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

class TestBookingEndpoints:
    """Tests pour les endpoints des réservations"""
    
    def test_create_booking(self, client, sample_flight_data, sample_passenger_data):
        """Test de création d'une réservation"""
        # Créer un vol et un passager
        flight_response = client.post("/flights/", json=sample_flight_data)
        flight_id = flight_response.json()["id"]
        
        passenger_response = client.post("/passengers/", json=sample_passenger_data)
        passenger_id = passenger_response.json()["id"]
        
        # Créer une réservation
        booking_data = {
            "passenger_id": passenger_id,
            "flight_id": flight_id,
            "travel_class": "BUSINESS",
            "price": 1200.00
        }
        
        response = client.post("/bookings/", json=booking_data)
        assert response.status_code == 200
        data = response.json()
        assert data["passenger_id"] == passenger_id
        assert data["flight_id"] == flight_id
        assert "booking_reference" in data

class TestRecommendationEndpoints:
    """Tests pour les endpoints de recommandation"""
    
    def test_generate_recommendations(self, client, sample_flight_data, sample_passenger_data):
        """Test de génération de recommandations"""
        # Créer un passager
        passenger_response = client.post("/passengers/", json=sample_passenger_data)
        passenger_id = passenger_response.json()["id"]
        
        # Créer quelques vols
        for i in range(3):
            flight_data = sample_flight_data.copy()
            flight_data["flight_number"] = f"AF{1234 + i}"
            flight_data["destination"] = ["New York JFK", "London Heathrow", "Tokyo Narita"][i]
            client.post("/flights/", json=flight_data)
        
        # Générer des recommandations
        response = client.post(f"/recommendations/generate/{passenger_id}")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_get_recommendations(self, client, sample_passenger_data):
        """Test de récupération des recommandations"""
        # Créer un passager
        passenger_response = client.post("/passengers/", json=sample_passenger_data)
        passenger_id = passenger_response.json()["id"]
        
        response = client.get(f"/recommendations/passenger/{passenger_id}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

class TestEmailEndpoints:
    """Tests pour les endpoints d'email"""
    
    def test_generate_travel_email(self, client, sample_flight_data, sample_passenger_data):
        """Test de génération d'email de voyage"""
        # Créer un vol et un passager
        flight_response = client.post("/flights/", json=sample_flight_data)
        flight_id = flight_response.json()["id"]
        
        passenger_response = client.post("/passengers/", json=sample_passenger_data)
        passenger_id = passenger_response.json()["id"]
        
        # Générer un email
        response = client.post("/emails/generate-travel-suggestion", json={
            "passenger_id": passenger_id,
            "flight_id": flight_id,
            "email_type": "travel_suggestion"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "email_content" in data
        email_content = data["email_content"]
        assert "subject" in email_content
        assert "body" in email_content
    
    def test_generate_marketing_email(self, client, sample_passenger_data):
        """Test de génération d'email marketing"""
        # Créer un passager
        passenger_response = client.post("/passengers/", json=sample_passenger_data)
        passenger_id = passenger_response.json()["id"]
        
        response = client.post("/emails/generate-marketing", json={
            "passenger_id": passenger_id,
            "campaign_type": "destination_promotion"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "email_content" in data

class TestRealTimeEndpoints:
    """Tests pour les endpoints temps réel"""
    
    def test_realtime_flights(self, client, sample_flight_data):
        """Test des données temps réel des vols"""
        # Créer un vol
        client.post("/flights/", json=sample_flight_data)
        
        response = client.get("/realtime/flights")
        assert response.status_code == 200
        data = response.json()
        assert "upcoming_flights" in data
        assert "recent_events" in data
    
    def test_realtime_services(self, client, sample_service_data):
        """Test des données temps réel des services"""
        client.post("/services/", json=sample_service_data)
        
        response = client.get("/realtime/services")
        assert response.status_code == 200
        data = response.json()
        assert "high_usage_services" in data
        assert "inactive_services" in data
    
    def test_realtime_dashboard(self, client):
        """Test des données temps réel du dashboard"""
        response = client.get("/realtime/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "flights" in data
        assert "services" in data
        assert "stats" in data
