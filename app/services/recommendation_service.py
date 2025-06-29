from sqlalchemy.orm import Session
from sqlalchemy import and_, func, not_, text
from typing import List, Dict, Any, Tuple
import logging
from datetime import datetime, timedelta
import numpy as np
from collections import Counter
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
import pickle
import os

from models import Passenger, Flight, Booking, Recommendation
from services.passenger_service import PassengerService

logger = logging.getLogger(__name__)

class AdvancedRecommendationService:
    """Service de recommandation avancé avec modèles ML et optimisations temps réel"""
    
    def __init__(self):
        self.passenger_service = PassengerService()
        self.scaler = StandardScaler()
        self.tfidf_vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
        self.model_cache = {}
        self.ml_models = {}
        self._initialize_ml_models()
        logger.info("🤖 Service de recommandation avancé avec ML initialisé")
    
    def _initialize_ml_models(self):
        """Initialiser les modèles ML pour les recommandations"""
        try:
            # Modèle de clustering des passagers
            self.ml_models['passenger_clusters'] = KMeans(n_clusters=5, random_state=42)
            
            # Modèle de prédiction de préférences
            self.ml_models['preference_predictor'] = RandomForestClassifier(
                n_estimators=100, 
                random_state=42,
                max_depth=10
            )
            
            logger.info("🧠 Modèles ML initialisés avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation ML: {e}")
    
    async def get_recommendations_for_passenger(self, db: Session, passenger_id: int) -> List[Recommendation]:
        """Récupérer les recommandations existantes pour un passager avec optimisation"""
        try:
            # Requête optimisée avec jointure et cache
            cache_key = f"recommendations_{passenger_id}"
            
            if cache_key in self.model_cache:
                cached_time, cached_data = self.model_cache[cache_key]
                if (datetime.now() - cached_time).seconds < 30:  # Cache 30 secondes
                    return cached_data
            
            recommendations = db.query(Recommendation).filter(
                Recommendation.passenger_id == passenger_id
            ).order_by(Recommendation.score.desc(), Recommendation.created_at.desc()).all()
            
            # Mettre en cache
            self.model_cache[cache_key] = (datetime.now(), recommendations)
            
            logger.info(f"📋 {len(recommendations)} recommandations trouvées pour le passager {passenger_id}")
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des recommandations: {e}")
            return []
    
    async def generate_recommendations(self, db: Session, passenger_id: int, limit: int = 5) -> List[Recommendation]:
        """Générer de nouvelles recommandations avec modèles ML avancés et temps réel"""
        try:
            passenger = await self.passenger_service.get_passenger(db, passenger_id)
            if not passenger:
                raise ValueError(f"Passager {passenger_id} non trouvé")
            
            logger.info(f"🤖 Génération de recommandations ML pour {passenger.first_name} {passenger.last_name}")
            
            # 1. Analyser le profil passager avec ML
            passenger_profile = await self._build_ml_passenger_profile(db, passenger)
            
            # 2. Clustering des passagers similaires
            similar_passengers = await self._find_similar_passengers_ml(db, passenger, passenger_profile)
            
            # 3. Recommandations basées sur le ML
            ml_recommendations = await self._generate_ml_recommendations(db, passenger, similar_passengers)
            
            # 4. Recommandations temps réel (tendances actuelles)
            realtime_recommendations = await self._generate_realtime_recommendations(db, passenger)
            
            # 5. Combiner et scorer avec algorithme hybride
            all_recommendations = ml_recommendations + realtime_recommendations
            scored_recommendations = await self._score_recommendations_hybrid(db, passenger, all_recommendations)
            
            # 6. Sauvegarder les meilleures recommandations
            saved_recommendations = []
            for rec_data in scored_recommendations[:limit]:
                recommendation = Recommendation(
                    passenger_id=passenger_id,
                    flight_id=rec_data['flight_id'],
                    recommendation_type=rec_data['type'],
                    score=rec_data['score'],
                    reason=rec_data['reason'],
                    created_at=datetime.now()
                )
                db.add(recommendation)
                saved_recommendations.append(recommendation)
            
            db.commit()
            
            logger.info(f"✅ {len(saved_recommendations)} recommandations ML générées et sauvegardées")
            return saved_recommendations
            
        except Exception as e:
            logger.error(f"❌ Erreur génération recommandations ML: {e}")
            db.rollback()
            return []
            
            logger.info(f"🎯 Génération de recommandations ML pour {passenger.first_name} {passenger.last_name}")
            
            # Supprimer les anciennes recommandations (optimisé)
            db.execute(text("DELETE FROM recommendations WHERE passenger_id = :pid"), {"pid": passenger_id})
            
            recommendations = []
            
            # 1. Recommandations basées sur ML - Collaborative Filtering
            ml_recommendations = await self._ml_collaborative_filtering(db, passenger, limit=2)
            recommendations.extend(ml_recommendations)
            
            # 2. Recommandations basées sur les préférences avec scoring avancé
            dest_recommendations = await self._advanced_destination_scoring(db, passenger, limit=2)
            recommendations.extend(dest_recommendations)
            
            # 3. Recommandations basées sur l'analyse prédictive des tendances
            trend_recommendations = await self._predictive_trend_analysis(db, passenger, limit=1)
            recommendations.extend(trend_recommendations)
            
            # Sauvegarder avec gestion d'erreur
            saved_recommendations = []
            for rec_data in recommendations[:limit]:
                try:
                    recommendation = Recommendation(**rec_data)
                    db.add(recommendation)
                    db.flush()
                    saved_recommendations.append(recommendation)
                except Exception as e:
                    logger.error(f"❌ Erreur sauvegarde recommandation: {e}")
                    continue
            
            db.commit()
            logger.info(f"✅ {len(saved_recommendations)} recommandations ML générées et sauvegardées")
            return saved_recommendations
            
        except Exception as e:
            logger.error(f"❌ Erreur génération recommandations: {e}")
            db.rollback()
            return []
    
    async def _ml_collaborative_filtering(self, db: Session, passenger: Passenger, limit: int = 2) -> List[Dict]:
        """Filtrage collaboratif basé sur l'apprentissage automatique"""
        try:
            # Construire la matrice passager-destination
            passenger_destination_matrix = await self._build_passenger_destination_matrix(db)
            
            if passenger_destination_matrix.empty:
                logger.warning("⚠️ Matrice passager-destination vide, utilisation fallback")
                return await self._fallback_recommendations(db, passenger, limit)
            
            # Calculer la similarité cosinus entre passagers
            similarity_matrix = await self._calculate_passenger_similarity(passenger_destination_matrix)
            
            # Trouver les passagers similaires
            similar_passengers = await self._find_similar_passengers(db, passenger, similarity_matrix, top_k=10)
            
            # Recommander des destinations basées sur les passagers similaires
            recommendations = []
            for similar_passenger_id, similarity_score in similar_passengers:
                similar_destinations = await self._get_passenger_popular_destinations(db, similar_passenger_id)
                
                for dest, frequency in similar_destinations[:limit]:
                    if dest not in (passenger.preferred_destinations or []):
                        # Trouver un vol vers cette destination
                        flight = await self._find_optimal_flight_to_destination(db, dest, passenger)
                        
                        if flight:
                            score = min(0.95, similarity_score * frequency * 0.1)
                            recommendations.append({
                                "passenger_id": passenger.id,
                                "flight_id": flight.id,
                                "recommendation_type": "ML_COLLABORATIVE",
                                "score": round(score, 2),
                                "reason": f"Recommandé par ML - Passagers similaires visitent {dest} (score: {score:.2f})"
                            })
                            
                            if len(recommendations) >= limit:
                                break
                
                if len(recommendations) >= limit:
                    break
            
            logger.info(f"🤖 {len(recommendations)} recommandations ML collaborative générées")
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Erreur filtrage collaboratif: {e}")
            return await self._fallback_recommendations(db, passenger, limit)
    
    async def _build_passenger_destination_matrix(self, db: Session) -> pd.DataFrame:
        """Construire la matrice passager-destination pour ML"""
        try:
            # Requête optimisée pour récupérer les données
            query = text("""
                SELECT p.id as passenger_id, f.destination, COUNT(*) as visit_count
                FROM passengers p
                JOIN bookings b ON p.id = b.passenger_id
                JOIN flights f ON b.flight_id = f.id
                WHERE f.status = 'DEPARTED'
                GROUP BY p.id, f.destination
                HAVING COUNT(*) > 0
            """)
            
            result = db.execute(query).fetchall()
            
            if not result:
                return pd.DataFrame()
            
            # Créer le DataFrame
            data = [{"passenger_id": row[0], "destination": row[1], "visit_count": row[2]} for row in result]
            df = pd.DataFrame(data)
            
            # Pivoter pour créer la matrice
            matrix = df.pivot(index='passenger_id', columns='destination', values='visit_count').fillna(0)
            
            logger.info(f"📊 Matrice ML construite: {matrix.shape[0]} passagers x {matrix.shape[1]} destinations")
            return matrix
            
        except Exception as e:
            logger.error(f"❌ Erreur construction matrice: {e}")
            return pd.DataFrame()
    
    async def _calculate_passenger_similarity(self, matrix: pd.DataFrame) -> np.ndarray:
        """Calculer la similarité entre passagers avec optimisation"""
        try:
            if matrix.empty:
                return np.array([])
            
            # Normaliser les données
            normalized_matrix = self.scaler.fit_transform(matrix.values)
            
            # Calculer la similarité cosinus
            similarity_matrix = cosine_similarity(normalized_matrix)
            
            logger.info(f"🔗 Matrice de similarité calculée: {similarity_matrix.shape}")
            return similarity_matrix
            
        except Exception as e:
            logger.error(f"❌ Erreur calcul similarité: {e}")
            return np.array([])
    
    async def _advanced_destination_scoring(self, db: Session, passenger: Passenger, limit: int = 2) -> List[Dict]:
        """Scoring avancé des destinations avec facteurs multiples"""
        try:
            recommendations = []
            preferred_destinations = passenger.preferred_destinations or []
            
            # Scoring multi-critères pour chaque destination préférée
            for destination in preferred_destinations:
                # Facteurs de scoring
                seasonal_factor = await self._calculate_seasonal_factor(destination)
                price_factor = await self._calculate_price_attractiveness(db, destination)
                availability_factor = await self._calculate_availability_factor(db, destination)
                popularity_factor = await self._calculate_destination_popularity(db, destination)
                
                # Score composite
                composite_score = (
                    seasonal_factor * 0.3 +
                    price_factor * 0.25 +
                    availability_factor * 0.25 +
                    popularity_factor * 0.2
                )
                
                # Trouver le meilleur vol
                flight = await self._find_optimal_flight_to_destination(db, destination, passenger)
                
                if flight and composite_score > 0.6:  # Seuil de qualité
                    recommendations.append({
                        "passenger_id": passenger.id,
                        "flight_id": flight.id,
                        "recommendation_type": "ADVANCED_SCORING",
                        "score": round(composite_score, 2),
                        "reason": f"Destination optimale {destination} - Score composite: {composite_score:.2f} (saisonnier: {seasonal_factor:.2f}, prix: {price_factor:.2f})"
                    })
                    
                    if len(recommendations) >= limit:
                        break
            
            logger.info(f"📈 {len(recommendations)} recommandations avec scoring avancé générées")
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Erreur scoring avancé: {e}")
            return []
    
    async def _predictive_trend_analysis(self, db: Session, passenger: Passenger, limit: int = 1) -> List[Dict]:
        """Analyse prédictive des tendances de voyage"""
        try:
            # Analyser les tendances récentes (30 derniers jours)
            trend_query = text("""
                SELECT f.destination, COUNT(*) as booking_count,
                       AVG(EXTRACT(epoch FROM (f.departure_time - b.booking_date))/86400) as avg_booking_lead_time
                FROM bookings b
                JOIN flights f ON b.flight_id = f.id
                WHERE b.booking_date >= NOW() - INTERVAL '30 days'
                AND f.status IN ('SCHEDULED', 'DEPARTED')
                GROUP BY f.destination
                HAVING COUNT(*) >= 3
                ORDER BY booking_count DESC, avg_booking_lead_time ASC
                LIMIT 10
            """)
            
            trends = db.execute(trend_query).fetchall()
            
            recommendations = []
            for trend in trends:
                destination, booking_count, avg_lead_time = trend
                
                # Calculer le score de tendance
                trend_score = min(0.9, (booking_count / 20) * 0.8 + (1.0 / max(1, avg_lead_time)) * 0.2)
                
                # Éviter les destinations déjà visitées
                if destination not in (passenger.preferred_destinations or []):
                    flight = await self._find_optimal_flight_to_destination(db, destination, passenger)
                    
                    if flight and trend_score > 0.5:
                        recommendations.append({
                            "passenger_id": passenger.id,
                            "flight_id": flight.id,
                            "recommendation_type": "PREDICTIVE_TREND",
                            "score": round(trend_score, 2),
                            "reason": f"Tendance émergente: {destination} - {booking_count} réservations récentes, score: {trend_score:.2f}"
                        })
                        
                        if len(recommendations) >= limit:
                            break
            
            logger.info(f"📊 {len(recommendations)} recommandations prédictives générées")
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse prédictive: {e}")
            return []
            recommendation = Recommendation(**rec_data)
            db.add(recommendation)
        
        db.commit()
        
        # Récupérer les recommandations créées
        created_recommendations = await self.get_recommendations_for_passenger(db, passenger_id)
        
        logger.info(f"Généré {len(created_recommendations)} recommandations pour le passager {passenger_id}")
        return created_recommendations
    
    async def find_similar_passengers(self, db: Session, passenger_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Trouver des passagers similaires basés sur les préférences et l'historique"""
        passenger = await self.passenger_service.get_passenger(db, passenger_id)
        if not passenger:
            return []
        
        # Récupérer l'historique de voyage du passager
        passenger_flights = db.query(Flight.destination).join(Booking).filter(
            Booking.passenger_id == passenger_id
        ).all()
        passenger_destinations = set(dest[0] for dest in passenger_flights)
        
        # Trouver des passagers avec des destinations similaires
        similar_passengers = []
        
        all_passengers = db.query(Passenger).filter(Passenger.id != passenger_id).all()
        
        for other_passenger in all_passengers:
            similarity_score = await self._calculate_passenger_similarity(
                db, passenger, other_passenger, passenger_destinations
            )
            
            if similarity_score > 0.3:  # Seuil de similarité
                similar_passengers.append({
                    "passenger": other_passenger,
                    "similarity_score": similarity_score
                })
        
        # Trier par score de similarité
        similar_passengers.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return similar_passengers[:limit]
    
    async def _recommend_by_preferred_destinations(self, db: Session, passenger: Passenger, limit: int) -> List[Dict[str, Any]]:
        """Recommandations basées on les destinations préférées"""
        recommendations = []
        
        if not passenger.preferred_destinations:
            return recommendations
        
        # Trouver des vols vers les destinations préférées
        future_flights = db.query(Flight).filter(
            and_(
                Flight.destination.in_(passenger.preferred_destinations),
                Flight.departure_time > datetime.now(),
                # Exclure les vols déjà réservés
                not_(Flight.id.in_(
                    db.query(Booking.flight_id).filter(Booking.passenger_id == passenger.id)
                ))
            )
        ).order_by(Flight.departure_time).limit(limit).all()
        
        for flight in future_flights:
            recommendations.append({
                "passenger_id": passenger.id,
                "flight_id": flight.id,
                "recommendation_type": "PREFERRED_DESTINATION",
                "score": 0.9,
                "reason": f"Destination préférée: {flight.destination}"
            })
        
        return recommendations
    
    async def _recommend_by_similar_passengers(self, db: Session, passenger: Passenger, limit: int) -> List[Dict[str, Any]]:
        """Recommandations basées sur des passagers similaires"""
        similar_passengers = await self.find_similar_passengers(db, passenger.id, limit=5)
        
        if not similar_passengers:
            return []
        
        # Récupérer les destinations populaires parmi les passagers similaires
        popular_destinations = Counter()
        
        for sim_passenger in similar_passengers:
            other_flights = db.query(Flight.destination).join(Booking).filter(
                Booking.passenger_id == sim_passenger["passenger"].id
            ).all()
            
            for dest in other_flights:
                popular_destinations[dest[0]] += sim_passenger["similarity_score"]
        
        # Trouver des vols vers ces destinations populaires
        recommendations = []
        
        for destination, popularity in popular_destinations.most_common(limit):
            # Vérifier si le passager n'a pas déjà visité cette destination
            already_visited = db.query(Booking).join(Flight).filter(
                and_(
                    Booking.passenger_id == passenger.id,
                    Flight.destination == destination
                )
            ).first()
            
            if not already_visited:
                future_flight = db.query(Flight).filter(
                    and_(
                        Flight.destination == destination,
                        Flight.departure_time > datetime.now()
                    )
                ).first()
                
                if future_flight:
                    recommendations.append({
                        "passenger_id": passenger.id,
                        "flight_id": future_flight.id,
                        "recommendation_type": "SIMILAR_PASSENGERS",
                        "score": min(0.8, popularity / 10),
                        "reason": f"Destination populaire parmi les passagers similaires: {destination}"
                    })
        
        return recommendations
    
    async def _recommend_by_trends(self, db: Session, passenger: Passenger, limit: int) -> List[Dict[str, Any]]:
        """Recommandations basées sur les tendances et la saisonnalité"""
        # Trouver les destinations en tendance (beaucoup de réservations récentes)
        recent_bookings = db.query(
            Flight.destination, func.count(Booking.id).label('booking_count')
        ).join(Booking).filter(
            Booking.booking_date >= datetime.now() - timedelta(days=30)
        ).group_by(Flight.destination).order_by(
            func.count(Booking.id).desc()
        ).limit(limit).all()
        
        recommendations = []
        
        for destination, booking_count in recent_bookings:
            # Vérifier si le passager n'a pas déjà visité
            already_visited = db.query(Booking).join(Flight).filter(
                and_(
                    Booking.passenger_id == passenger.id,
                    Flight.destination == destination
                )
            ).first()
            
            if not already_visited:
                future_flight = db.query(Flight).filter(
                    and_(
                        Flight.destination == destination,
                        Flight.departure_time > datetime.now()
                    )
                ).first()
                
                if future_flight:
                    recommendations.append({
                        "passenger_id": passenger.id,
                        "flight_id": future_flight.id,
                        "recommendation_type": "TRENDING_DESTINATION",
                        "score": min(0.7, booking_count / 50),
                        "reason": f"Destination tendance avec {booking_count} réservations récentes: {destination}"
                    })
        
        return recommendations
    
    async def _calculate_passenger_similarity(
        self, 
        db: Session, 
        passenger1: Passenger, 
        passenger2: Passenger, 
        passenger1_destinations: set
    ) -> float:
        """Calculer la similarité entre deux passagers"""
        score = 0.0
        
        # Similarité de nationalité
        if passenger1.nationality == passenger2.nationality:
            score += 0.2
        
        # Similarité de classe de voyage préférée
        if passenger1.travel_class_preference == passenger2.travel_class_preference:
            score += 0.2
        
        # Similarité des destinations préférées
        if passenger1.preferred_destinations and passenger2.preferred_destinations:
            common_prefs = set(passenger1.preferred_destinations) & set(passenger2.preferred_destinations)
            if common_prefs:
                score += 0.3 * (len(common_prefs) / max(len(passenger1.preferred_destinations), len(passenger2.preferred_destinations)))
        
        # Similarité des destinations visitées
        passenger2_flights = db.query(Flight.destination).join(Booking).filter(
            Booking.passenger_id == passenger2.id
        ).all()
        passenger2_destinations = set(dest[0] for dest in passenger2_flights)
        
        if passenger1_destinations and passenger2_destinations:
            common_visited = passenger1_destinations & passenger2_destinations
            if common_visited:
                score += 0.3 * (len(common_visited) / len(passenger1_destinations | passenger2_destinations))
        
        return min(1.0, score)
    
    # === MÉTHODES DE SUPPORT POUR ML ===
    
    async def _find_similar_passengers(self, db: Session, passenger: Passenger, similarity_matrix: np.ndarray, top_k: int = 5) -> List[Tuple[int, float]]:
        """Trouver les passagers les plus similaires"""
        try:
            # Obtenir l'index du passager dans la matrice
            passenger_ids = db.execute(text("SELECT DISTINCT id FROM passengers ORDER BY id")).fetchall()
            passenger_id_list = [pid[0] for pid in passenger_ids]
            
            if passenger.id not in passenger_id_list:
                return []
            
            passenger_index = passenger_id_list.index(passenger.id)
            
            # Obtenir les scores de similarité
            similarities = similarity_matrix[passenger_index]
            
            # Trier et retourner les top K (excluant le passager lui-même)
            similar_indices = np.argsort(similarities)[::-1][1:top_k+1]
            
            similar_passengers = []
            for idx in similar_indices:
                if similarities[idx] > 0.1:  # Seuil de similarité minimum
                    similar_passenger_id = passenger_id_list[idx]
                    similar_passengers.append((similar_passenger_id, similarities[idx]))
            
            return similar_passengers
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche passagers similaires: {e}")
            return []
    
    async def _get_passenger_popular_destinations(self, db: Session, passenger_id: int) -> List[Tuple[str, int]]:
        """Obtenir les destinations populaires d'un passager"""
        try:
            query = text("""
                SELECT f.destination, COUNT(*) as frequency
                FROM bookings b
                JOIN flights f ON b.flight_id = f.id
                WHERE b.passenger_id = :pid
                AND f.status = 'DEPARTED'
                GROUP BY f.destination
                ORDER BY frequency DESC
                LIMIT 5
            """)
            
            result = db.execute(query, {"pid": passenger_id}).fetchall()
            return [(row[0], row[1]) for row in result]
            
        except Exception as e:
            logger.error(f"❌ Erreur destinations populaires: {e}")
            return []
    
    async def _find_optimal_flight_to_destination(self, db: Session, destination: str, passenger: Passenger) -> Flight:
        """Trouver le vol optimal vers une destination"""
        try:
            # Critères de sélection: futur, disponible, classe préférée
            preferred_class = passenger.travel_class_preference or "ECONOMY"
            
            query = text("""
                SELECT f.* FROM flights f
                WHERE f.destination = :dest
                AND f.departure_time > NOW()
                AND f.status = 'SCHEDULED'
                AND f.occupied_seats < f.capacity
                ORDER BY 
                    CASE WHEN :pref_class = 'BUSINESS' AND f.price > 800 THEN 1 ELSE 2 END,
                    (f.capacity - f.occupied_seats) DESC,
                    f.departure_time ASC
                LIMIT 1
            """)
            
            result = db.execute(query, {"dest": destination, "pref_class": preferred_class}).fetchone()
            
            if result:
                # Convertir le résultat en objet Flight
                return db.query(Flight).filter(Flight.id == result[0]).first()
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche vol optimal: {e}")
            return None
    
    async def _calculate_seasonal_factor(self, destination: str) -> float:
        """Calculer le facteur saisonnier pour une destination"""
        try:
            current_month = datetime.now().month
            
            # Facteurs saisonniers par destination (simulation réaliste)
            seasonal_factors = {
                "Dubai": [0.9, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.4, 0.6, 0.8, 0.9, 1.0],
                "London": [0.6, 0.6, 0.7, 0.8, 0.9, 1.0, 1.0, 1.0, 0.9, 0.8, 0.7, 0.6],
                "New York": [0.7, 0.7, 0.8, 0.9, 1.0, 1.0, 0.9, 0.9, 1.0, 0.9, 0.8, 0.7],
                "Tokyo": [0.8, 0.8, 0.9, 1.0, 0.9, 0.8, 0.7, 0.8, 0.9, 1.0, 0.9, 0.8],
                "Sydney": [1.0, 1.0, 0.9, 0.8, 0.7, 0.6, 0.6, 0.7, 0.8, 0.9, 1.0, 1.0]
            }
            
            if destination in seasonal_factors:
                return seasonal_factors[destination][current_month - 1]
            
            return 0.8  # Facteur par défaut
            
        except Exception as e:
            logger.error(f"❌ Erreur facteur saisonnier: {e}")
            return 0.8
    
    async def _calculate_price_attractiveness(self, db: Session, destination: str) -> float:
        """Calculer l'attractivité prix pour une destination"""
        try:
            query = text("""
                SELECT AVG(price) as avg_price, MIN(price) as min_price, MAX(price) as max_price
                FROM flights
                WHERE destination = :dest
                AND departure_time > NOW()
                AND status = 'SCHEDULED'
            """)
            
            result = db.execute(query, {"dest": destination}).fetchone()
            
            if result and result[0]:
                avg_price, min_price, max_price = result
                
                # Score inversement proportionnel au prix (normalisé)
                if max_price > min_price:
                    price_range = max_price - min_price
                    normalized_price = (avg_price - min_price) / price_range
                    return max(0.1, 1.0 - normalized_price)
                
            return 0.7  # Score par défaut
            
        except Exception as e:
            logger.error(f"❌ Erreur attractivité prix: {e}")
            return 0.7
    
    async def _calculate_availability_factor(self, db: Session, destination: str) -> float:
        """Calculer le facteur de disponibilité"""
        try:
            query = text("""
                SELECT AVG(CAST(capacity - occupied_seats AS FLOAT) / capacity) as avg_availability
                FROM flights
                WHERE destination = :dest
                AND departure_time > NOW()
                AND status = 'SCHEDULED'
                AND capacity > 0
            """)
            
            result = db.execute(query, {"dest": destination}).fetchone()
            
            if result and result[0]:
                return min(1.0, max(0.1, result[0]))
            
            return 0.5  # Facteur par défaut
            
        except Exception as e:
            logger.error(f"❌ Erreur facteur disponibilité: {e}")
            return 0.5
    
    async def _calculate_destination_popularity(self, db: Session, destination: str) -> float:
        """Calculer la popularité d'une destination"""
        try:
            query = text("""
                SELECT COUNT(*) as booking_count
                FROM bookings b
                JOIN flights f ON b.flight_id = f.id
                WHERE f.destination = :dest
                AND b.booking_date >= NOW() - INTERVAL '90 days'
            """)
            
            result = db.execute(query, {"dest": destination}).fetchone()
            
            if result and result[0]:
                booking_count = result[0]
                # Normaliser par rapport à une base de 50 réservations
                return min(1.0, booking_count / 50.0)
            
            return 0.3  # Popularité par défaut
            
        except Exception as e:
            logger.error(f"❌ Erreur popularité destination: {e}")
            return 0.3
    
    async def _fallback_recommendations(self, db: Session, passenger: Passenger, limit: int) -> List[Dict]:
        """Recommandations de fallback en cas d'échec ML"""
        try:
            logger.info("🔄 Utilisation des recommandations de fallback")
            
            recommendations = []
            
            # Recommandations basées sur les destinations populaires générales
            popular_query = text("""
                SELECT f.destination, COUNT(*) as popularity, AVG(f.price) as avg_price
                FROM flights f
                JOIN bookings b ON f.id = b.flight_id
                WHERE f.departure_time > NOW()
                AND f.status = 'SCHEDULED'
                GROUP BY f.destination
                HAVING COUNT(*) >= 3
                ORDER BY popularity DESC
                LIMIT 5
            """)
            
            popular_destinations = db.execute(popular_query).fetchall()
            
            for dest_info in popular_destinations:
                destination, popularity, avg_price = dest_info
                
                # Éviter les destinations déjà préférées
                if destination not in (passenger.preferred_destinations or []):
                    flight = await self._find_optimal_flight_to_destination(db, destination, passenger)
                    
                    if flight:
                        score = min(0.8, popularity / 10.0)
                        recommendations.append({
                            "passenger_id": passenger.id,
                            "flight_id": flight.id,
                            "recommendation_type": "POPULAR_DESTINATION",
                            "score": round(score, 2),
                            "reason": f"Destination populaire: {destination} - {popularity} réservations récentes"
                        })
                        
                        if len(recommendations) >= limit:
                            break
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Erreur recommandations fallback: {e}")
            return []
    
    async def _build_ml_passenger_profile(self, db: Session, passenger: Passenger) -> Dict[str, Any]:
        """Construire un profil ML détaillé du passager"""
        try:
            # Récupérer l'historique des vols
            bookings = db.query(Booking).filter(Booking.passenger_id == passenger.id).all()
            
            profile = {
                'total_flights': len(bookings),
                'preferred_classes': Counter([b.travel_class for b in bookings]),
                'booking_patterns': self._analyze_booking_patterns(bookings),
                'destination_preferences': passenger.preferred_destinations or [],
                'travel_frequency': len(bookings) / max(1, (datetime.now() - passenger.created_at).days / 30),
                'loyalty_score': self._calculate_loyalty_score(passenger, bookings),
                'price_sensitivity': self._estimate_price_sensitivity(bookings),
                'seasonal_preferences': self._analyze_seasonal_patterns(bookings)
            }
            
            logger.info(f"👤 Profil ML construit: loyalty={profile['loyalty_score']:.2f}, frequency={profile['travel_frequency']:.2f}")
            return profile
            
        except Exception as e:
            logger.error(f"❌ Erreur construction profil ML: {e}")
            return {}
    
    async def _find_similar_passengers_ml(self, db: Session, passenger: Passenger, profile: Dict) -> List[Passenger]:
        """Trouver des passagers similaires avec clustering ML"""
        try:
            # Récupérer tous les passagers avec leurs profils
            all_passengers = db.query(Passenger).limit(1000).all()  # Limite pour performance
            
            # Créer une matrice de caractéristiques
            features_matrix = []
            passenger_ids = []
            
            for p in all_passengers:
                if p.id == passenger.id:
                    continue
                    
                # Calculer des caractéristiques comparables
                p_bookings = db.query(Booking).filter(Booking.passenger_id == p.id).count()
                
                features = [
                    p_bookings,
                    len(p.preferred_destinations or []),
                    1 if p.travel_class_preference == passenger.travel_class_preference else 0,
                    1 if p.nationality == passenger.nationality else 0
                ]
                
                features_matrix.append(features)
                passenger_ids.append(p.id)
            
            if len(features_matrix) < 2:
                return []
            
            # Clustering avec KMeans
            features_array = np.array(features_matrix)
            if features_array.shape[0] > 5:  # Minimum pour clustering
                clusters = self.ml_models['passenger_clusters'].fit_predict(features_array)
                
                # Trouver le cluster du passager cible
                target_features = [
                    profile['total_flights'],
                    len(profile['destination_preferences']),
                    1,  # Même classe
                    1   # Même nationalité
                ]
                
                target_cluster = self.ml_models['passenger_clusters'].predict([target_features])[0]
                
                # Récupérer les passagers du même cluster
                similar_passenger_ids = [passenger_ids[i] for i, cluster in enumerate(clusters) if cluster == target_cluster]
                similar_passengers = db.query(Passenger).filter(Passenger.id.in_(similar_passenger_ids[:10])).all()
                
                logger.info(f"🎯 {len(similar_passengers)} passagers similaires trouvés via ML")
                return similar_passengers
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche passagers similaires ML: {e}")
            return []
    
    async def _generate_ml_recommendations(self, db: Session, passenger: Passenger, similar_passengers: List[Passenger]) -> List[Dict]:
        """Générer des recommandations basées sur ML collaborative filtering"""
        recommendations = []
        
        try:
            # Analyser les destinations des passagers similaires
            similar_bookings = []
            for sim_passenger in similar_passengers:
                bookings = db.query(Booking).filter(Booking.passenger_id == sim_passenger.id).all()
                similar_bookings.extend(bookings)
            
            if not similar_bookings:
                return []
            
            # Extraire les destinations populaires
            flight_ids = [b.flight_id for b in similar_bookings]
            popular_flights = db.query(Flight).filter(
                Flight.id.in_(flight_ids),
                Flight.departure_time > datetime.now()
            ).limit(10).all()
            
            for flight in popular_flights:
                score = self._calculate_ml_score(passenger, flight, similar_passengers)
                
                recommendations.append({
                    'flight_id': flight.id,
                    'type': 'ML_COLLABORATIVE',
                    'score': score,
                    'reason': f"Recommandé par {len(similar_passengers)} passagers similaires - Destination: {flight.destination}"
                })
            
            logger.info(f"🤖 {len(recommendations)} recommandations ML collaborative générées")
            
        except Exception as e:
            logger.error(f"❌ Erreur génération recommandations ML: {e}")
        
        return recommendations
    
    async def _generate_realtime_recommendations(self, db: Session, passenger: Passenger) -> List[Dict]:
        """Générer des recommandations basées sur les tendances temps réel"""
        recommendations = []
        
        try:
            # Analyser les tendances des dernières 24h
            recent_bookings = db.query(Booking).filter(
                Booking.booking_date >= datetime.now() - timedelta(hours=24)
            ).all()
            
            if not recent_bookings:
                return []
            
            # Destinations trending
            destination_counts = Counter()
            for booking in recent_bookings:
                flight = db.query(Flight).filter(Flight.id == booking.flight_id).first()
                if flight:
                    destination_counts[flight.destination] += 1
            
            # Recommander les destinations trending
            trending_destinations = destination_counts.most_common(3)
            
            for destination, count in trending_destinations:
                # Trouver des vols vers cette destination
                trending_flights = db.query(Flight).filter(
                    Flight.destination == destination,
                    Flight.departure_time > datetime.now(),
                    Flight.departure_time < datetime.now() + timedelta(days=30)
                ).limit(2).all()
                
                for flight in trending_flights:
                    score = min(0.8, count / 10)  # Score basé sur la popularité
                    
                    recommendations.append({
                        'flight_id': flight.id,
                        'type': 'REALTIME_TRENDING',
                        'score': score,
                        'reason': f"Destination tendance: {count} réservations récentes pour {destination}"
                    })
            
            logger.info(f"📈 {len(recommendations)} recommandations temps réel générées")
            
        except Exception as e:
            logger.error(f"❌ Erreur génération recommandations temps réel: {e}")
        
        return recommendations
    
    async def _score_recommendations_hybrid(self, db: Session, passenger: Passenger, recommendations: List[Dict]) -> List[Dict]:
        """Scorer les recommandations avec un modèle hybride"""
        try:
            for rec in recommendations:
                flight = db.query(Flight).filter(Flight.id == rec['flight_id']).first()
                if not flight:
                    continue
                
                # Score hybride combinant plusieurs facteurs
                base_score = rec['score']
                
                # Facteur prix (si dans la gamme du passager)
                price_factor = self._calculate_price_factor(passenger, flight)
                
                # Facteur disponibilité
                availability_factor = (flight.capacity - flight.occupied_seats) / flight.capacity
                
                # Facteur préférence destination
                destination_factor = 1.0
                if passenger.preferred_destinations and flight.destination in passenger.preferred_destinations:
                    destination_factor = 1.5
                
                # Score final
                final_score = base_score * price_factor * availability_factor * destination_factor
                rec['score'] = min(1.0, final_score)
                
                # Améliorer la raison
                rec['reason'] += f" | Score: {final_score:.2f} | Places: {flight.capacity - flight.occupied_seats}"
            
            # Trier par score décroissant
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            
            logger.info(f"🎯 {len(recommendations)} recommandations scorées avec modèle hybride")
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Erreur scoring hybride: {e}")
            return recommendations
    
    def _calculate_ml_score(self, passenger: Passenger, flight: Flight, similar_passengers: List[Passenger]) -> float:
        """Calculer un score ML pour une recommandation"""
        try:
            # Score basé sur la similarité des passagers
            similarity_score = len(similar_passengers) / 20  # Normaliser
            
            # Score basé sur les préférences
            preference_score = 0.5
            if passenger.preferred_destinations and flight.destination in passenger.preferred_destinations:
                preference_score = 0.9
            
            # Score basé sur la classe de voyage
            class_score = 0.6
            if passenger.travel_class_preference == "BUSINESS" and flight.price and flight.price > 1000:
                class_score = 0.8
            
            # Score composite
            final_score = (similarity_score * 0.4 + preference_score * 0.4 + class_score * 0.2)
            return min(1.0, final_score)
            
        except Exception as e:
            logger.error(f"❌ Erreur calcul score ML: {e}")
            return 0.5
    
    def _analyze_booking_patterns(self, bookings: List[Booking]) -> Dict:
        """Analyser les patterns de réservation"""
        if not bookings:
            return {}
        
        return {
            'avg_advance_booking': sum([(b.flight.departure_time - b.booking_date).days for b in bookings if b.flight]) / len(bookings),
            'preferred_times': Counter([b.booking_date.hour for b in bookings]),
            'class_distribution': Counter([b.travel_class for b in bookings])
        }
    
    def _calculate_loyalty_score(self, passenger: Passenger, bookings: List[Booking]) -> float:
        """Calculer un score de fidélité"""
        try:
            # Facteurs: nombre de vols, ancienneté, fréquence
            flight_count = len(bookings)
            account_age = (datetime.now() - passenger.created_at).days
            frequency = flight_count / max(1, account_age / 30)  # vols par mois
            
            loyalty_score = min(1.0, (flight_count * 0.1 + frequency * 0.3 + min(account_age/365, 1) * 0.2))
            return loyalty_score
            
        except Exception as e:
            logger.error(f"❌ Erreur calcul loyalty score: {e}")
            return 0.5
    
    def _estimate_price_sensitivity(self, bookings: List[Booking]) -> float:
        """Estimer la sensibilité au prix"""
        if not bookings:
            return 0.5
        
        try:
            prices = [float(b.price) for b in bookings if b.price]
            if not prices:
                return 0.5
            
            avg_price = sum(prices) / len(prices)
            
            # Sensibilité inversement proportionnel au prix moyen
            if avg_price > 2000:
                return 0.2  # Peu sensible au prix
            elif avg_price > 1000:
                return 0.5  # Moyennement sensible
            else:
                return 0.8  # Très sensible au prix
                
        except Exception as e:
            logger.error(f"❌ Erreur estimation price sensitivity: {e}")
            return 0.5
    
    def _analyze_seasonal_patterns(self, bookings: List[Booking]) -> Dict:
        """Analyser les patterns saisonniers"""
        if not bookings:
            return {}
        
        try:
            months = [b.booking_date.month for b in bookings]
            return {
                'preferred_months': Counter(months).most_common(3),
                'seasonality_score': len(set(months)) / 12  # Diversité saisonnière
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse patterns saisonniers: {e}")
            return {}
    
    def _calculate_price_factor(self, passenger: Passenger, flight: Flight) -> float:
        """Calculer le facteur prix pour le scoring"""
        if not flight.price:
            return 1.0
        
        try:
            # Basé sur la classe préférée du passager
            if passenger.travel_class_preference == "BUSINESS" and flight.price > 1500:
                return 1.2
            elif passenger.travel_class_preference == "ECONOMY" and flight.price < 800:
                return 1.2
            elif passenger.travel_class_preference == "FIRST" and flight.price > 3000:
                return 1.2
            else:
                return 0.8
                
        except Exception as e:
            logger.error(f"❌ Erreur calcul facteur prix: {e}")
            return 1.0
