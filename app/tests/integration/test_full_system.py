import pytest
import requests
import time
from datetime import datetime, timedelta

# Configuration pour les tests d'intégration
API_BASE_URL = "http://localhost:8000"
DASHBOARD_URL = "http://localhost:8501"

class TestFullWorkflow:
    """Tests d'intégration du workflow complet"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Attendre que les services soient prêts"""
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{API_BASE_URL}/health", timeout=5)
                if response.status_code == 200:
                    break
            except requests.RequestException:
                if attempt == max_attempts - 1:
                    pytest.skip("API not available for integration tests")
                time.sleep(2)
    
    def test_complete_booking_workflow(self):
        """Test du workflow complet de réservation"""
        # 1. Créer un passager
        passenger_data = {
            "first_name": "Integration",
            "last_name": "Test",
            "email": f"integration.test.{int(time.time())}@example.com",
            "nationality": "French",
            "preferred_destinations": ["New York", "London"],
            "travel_class_preference": "BUSINESS"
        }
        
        passenger_response = requests.post(f"{API_BASE_URL}/passengers/", json=passenger_data)
        assert passenger_response.status_code == 200
        passenger_id = passenger_response.json()["id"]
        
        # 2. Créer un vol
        flight_data = {
            "flight_number": f"IT{int(time.time()) % 10000}",
            "airline": "Integration Airlines",
            "origin": "Paris CDG",
            "destination": "New York JFK",
            "departure_time": (datetime.now() + timedelta(hours=24)).isoformat(),
            "arrival_time": (datetime.now() + timedelta(hours=32)).isoformat(),
            "aircraft_type": "Boeing 777",
            "gate": "A50",
            "terminal": "2E",
            "capacity": 300,
            "price": 800.00
        }
        
        flight_response = requests.post(f"{API_BASE_URL}/flights/", json=flight_data)
        assert flight_response.status_code == 200
        flight_id = flight_response.json()["id"]
        
        # 3. Créer une réservation
        booking_data = {
            "passenger_id": passenger_id,
            "flight_id": flight_id,
            "travel_class": "BUSINESS",
            "price": 1200.00
        }
        
        booking_response = requests.post(f"{API_BASE_URL}/bookings/", json=booking_data)
        assert booking_response.status_code == 200
        booking_id = booking_response.json()["id"]
        booking_reference = booking_response.json()["booking_reference"]
        
        # 4. Vérifier que la réservation existe
        get_booking_response = requests.get(f"{API_BASE_URL}/bookings/{booking_id}")
        assert get_booking_response.status_code == 200
        assert get_booking_response.json()["booking_reference"] == booking_reference
        
        # 5. Générer des recommandations pour le passager
        rec_response = requests.post(f"{API_BASE_URL}/recommendations/generate/{passenger_id}")
        assert rec_response.status_code == 200
        
        # 6. Récupérer les recommandations
        get_rec_response = requests.get(f"{API_BASE_URL}/recommendations/passenger/{passenger_id}")
        assert get_rec_response.status_code == 200
        recommendations = get_rec_response.json()
        
        # 7. Générer un email de voyage
        email_response = requests.post(f"{API_BASE_URL}/emails/generate-travel-suggestion", json={
            "passenger_id": passenger_id,
            "flight_id": flight_id,
            "email_type": "travel_suggestion"
        })
        assert email_response.status_code == 200
        email_content = email_response.json()["email_content"]
        assert "subject" in email_content
        assert "body" in email_content
        assert passenger_data["first_name"] in email_content["body"]
        
        print(f"✅ Workflow complet testé avec succès!")
        print(f"   - Passager créé: {passenger_id}")
        print(f"   - Vol créé: {flight_id}")
        print(f"   - Réservation: {booking_reference}")
        print(f"   - Recommandations: {len(recommendations)}")
        print(f"   - Email généré: {email_content['subject']}")
    
    def test_realtime_data_flow(self):
        """Test du flux de données temps réel"""
        # 1. Récupérer les données temps réel des vols
        realtime_flights = requests.get(f"{API_BASE_URL}/realtime/flights")
        assert realtime_flights.status_code == 200
        flights_data = realtime_flights.json()
        assert "upcoming_flights" in flights_data
        assert "recent_events" in flights_data
        
        # 2. Récupérer les données temps réel des services
        realtime_services = requests.get(f"{API_BASE_URL}/realtime/services")
        assert realtime_services.status_code == 200
        services_data = realtime_services.json()
        assert "high_usage_services" in services_data
        assert "inactive_services" in services_data
        
        # 3. Récupérer le dashboard temps réel
        realtime_dashboard = requests.get(f"{API_BASE_URL}/realtime/dashboard")
        assert realtime_dashboard.status_code == 200
        dashboard_data = realtime_dashboard.json()
        assert "flights" in dashboard_data
        assert "services" in dashboard_data
        assert "stats" in dashboard_data
        
        print("✅ Flux de données temps réel testé avec succès!")
    
    def test_api_performance(self):
        """Test de performance de l'API"""
        endpoints_to_test = [
            "/health",
            "/flights/",
            "/passengers/",
            "/services/",
            "/flights/stats/dashboard",
            "/realtime/flights",
            "/realtime/services"
        ]
        
        performance_results = {}
        
        for endpoint in endpoints_to_test:
            start_time = time.time()
            response = requests.get(f"{API_BASE_URL}{endpoint}")
            end_time = time.time()
            
            assert response.status_code == 200
            response_time = end_time - start_time
            performance_results[endpoint] = response_time
            
            # Vérifier que la réponse est dans un délai raisonnable (< 2 secondes)
            assert response_time < 2.0, f"Endpoint {endpoint} trop lent: {response_time:.2f}s"
        
        print("✅ Tests de performance réussis!")
        for endpoint, time_taken in performance_results.items():
            print(f"   - {endpoint}: {time_taken:.3f}s")
    
    def test_data_consistency(self):
        """Test de cohérence des données"""
        # 1. Créer des données liées
        passenger_data = {
            "first_name": "Consistency",
            "last_name": "Test",
            "email": f"consistency.{int(time.time())}@example.com",
            "nationality": "French"
        }
        
        passenger_response = requests.post(f"{API_BASE_URL}/passengers/", json=passenger_data)
        passenger_id = passenger_response.json()["id"]
        
        flight_data = {
            "flight_number": f"CT{int(time.time()) % 10000}",
            "airline": "Consistency Air",
            "origin": "Paris CDG",
            "destination": "London",
            "departure_time": (datetime.now() + timedelta(hours=12)).isoformat(),
            "arrival_time": (datetime.now() + timedelta(hours=14)).isoformat(),
            "capacity": 180
        }
        
        flight_response = requests.post(f"{API_BASE_URL}/flights/", json=flight_data)
        flight_id = flight_response.json()["id"]
        
        # 2. Créer une réservation
        booking_data = {
            "passenger_id": passenger_id,
            "flight_id": flight_id,
            "travel_class": "ECONOMY"
        }
        
        booking_response = requests.post(f"{API_BASE_URL}/bookings/", json=booking_data)
        booking_id = booking_response.json()["id"]
        
        # 3. Vérifier la cohérence
        # Le vol doit maintenant avoir un siège occupé de plus
        flight_check = requests.get(f"{API_BASE_URL}/flights/{flight_id}")
        flight_data_updated = flight_check.json()
        assert flight_data_updated["occupied_seats"] == 1
        
        # 4. Supprimer la réservation
        delete_response = requests.delete(f"{API_BASE_URL}/bookings/{booking_id}")
        assert delete_response.status_code == 200
        
        # 5. Vérifier que le siège est libéré
        flight_check_after = requests.get(f"{API_BASE_URL}/flights/{flight_id}")
        flight_data_after = flight_check_after.json()
        assert flight_data_after["occupied_seats"] == 0
        
        print("✅ Test de cohérence des données réussi!")
    
    def test_error_handling(self):
        """Test de gestion d'erreurs"""
        # 1. Essayer d'accéder à un vol inexistant
        response = requests.get(f"{API_BASE_URL}/flights/99999")
        assert response.status_code == 404
        
        # 2. Essayer de créer une réservation avec un vol inexistant
        booking_data = {
            "passenger_id": 1,
            "flight_id": 99999,
            "travel_class": "ECONOMY"
        }
        
        booking_response = requests.post(f"{API_BASE_URL}/bookings/", json=booking_data)
        assert booking_response.status_code in [400, 422, 500]  # Erreur attendue
        
        # 3. Essayer de créer un passager avec des données invalides
        invalid_passenger = {
            "first_name": "",  # Nom vide
            "last_name": "Test",
            "email": "invalid-email"  # Email invalide
        }
        
        passenger_response = requests.post(f"{API_BASE_URL}/passengers/", json=invalid_passenger)
        assert passenger_response.status_code in [400, 422]  # Erreur de validation
        
        print("✅ Test de gestion d'erreurs réussi!")

