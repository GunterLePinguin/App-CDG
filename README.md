# 🛫 Système de Gestion Aéroport CDG - Rapport de Projet

**Projet réalisé par :** (Alexandre Goin, Philippe Ksnatkin, Samy Janah, Eliesse Laslah, Nino Liberos, Aline Alhelou)


## 🎯 Présentation du Projet

### Objectif
Ce projet consiste en la création d'un **système de gestion complet pour l'aéroport Charles de Gaulle (CDG)**. Il s'agit d'une application web moderne permettant de gérer en temps réel les vols, passagers et services de l'aéroport.

### Problématique Adressée
- **Gestion centralisée** des données aéroportuaires
- **Visualisation en temps réel** des informations de vol
- **Monitoring des services** de l'aéroport (restaurants, boutiques, sécurité)
- **Interface intuitive** pour les opérateurs aéroportuaires
- **Système de recommandations intelligentes** pour optimiser l'expérience passager

### Approche Technique
Le projet adopte une **architecture microservices** moderne avec :
- API REST robuste
- Interface web responsive
- Base de données relationnelle
- Génération de données temps réel
- Containerisation Docker

---

## 🏗️ Architecture Technique

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FRONTEND      │    │   BACKEND       │    │   DATABASE      │
│   (Streamlit)   │◄──►│   (FastAPI)     │◄──►│  (PostgreSQL)   │
│   Port: 8501    │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       ▲
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  DATA GENERATOR │
                    │   (Python)      │
                    │ Simulation Data │
                    └─────────────────┘
