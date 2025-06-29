from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging
import os
from models import Passenger, Flight
from services.passenger_service import PassengerService
from services.flight_service import FlightService

logger = logging.getLogger(__name__)

class EmailService:
    
    def __init__(self):
        self.passenger_service = PassengerService()
        self.flight_service = FlightService()
        # Note: Dans un environnement de production, utilisez une vraie clé API OpenAI
        self.openai_enabled = os.getenv("OPENAI_API_KEY", "").strip() not in ["", "dummy_key"]
    
    async def generate_travel_email(
        self, 
        db: Session, 
        passenger_id: int, 
        flight_id: int, 
        email_type: str = "travel_suggestion"
    ) -> Dict[str, Any]:
        """Générer un email de suggestion de voyage personnalisé"""
        
        passenger = await self.passenger_service.get_passenger(db, passenger_id)
        flight = await self.flight_service.get_flight(db, flight_id)
        
        if not passenger or not flight:
            raise ValueError("Passager ou vol non trouvé")
        
        passenger_profile = await self.passenger_service.get_passenger_profile(db, passenger_id)
        
        # Données pour la personnalisation
        context = {
            "passenger_name": f"{passenger.first_name} {passenger.last_name}",
            "destination": flight.destination,
            "departure_time": flight.departure_time,
            "flight_number": flight.flight_number,
            "airline": flight.airline,
            "price": float(flight.price) if flight.price else None,
            "preferred_class": passenger.travel_class_preference,
            "total_flights": passenger.total_flights,
            "visited_destinations": passenger_profile.get("visited_destinations", []),
            "preferred_destinations": passenger.preferred_destinations or []
        }
        
        if self.openai_enabled:
            return await self._generate_ai_email(context, email_type)
        else:
            return await self._generate_template_email(context, email_type)
    
    async def generate_marketing_email(
        self, 
        db: Session, 
        passenger_id: int, 
        campaign_type: str = "destination_promotion"
    ) -> Dict[str, Any]:
        """Générer un email marketing personnalisé"""
        
        passenger = await self.passenger_service.get_passenger(db, passenger_id)
        if not passenger:
            raise ValueError("Passager non trouvé")
        
        passenger_profile = await self.passenger_service.get_passenger_profile(db, passenger_id)
        
        context = {
            "passenger_name": f"{passenger.first_name} {passenger.last_name}",
            "preferred_class": passenger.travel_class_preference,
            "total_flights": passenger.total_flights,
            "visited_destinations": passenger_profile.get("visited_destinations", []),
            "preferred_destinations": passenger.preferred_destinations or [],
            "frequent_flyer_id": passenger.frequent_flyer_id
        }
        
        if self.openai_enabled:
            return await self._generate_ai_marketing_email(context, campaign_type)
        else:
            return await self._generate_template_marketing_email(context, campaign_type)
    
    async def _generate_ai_email(self, context: Dict[str, Any], email_type: str) -> Dict[str, Any]:
        """Générer un email avec OpenAI (simulation)"""
        # Cette fonction simule l'utilisation d'OpenAI
        # Dans un environnement réel, vous utiliseriez l'API OpenAI
        
        prompt = self._build_ai_prompt(context, email_type)
        
        # Simulation d'une réponse AI
        if email_type == "travel_suggestion":
            subject = f"✈️ {context['passenger_name']}, découvrez {context['destination']} !"
            body = f"""
Bonjour {context['passenger_name']},

Nous avons trouvé une opportunité parfaite pour votre prochain voyage !

🌍 Destination : {context['destination']}
✈️ Vol : {context['flight_number']} ({context['airline']})
📅 Départ : {context['departure_time'].strftime('%d/%m/%Y à %H:%M')}
💰 Prix : {context['price']}€

Basé sur votre profil de voyageur ({context['total_flights']} vols effectués) et vos préférences pour {', '.join(context['preferred_destinations'][:3])}, nous pensons que cette destination vous plaira !

Réservez maintenant et profitez de votre classe préférée : {context['preferred_class']}.

Bon voyage !
L'équipe CDG
"""
        else:
            subject = f"Offre spéciale pour {context['passenger_name']}"
            body = "Email personnalisé généré par IA (simulation)"
        
        return {
            "subject": subject,
            "body": body,
            "recipient_email": context.get("email", ""),
            "recipient_name": context["passenger_name"],
            "personalization_data": context,
            "generation_method": "AI_SIMULATION"
        }
    
    async def _generate_template_email(self, context: Dict[str, Any], email_type: str) -> Dict[str, Any]:
        """Générer un email avec des templates prédéfinis"""
        
        templates = {
            "travel_suggestion": {
                "subject": f"✈️ Nouvelle destination recommandée : {context['destination']}",
                "body": f"""
Bonjour {context['passenger_name']},

Nous avons une suggestion de voyage spécialement pour vous !

🎯 Destination recommandée : {context['destination']}
✈️ Vol disponible : {context['flight_number']} - {context['airline']}
📅 Départ le : {context['departure_time'].strftime('%d/%m/%Y à %H:%M')}
{'💰 Prix : ' + str(context['price']) + '€' if context['price'] else ''}

Cette recommandation est basée sur :
- Vos {context['total_flights']} voyages précédents
- Vos destinations préférées : {', '.join(context['preferred_destinations'][:3]) if context['preferred_destinations'] else 'À découvrir'}
- Votre classe préférée : {context['preferred_class']}

Ne manquez pas cette opportunité !

Cordialement,
L'équipe Aéroport Charles de Gaulle

---
Cet email a été personnalisé pour vous. Si vous ne souhaitez plus recevoir nos suggestions, contactez-nous.
"""
            },
            "booking_confirmation": {
                "subject": f"Confirmation de réservation - Vol {context['flight_number']}",
                "body": f"""
Bonjour {context['passenger_name']},

Votre réservation est confirmée !

✅ Référence : {context.get('booking_reference', 'N/A')}
✈️ Vol : {context['flight_number']} - {context['airline']}
🎯 Destination : {context['destination']}
📅 Départ : {context['departure_time'].strftime('%d/%m/%Y à %H:%M')}
🪑 Siège : {context.get('seat_number', 'À attribuer')}

Bon voyage !
L'équipe CDG
"""
            }
        }
        
        template = templates.get(email_type, templates["travel_suggestion"])
        
        return {
            "subject": template["subject"],
            "body": template["body"],
            "recipient_email": context.get("email", ""),
            "recipient_name": context["passenger_name"],
            "personalization_data": context,
            "generation_method": "TEMPLATE"
        }
    
    async def _generate_ai_marketing_email(self, context: Dict[str, Any], campaign_type: str) -> Dict[str, Any]:
        """Générer un email marketing avec IA (simulation)"""
        
        if campaign_type == "destination_promotion":
            subject = f"🌟 Offres exclusives pour {context['passenger_name']}"
            body = f"""
Cher(e) {context['passenger_name']},

En tant que voyageur expérimenté ({context['total_flights']} vols), vous méritez les meilleures offres !

🎁 OFFRES PERSONNALISÉES :
- 20% de réduction sur vos destinations préférées
- Surclassement gratuit en {context['preferred_class']}
- Accès prioritaire aux nouveaux vols

Vos destinations recommandées :
{chr(10).join(['• ' + dest for dest in context['preferred_destinations'][:5]])}

Utilisez votre numéro de fidélité : {context['frequent_flyer_id']}

L'équipe Marketing CDG
"""
        else:
            subject = f"Offre spéciale {campaign_type}"
            body = f"Email marketing personnalisé pour {context['passenger_name']}"
        
        return {
            "subject": subject,
            "body": body,
            "recipient_name": context["passenger_name"],
            "campaign_type": campaign_type,
            "personalization_data": context,
            "generation_method": "AI_MARKETING_SIMULATION"
        }
    
    async def _generate_template_marketing_email(self, context: Dict[str, Any], campaign_type: str) -> Dict[str, Any]:
        """Générer un email marketing avec des templates"""
        
        templates = {
            "destination_promotion": {
                "subject": f"🌟 Offres exclusives destinations - {context['passenger_name']}",
                "body": f"""
Bonjour {context['passenger_name']},

Découvrez nos offres exclusives sélectionnées pour vous !

🎯 DESTINATIONS RECOMMANDÉES :
{chr(10).join(['• ' + dest for dest in context['preferred_destinations'][:5]]) if context['preferred_destinations'] else '• Paris • Londres • New York • Tokyo • Dubai'}

✨ VOS AVANTAGES :
- Membre depuis {context['total_flights']} voyages
- Réductions sur votre classe préférée : {context['preferred_class']}
- Offres personnalisées basées sur votre profil

💳 Code promo : VOYAGE2024

Réservez maintenant !

L'équipe CDG Marketing
""",
            },
            "seasonal_offers": {
                "subject": "🌞 Offres saisonnières personnalisées",
                "body": f"""
Cher(e) {context['passenger_name']},

Profitez de nos offres saisonnières !

🌞 DESTINATIONS DE SAISON
🎫 RÉDUCTIONS JUSQU'À 30%
✈️ SURCLASSEMENTS GRATUITS

Votre profil voyageur nous permet de vous proposer les meilleures offres.

À bientôt,
L'équipe CDG
"""
            }
        }
        
        template = templates.get(campaign_type, templates["destination_promotion"])
        
        return {
            "subject": template["subject"],
            "body": template["body"],
            "recipient_name": context["passenger_name"],
            "campaign_type": campaign_type,
            "personalization_data": context,
            "generation_method": "TEMPLATE_MARKETING"
        }
    
    def _build_ai_prompt(self, context: Dict[str, Any], email_type: str) -> str:
        """Construire le prompt pour l'IA"""
        return f"""
Générer un email {email_type} personnalisé pour :
- Nom : {context['passenger_name']}
- Destination : {context.get('destination', 'N/A')}
- Préférences : {context.get('preferred_destinations', [])}
- Classe préférée : {context.get('preferred_class', 'ECONOMY')}
- Nombre de vols : {context.get('total_flights', 0)}

L'email doit être professionnel, engageant et personnalisé.
"""