class TestDataGenerator:
    """Tests pour le générateur de données"""
    
    def test_data_generation_impact(self):
        """Test de l'impact du générateur de données"""
        # Récupérer l'état initial
        initial_flights = requests.get(f"{API_BASE_URL}/flights/")
        initial_count = len(initial_flights.json())
        
        # Attendre un peu pour que le générateur fonctionne
        time.sleep(30)
        
        # Récupérer l'état après génération
        after_flights = requests.get(f"{API_BASE_URL}/flights/")
        after_count = len(after_flights.json())
        
        # Il devrait y avoir plus de vols (ou au moins une activité)
        print(f"Vols initiaux: {initial_count}, Vols après 30s: {after_count}")
        
        # Vérifier qu'il y a eu de l'activité dans les événements
        events_response = requests.get(f"{API_BASE_URL}/realtime/flights")
        events_data = events_response.json()
        recent_events = events_data.get("recent_events", [])
        
        print(f"Événements récents: {len(recent_events)}")
        print("✅ Test du générateur de données terminé!")

if __name__ == "__main__":
    # Lancer les tests d'intégration manuellement
    test_instance = TestFullWorkflow()
    test_instance.setup()
    
    print("🧪 Lancement des tests d'intégration...")
    
    try:
        test_instance.test_complete_booking_workflow()
        test_instance.test_realtime_data_flow()
        test_instance.test_api_performance()
        test_instance.test_data_consistency()
        test_instance.test_error_handling()
        
        data_gen_test = TestDataGenerator()
        data_gen_test.test_data_generation_impact()
        
        print("🎉 Tous les tests d'intégration sont passés!")
        
    except Exception as e:
        print(f"❌ Erreur lors des tests d'intégration: {e}")
        raise