```

### Composants Principaux

1. **Frontend (Dashboard Streamlit)**
   - Interface web interactive
   - Graphiques temps réel
   - Tableaux de données dynamiques
   - Auto-refresh configurable

2. **Backend (API FastAPI)**
   - API REST complète
   - Gestion CRUD des entités
   - Endpoints temps réel
   - Documentation automatique (Swagger)

3. **Base de Données (PostgreSQL)**
   - Modèle relationnel optimisé
   - Index pour performances
   - Contraintes d'intégrité

4. **Générateur de Données**
   - Simulation de données réalistes
   - Mise à jour continue
   - Scénarios d'événements

---

## 🛠️ Technologies Utilisées

### Backend
- **FastAPI** - Framework web moderne et performant
- **SQLAlchemy** - ORM pour la gestion de base de données
- **Pydantic** - Validation et sérialisation des données
- **PostgreSQL** - Base de données relationnelle

### Frontend
- **Streamlit** - Framework pour applications web de données
- **Plotly** - Bibliothèque de visualisation interactive
- **Pandas** - Manipulation et analyse de données

### Infrastructure
- **Docker & Docker Compose** - Containerisation et orchestration
- **Nginx** (optionnel) - Reverse proxy et load balancer

### Outils de Développement
- **Python 3.11+** - Langage principal
- **Poetry/pip** - Gestion des dépendances
- **Faker** - Génération de données de test

---

## ⚡ Fonctionnalités Développées

### 1. Gestion des Vols ✈️
- **CRUD complet** : Création, lecture, mise à jour, suppression
- **Statuts en temps réel** : Programmé, Embarquement, Retardé, Parti
- **Informations détaillées** : Compagnie, destination, porte, horaires
- **Taux d'occupation** : Calcul automatique places occupées/capacité

### 2. Gestion des Passagers 👥
- **Profils complets** : Nom, nationalité, préférences
- **Historique des vols** : Suivi des voyages
- **Classes de voyage** : Economy, Business, First
- **Segmentation** : Analyse par âge et nationalité

### 3. Services Aéroport 🏪
- **Types variés** : Restaurants, boutiques, lounges, sécurité
- **Monitoring d'utilisation** : Capacité vs utilisation actuelle
- **Répartition par terminal** : Vue d'ensemble géographique
- **Système de notation** : Évaluation de la qualité

### 4. Événements Temps Réel 📡
- **Journal d'activité** : Embarquements, changements de porte
- **Timeline** : Événements récents avec horodatage
- **Alertes** : Notifications importantes
- **Statistiques** : Fréquence par type d'événement



## 🚀 Installation et Déploiement

### Prérequis
```bash
- Docker & Docker Compose
- Git
- 8 GB RAM minimum
- Ports libres : 8000, 8501, 5432
```

### Installation Rapide

1. **Clonage du projet**
```bash
git clone [https://github.com/GunterLePinguin/App-CDG.git]
cd CDG_TP
```

2. **Démarrage avec Docker**
```bash
docker-compose up -d
```

3. **Vérification des services**
```bash
docker-compose ps
```

4. **Accès aux interfaces**
- **Dashboard** : http://localhost:8501
- **API Documentation** : http://localhost:8000/docs
- **API** : http://localhost:8000

### Structure du Projet
```
CDG_TP/
├── app/                    # Backend FastAPI
│   ├── main.py            # Point d'entrée API
│   ├── models.py          # Modèles de données
│   ├── schemas.py         # Validation Pydantic
│   └── services/          # Logique métier
├── frontend/              # Dashboard Streamlit
│   ├── dashboard.py       # Interface principale
│   └── .streamlit/        # Configuration
├── data_generator/        # Simulation de données
├── docker-compose.yml     # Orchestration
└── requirements/          # Dépendances
```

### Configuration Docker
```yaml
services:
  api:         # Backend FastAPI
  frontend:    # Dashboard Streamlit  
  postgres:    # Base de données
  generator:   # Générateur de données
```

---

## 🎨 Interface Utilisateur

### Dashboard Principal
L'interface est conçue pour être **intuitive et informative** :

#### En-tête
```
✈️ CDG Airport Dashboard
Tableau de Bord Temps Réel Cohérent
```

#### Métriques Clés (5 indicateurs)
- **Total Vols** : Nombre de vols actifs
- **En Embarquement** : Vols en cours d'embarquement
- **Occupation Moyenne** : Taux de remplissage
- **Retardés** : Nombre de vols retardés
- **Passagers** : Total des passagers

#### Jauges Interactives (3 graphiques)
1. **Taux d'Occupation Global** - Jauge circulaire avec seuils
2. **Utilisation Services** - Performance des services
3. **Score Ponctualité** - Indicateur de performance

#### Onglets Fonctionnels

**1. Onglet Vols ✈️**
- Graphique en secteurs des statuts
- Top compagnies (barres horizontales)
- Histogramme des taux d'occupation
- Tableau détaillé avec pagination

**2. Onglet Passagers 👥**
- Répartition des nationalités (secteurs)
- Préférences de classe (barres)
- Distribution des âges par groupes
- Liste paginée des passagers

**3. Onglet Services 🏪**
- Types de services (secteurs)
- Services par terminal (barres)
- Heatmap d'utilisation par type/terminal
- Histogramme des taux d'utilisation

**4. Onglet Événements 📡**
- Fréquence des événements (barres)
- Timeline des événements récents
- Activité par heure de la journée
- Journal chronologique

### Fonctionnalités UX
- **Auto-refresh** configurable (1-10 secondes)
- **Responsive design** - S'adapte à tous les écrans
- **Couleurs thématiques** - Code couleur par statut/type
- **Interactions** - Graphiques Plotly interactifs
- **Fallback gracieux** - Données de démonstration si API indisponible

---

## 📊 Performances et Métriques

### Données Générées
- **~800 vols** actifs simultanément
- **~20 000 passagers** dans la base
- **~800 services** répartis sur 5 terminaux
- **Événements** générés toutes les 0.5-3 secondes

### Performance API
- **Temps de réponse** : < 100ms par endpoint
- **Concurrence** : Support de 50+ utilisateurs simultanés
- **Cache** : Mise en cache des recommandations
- **Pagination** : Gestion efficace des grandes listes

### Dashboard
- **Chargement initial** : < 3 secondes
- **Refresh** : Mise à jour en < 1 seconde
- **Graphiques** : Rendu temps réel fluide
- **Fallback** : Basculement automatique si API indisponible

---

## 🧩 Défis Techniques Relevés

### 1. Architecture Microservices
**Défi** : Orchestration de 4 services Docker indépendants
**Solution** : Docker Compose avec health checks et dépendances

### 2. Gestion des Données Temps Réel
**Défi** : Génération continue de données cohérentes
**Solution** : Générateur asynchrone avec scénarios réalistes

### 3. Interface Utilisateur Robuste
**Défi** : Dashboard qui reste fonctionnel même si l'API est indisponible
**Solution** : Système de fallback avec données de démonstration

### 4. Performance des Graphiques
**Défi** : Affichage fluide de milliers de points de données
**Solution** : Pagination intelligente et optimisation Plotly

### 5. Cohérence des Données
**Défi** : Synchronisation entre génération et affichage
**Solution** : Validation côté API et normalisation côté frontend

---

## ⚠️ Limites du projet en l'état
### Limites Actuelles

#### Scalabilité
- **Base de données** : Instance unique PostgreSQL
- **Cache** : Cache en mémoire non persistant
- **Load balancing** : Pas de répartition de charge
- **Monitoring** : Logs basiques sans centralisation

#### Fonctionnalités
- **Temps réel** : Pas de WebSockets (polling uniquement)
- **Notifications** : Pas d'alertes push
- **Export** : Pas d'export PDF/Excel des données
- **Personnalisation** : Interface non customisable par utilisateur


## 🎓 Conclusion

### Objectifs Atteints
✅ **Architecture moderne** : Microservices avec Docker  
✅ **Interface riche** : Dashboard interactif temps réel  
✅ **Performance** : Gestion de gros volumes de données  
✅ **Robustesse** : Système de fallback et gestion d'erreurs  
✅ **Évolutivité** : Code modulaire et maintenable  




