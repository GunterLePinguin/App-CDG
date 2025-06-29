import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import json
import random
import math

# Configuration de la page
st.set_page_config(
    page_title="✈️ Aéroport CDG - Dashboard Cohérent",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

class CDGDashboardV2:
    def __init__(self):
        self.api_base_url = "http://app:8000"
        
    def make_api_request(self, endpoint):
        """Effectuer une requête API avec gestion d'erreur améliorée"""
        try:
            url = f"{self.api_base_url}{endpoint}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                st.warning(f"⚠️ API Error {response.status_code} for {endpoint}")
                return None
        except requests.exceptions.ConnectionError:
            st.error(f"🔌 Connexion impossible à l'API: {endpoint}")
            return None
        except requests.exceptions.Timeout:
            st.error(f"⏱️ Timeout API (>10s): {endpoint}")
            return None
        except Exception as e:
            st.error(f"❌ Erreur API {endpoint}: {str(e)}")
            return None
    
    def get_consistent_data(self, data_type):
        """Récupérer des données cohérentes avec fallback simplifié"""
        endpoints = {
            "flights": ["/flights/"],
            "passengers": ["/passengers/"], 
            "services": ["/services/"],
            "events": ["/realtime/events/stream"],
            "realtime": ["/realtime/dashboard"]
        }
        
        # Essayer les endpoints pour ce type de données
        if data_type in endpoints:
            for endpoint in endpoints[data_type]:
                try:
                    data = self.make_api_request(endpoint)
                    if data and isinstance(data, list) and len(data) > 0:
                        return data
                    elif data and isinstance(data, dict):
                        # Pour realtime/dashboard, extraire les bonnes données
                        if endpoint == "/realtime/dashboard":
                            if data_type == "flights" and "flights" in data:
                                flight_data = data["flights"]
                                if isinstance(flight_data, list):
                                    return flight_data
                        # Pour d'autres structures de données imbriquées
                        elif data_type in data and isinstance(data[data_type], list):
                            return data[data_type]
                except Exception as e:
                    continue
        
        # Fallback vers données simulées cohérentes
        st.info(f"🔄 Utilisation des données de démonstration pour {data_type}")
        return self.get_fallback_data(data_type)
    
    def get_fallback_data(self, data_type):
        """Données de fallback cohérentes"""
        current_time = datetime.now()
        
        if data_type == "flights":
            return [
                {
                    "id": 1, "flight_number": "AF1234", "airline": "Air France",
                    "departure_time": (current_time + timedelta(hours=2)).isoformat(),
                    "arrival_time": (current_time + timedelta(hours=5)).isoformat(),
                    "destination": "New York JFK", "gate": "A12", "status": "SCHEDULED",
                    "capacity": 300, "occupied_seats": 245
                },
                {
                    "id": 2, "flight_number": "LH5678", "airline": "Lufthansa",
                    "departure_time": (current_time + timedelta(minutes=45)).isoformat(),
                    "arrival_time": (current_time + timedelta(hours=2)).isoformat(),
                    "destination": "Munich", "gate": "B23", "status": "BOARDING",
                    "capacity": 180, "occupied_seats": 156
                },
                {
                    "id": 3, "flight_number": "BA9012", "airline": "British Airways",
                    "departure_time": (current_time + timedelta(hours=1)).isoformat(),
                    "arrival_time": (current_time + timedelta(hours=3)).isoformat(),
                    "destination": "London Heathrow", "gate": "C15", "status": "DELAYED",
                    "capacity": 250, "occupied_seats": 198
                }
            ]
        
        elif data_type == "passengers":
            return [
                {"id": 1, "first_name": "Jean", "last_name": "Dupont", "email": "jean.dupont@email.fr", "nationality": "FR"},
                {"id": 2, "first_name": "Marie", "last_name": "Martin", "email": "marie.martin@email.fr", "nationality": "FR"},
                {"id": 3, "first_name": "Hans", "last_name": "Mueller", "email": "hans.mueller@email.de", "nationality": "DE"},
                {"id": 4, "first_name": "John", "last_name": "Smith", "email": "john.smith@email.com", "nationality": "US"},
                {"id": 5, "first_name": "Maria", "last_name": "Garcia", "email": "maria.garcia@email.es", "nationality": "ES"}
            ]
        
        elif data_type == "services":
            return [
                {"id": 1, "name": "Restaurant Le Bistrot", "type": "RESTAURANT", "terminal": "A", "capacity": 120, "current_usage": 85, "rating": 4.2},
                {"id": 2, "name": "Boutique Duty Free", "type": "SHOP", "terminal": "B", "capacity": 200, "current_usage": 145, "rating": 4.0},
                {"id": 3, "name": "Salon VIP", "type": "LOUNGE", "terminal": "C", "capacity": 80, "current_usage": 45, "rating": 4.8}
            ]
        
        elif data_type == "events":
            return [
                {"id": 1, "event_type": "BOARDING_STARTED", "description": "Embarquement AF1234", "timestamp": current_time.isoformat()},
                {"id": 2, "event_type": "GATE_CHANGE", "description": "Changement porte A12→A15", "timestamp": (current_time - timedelta(minutes=5)).isoformat()},
                {"id": 3, "event_type": "SECURITY_CHECK", "description": "Contrôle sécurité terminal B", "timestamp": (current_time - timedelta(minutes=10)).isoformat()}
            ]
        
        return []
    
    def display_header(self):
        """En-tête moderne"""
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 2rem; border-radius: 20px; margin-bottom: 2rem; color: white; text-align: center;">
            <h1 style="margin: 0; font-size: 3rem; font-weight: 700;">✈️ CDG Airport Dashboard</h1>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;">Tableau de Bord Temps Réel Cohérent</p>
        </div>
        """, unsafe_allow_html=True)
    
    def display_metrics(self):
        """Métriques principales cohérentes avec graphiques"""
        flights_data = self.get_consistent_data("flights")
        passengers_data = self.get_consistent_data("passengers")
        services_data = self.get_consistent_data("services")
        
        # Métriques principales
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_flights = len(flights_data) if flights_data else 0
            st.metric("✈️ Total Vols", total_flights)
        
        with col2:
            boarding_count = len([f for f in flights_data if f.get('status') == 'BOARDING']) if flights_data else 0
            st.metric("🛫 En Embarquement", boarding_count)
        
        with col3:
            if flights_data:
                avg_occ = sum(f.get('occupied_seats', 0) / f.get('capacity', 1) * 100 for f in flights_data) / len(flights_data)
                st.metric("📊 Occupation Moy.", f"{avg_occ:.1f}%")
            else:
                st.metric("📊 Occupation Moy.", "N/A")
        
        with col4:
            delayed_count = len([f for f in flights_data if f.get('status') == 'DELAYED']) if flights_data else 0
            st.metric("⏰ Retardés", delayed_count)
        
        with col5:
            total_passengers = len(passengers_data) if passengers_data else 0
            st.metric("👥 Passagers", total_passengers)
        
        # Graphiques de métriques en temps réel
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Jauge d'occupation globale
            if flights_data:
                avg_occupation = sum(f.get('occupied_seats', 0) / f.get('capacity', 1) * 100 for f in flights_data) / len(flights_data)
                fig_gauge = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = avg_occupation,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Taux d'Occupation Global (%)"},
                    delta = {'reference': 75},
                    gauge = {
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 80], 'color': "yellow"},
                            {'range': [80, 100], 'color': "red"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 90
                        }
                    }
                ))
                fig_gauge.update_layout(height=300)
                st.plotly_chart(fig_gauge, use_container_width=True)
        
        with col2:
            # Indicateur de performance des services
            if services_data:
                services_df = pd.DataFrame(services_data)
                if 'current_usage' in services_df.columns and 'capacity' in services_df.columns:
                    avg_service_usage = (services_df['current_usage'] / services_df['capacity'] * 100).mean()
                    fig_service_gauge = go.Figure(go.Indicator(
                        mode = "gauge+number",
                        value = avg_service_usage,
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        title = {'text': "Utilisation Services (%)"},
                        gauge = {
                            'axis': {'range': [None, 100]},
                            'bar': {'color': "green"},
                            'steps': [
                                {'range': [0, 30], 'color': "lightgray"},
                                {'range': [30, 70], 'color': "yellow"},
                                {'range': [70, 100], 'color': "red"}
                            ]
                        }
                    ))
                    fig_service_gauge.update_layout(height=300)
                    st.plotly_chart(fig_service_gauge, use_container_width=True)
        
        with col3:
            # Score de ponctualité
            if flights_data:
                on_time = len([f for f in flights_data if f.get('status') in ['SCHEDULED', 'BOARDING', 'DEPARTED']])
                punctuality_score = (on_time / len(flights_data) * 100) if flights_data else 0
                fig_punct = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = punctuality_score,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Score Ponctualité (%)"},
                    gauge = {
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "purple"},
                        'steps': [
                            {'range': [0, 60], 'color': "red"},
                            {'range': [60, 85], 'color': "yellow"},
                            {'range': [85, 100], 'color': "green"}
                        ]
                    }
                ))
                fig_punct.update_layout(height=300)
                st.plotly_chart(fig_punct, use_container_width=True)
    
    def display_flights_table(self):
        """Tableau des vols cohérent avec graphiques"""
        st.markdown("### ✈️ Vols en Temps Réel")
        
        flights_data = self.get_consistent_data("flights")
        if flights_data:
            df = pd.DataFrame(flights_data)
            
            # Graphiques en colonnes
            col1, col2 = st.columns(2)
            
            with col1:
                # Graphique des statuts de vols
                if 'status' in df.columns:
                    st.markdown("#### 📊 Statuts des Vols")
                    status_counts = df['status'].value_counts()
                    colors = {'SCHEDULED': '#3498db', 'BOARDING': '#f39c12', 'DELAYED': '#e74c3c', 'DEPARTED': '#27ae60', 'CANCELLED': '#95a5a6'}
                    fig_status = px.pie(
                        values=status_counts.values, 
                        names=status_counts.index,
                        title="Répartition des Statuts",
                        color=status_counts.index,
                        color_discrete_map=colors
                    )
                    fig_status.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_status, use_container_width=True)
            
            with col2:
                # Graphique des compagnies
                if 'airline' in df.columns:
                    st.markdown("#### 🏢 Vols par Compagnie")
                    airline_counts = df['airline'].value_counts().head(8)
                    fig_airlines = px.bar(
                        x=airline_counts.values,
                        y=airline_counts.index,
                        orientation='h',
                        title="Top Compagnies",
                        color=airline_counts.values,
                        color_continuous_scale='viridis'
                    )
                    fig_airlines.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_airlines, use_container_width=True)
            
            # Graphique d'occupation des vols
            if 'occupied_seats' in df.columns and 'capacity' in df.columns:
                df['occupation_rate'] = (df['occupied_seats'] / df['capacity'] * 100).round(1)
                st.markdown("#### 📈 Taux d'Occupation des Vols")
                
                fig_occupation = px.histogram(
                    df, 
                    x='occupation_rate',
                    nbins=10,
                    title="Distribution du Taux d'Occupation",
                    labels={'occupation_rate': 'Taux d\'Occupation (%)', 'count': 'Nombre de Vols'},
                    color_discrete_sequence=['#3498db']
                )
                fig_occupation.add_vline(x=df['occupation_rate'].mean(), line_dash="dash", line_color="red", 
                                       annotation_text=f"Moyenne: {df['occupation_rate'].mean():.1f}%")
                st.plotly_chart(fig_occupation, use_container_width=True)
            
            # Formater les heures pour le tableau
            if 'departure_time' in df.columns:
                df['departure_time'] = pd.to_datetime(df['departure_time']).dt.strftime('%H:%M')
            
            # Tableau des vols
            st.markdown("#### 📋 Tableau Détaillé")
            display_columns = ['flight_number', 'airline', 'departure_time', 'destination', 'gate', 'status']
            available_columns = [col for col in display_columns if col in df.columns]
            
            if available_columns:
                df_display = df[available_columns].copy()
                
                # Renommer pour l'affichage
                column_names = {
                    'flight_number': 'Vol',
                    'airline': 'Compagnie',
                    'departure_time': 'Départ',
                    'destination': 'Destination',
                    'gate': 'Porte',
                    'status': 'Statut'
                }
                
                df_display = df_display.rename(columns={k: v for k, v in column_names.items() if k in df_display.columns})
                
                # Ajouter l'occupation si calculée
                if 'occupation_rate' in df.columns:
                    df_display['Occupation %'] = df['occupation_rate']
                
                st.dataframe(df_display, use_container_width=True, height=300)
            else:
                st.warning("Aucune colonne de vol disponible")
        else:
            st.warning("Aucune donnée de vol disponible")
    
    def display_passengers_table(self):
        """Tableau des passagers cohérent avec graphiques"""
        st.markdown("### 👥 Passagers Récents")
        
        passengers_data = self.get_consistent_data("passengers")
        if passengers_data:
            df = pd.DataFrame(passengers_data[:100])  # Limiter à 100 pour les graphiques
            
            # Graphiques en colonnes
            col1, col2 = st.columns(2)
            
            with col1:
                # Graphique des nationalités
                if 'nationality' in df.columns:
                    st.markdown("#### 🌍 Répartition par Nationalité")
                    nat_counts = df['nationality'].value_counts().head(10)
                    fig_nat = px.pie(
                        values=nat_counts.values, 
                        names=nat_counts.index, 
                        title="Top 10 Nationalités",
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    fig_nat.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_nat, use_container_width=True)
            
            with col2:
                # Graphique des classes de voyage
                if 'travel_class_preference' in df.columns:
                    st.markdown("#### ✈️ Préférences de Classe")
                    class_counts = df['travel_class_preference'].value_counts()
                    colors = {'ECONOMY': '#3498db', 'BUSINESS': '#f39c12', 'FIRST': '#e74c3c'}
                    fig_class = px.bar(
                        x=class_counts.index,
                        y=class_counts.values,
                        title="Classes de Voyage",
                        color=class_counts.index,
                        color_discrete_map=colors
                    )
                    fig_class.update_layout(showlegend=False, xaxis_title="Classe", yaxis_title="Nombre de Passagers")
                    st.plotly_chart(fig_class, use_container_width=True)
            
            # Graphique des âges si disponible
            if 'date_of_birth' in df.columns:
                try:
                    df['age'] = (datetime.now() - pd.to_datetime(df['date_of_birth'])).dt.days // 365
                    st.markdown("#### 📊 Distribution des Âges")
                    
                    # Créer des groupes d'âge
                    bins = [0, 18, 30, 45, 60, 100]
                    labels = ['<18', '18-30', '30-45', '45-60', '60+']
                    df['age_group'] = pd.cut(df['age'], bins=bins, labels=labels, right=False)
                    
                    age_counts = df['age_group'].value_counts()
                    fig_age = px.bar(
                        x=age_counts.index,
                        y=age_counts.values,
                        title="Répartition par Groupe d'Âge",
                        color=age_counts.values,
                        color_continuous_scale='blues'
                    )
                    fig_age.update_layout(showlegend=False, xaxis_title="Groupe d'Âge", yaxis_title="Nombre de Passagers")
                    st.plotly_chart(fig_age, use_container_width=True)
                except:
                    pass
            
            # Tableau des passagers
            st.markdown("#### 📋 Liste des Passagers")
            display_columns = ['first_name', 'last_name', 'email', 'nationality']
            available_columns = [col for col in display_columns if col in df.columns]
            
            if available_columns:
                df_display = df[available_columns].head(50).copy()  # Limiter à 50 pour l'affichage
                
                # Renommer
                column_names = {
                    'first_name': 'Prénom',
                    'last_name': 'Nom',
                    'email': 'Email',
                    'nationality': 'Nationalité'
                }
                
                df_display = df_display.rename(columns={k: v for k, v in column_names.items() if k in df_display.columns})
                
                st.dataframe(df_display, use_container_width=True, height=300)
            else:
                st.warning("Aucune colonne de passager disponible")
        else:
            st.warning("Aucune donnée de passager disponible")
    
    def display_services_table(self):
        """Tableau des services cohérent avec graphiques"""
        st.markdown("### 🏪 Services Aéroport")
        
        services_data = self.get_consistent_data("services")
        if services_data:
            df = pd.DataFrame(services_data)
            
            # Calculer le taux d'utilisation
            if 'current_usage' in df.columns and 'capacity' in df.columns:
                df['usage_rate'] = (df['current_usage'] / df['capacity'] * 100).round(1)
            
            # Graphiques en colonnes
            col1, col2 = st.columns(2)
            
            with col1:
                # Graphique des types de services
                if 'type' in df.columns:
                    st.markdown("#### 🏢 Types de Services")
                    type_counts = df['type'].value_counts()
                    colors = {
                        'RESTAURANT': '#e74c3c', 'SHOP': '#3498db', 'LOUNGE': '#f39c12', 
                        'SECURITY': '#9b59b6', 'CUSTOMS': '#27ae60', 'BAGGAGE': '#34495e'
                    }
                    fig_types = px.pie(
                        values=type_counts.values,
                        names=type_counts.index,
                        title="Répartition par Type",
                        color=type_counts.index,
                        color_discrete_map=colors
                    )
                    fig_types.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_types, use_container_width=True)
            
            with col2:
                # Graphique des services par terminal
                if 'terminal' in df.columns:
                    st.markdown("#### 🏢 Services par Terminal")
                    terminal_counts = df['terminal'].value_counts()
                    fig_terminals = px.bar(
                        x=terminal_counts.index,
                        y=terminal_counts.values,
                        title="Nombre de Services",
                        color=terminal_counts.values,
                        color_continuous_scale='viridis'
                    )
                    fig_terminals.update_layout(showlegend=False, xaxis_title="Terminal", yaxis_title="Nombre de Services")
                    st.plotly_chart(fig_terminals, use_container_width=True)
            
            # Graphique des taux d'utilisation
            if 'usage_rate' in df.columns:
                st.markdown("#### 📊 Taux d'Utilisation des Services")
                
                # Heatmap par type et terminal
                if 'type' in df.columns and 'terminal' in df.columns:
                    pivot_data = df.pivot_table(values='usage_rate', index='type', columns='terminal', aggfunc='mean')
                    fig_heatmap = px.imshow(
                        pivot_data,
                        title="Taux d'Utilisation Moyen par Type et Terminal (%)",
                        color_continuous_scale='RdYlBu_r',
                        aspect="auto"
                    )
                    fig_heatmap.update_layout(xaxis_title="Terminal", yaxis_title="Type de Service")
                    st.plotly_chart(fig_heatmap, use_container_width=True)
                
                # Histogramme des taux d'utilisation
                fig_usage = px.histogram(
                    df,
                    x='usage_rate',
                    nbins=15,
                    title="Distribution des Taux d'Utilisation",
                    labels={'usage_rate': 'Taux d\'Utilisation (%)', 'count': 'Nombre de Services'},
                    color_discrete_sequence=['#e74c3c']
                )
                fig_usage.add_vline(x=df['usage_rate'].mean(), line_dash="dash", line_color="blue",
                                   annotation_text=f"Moyenne: {df['usage_rate'].mean():.1f}%")
                st.plotly_chart(fig_usage, use_container_width=True)
            
            # Tableau des services
            st.markdown("#### 📋 Tableau Détaillé")
            display_columns = ['name', 'type', 'terminal', 'current_usage', 'capacity', 'usage_rate', 'rating']
            available_columns = [col for col in display_columns if col in df.columns]
            
            if available_columns:
                df_display = df[available_columns].copy()
                
                # Renommer
                column_names = {
                    'name': 'Service',
                    'type': 'Type',
                    'terminal': 'Terminal',
                    'current_usage': 'Utilisation',
                    'capacity': 'Capacité',
                    'usage_rate': 'Taux %',
                    'rating': 'Note'
                }
                
                df_display = df_display.rename(columns={k: v for k, v in column_names.items() if k in df_display.columns})
                
                st.dataframe(df_display, use_container_width=True, height=300)
            else:
                st.warning("Aucune colonne de service disponible")
        else:
            st.warning("Aucune donnée de service disponible")
    
    def display_events_table(self):
        """Tableau des événements cohérent avec graphiques"""
        st.markdown("### 📡 Événements Récents")
        
        events_data = self.get_consistent_data("events")
        if events_data:
            df = pd.DataFrame(events_data[:100])  # Limiter à 100 pour les graphiques
            
            # Graphiques en colonnes
            col1, col2 = st.columns(2)
            
            with col1:
                # Graphique des types d'événements
                if 'event_type' in df.columns:
                    st.markdown("#### 📊 Types d'Événements")
                    event_counts = df['event_type'].value_counts()
                    colors = {
                        'BOARDING_STARTED': '#27ae60', 'GATE_CHANGE': '#f39c12', 'SECURITY_CHECK': '#e74c3c',
                        'FLIGHT_DELAYED': '#e67e22', 'BOARDING_COMPLETE': '#2ecc71', 'BAGGAGE_CLAIM': '#3498db'
                    }
                    fig_events = px.bar(
                        x=event_counts.values,
                        y=event_counts.index,
                        orientation='h',
                        title="Fréquence des Événements",
                        color=event_counts.index,
                        color_discrete_map=colors
                    )
                    fig_events.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_events, use_container_width=True)
            
            with col2:
                # Timeline des événements dans la dernière heure
                if 'timestamp' in df.columns:
                    try:
                        st.markdown("#### ⏰ Événements Récents")
                        df['timestamp_dt'] = pd.to_datetime(df['timestamp'])
                        df['time_ago'] = (datetime.now() - df['timestamp_dt']).dt.total_seconds() / 60  # minutes
                        
                        # Événements des 60 dernières minutes
                        recent_events = df[df['time_ago'] <= 60].copy()
                        if not recent_events.empty:
                            # Créer des bins de 10 minutes
                            recent_events['time_bin'] = (recent_events['time_ago'] // 10) * 10
                            time_counts = recent_events.groupby('time_bin').size()
                            
                            fig_timeline = px.bar(
                                x=[f"{int(t)}-{int(t+10)}min" for t in time_counts.index],
                                y=time_counts.values,
                                title="Événements par Tranche (10min)",
                                color=time_counts.values,
                                color_continuous_scale='reds'
                            )
                            fig_timeline.update_layout(showlegend=False, xaxis_title="Il y a (minutes)", yaxis_title="Nombre d'Événements")
                            st.plotly_chart(fig_timeline, use_container_width=True)
                        else:
                            st.info("Aucun événement récent")
                    except:
                        st.info("Impossible d'analyser la timeline")
            
            # Graphique de l'activité par heure
            if 'timestamp' in df.columns:
                try:
                    st.markdown("#### � Activité par Heure de la Journée")
                    df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
                    hourly_counts = df['hour'].value_counts().sort_index()
                    
                    fig_hourly = px.line(
                        x=hourly_counts.index,
                        y=hourly_counts.values,
                        title="Nombre d'Événements par Heure",
                        markers=True
                    )
                    fig_hourly.update_traces(line_color='#3498db', marker_color='#e74c3c')
                    fig_hourly.update_layout(xaxis_title="Heure de la Journée", yaxis_title="Nombre d'Événements")
                    st.plotly_chart(fig_hourly, use_container_width=True)
                except:
                    pass
            
            # Tableau des événements
            st.markdown("#### 📋 Journal des Événements")
            # Formater la timestamp
            if 'timestamp' in df.columns:
                try:
                    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%H:%M:%S')
                except:
                    pass
            
            # Colonnes d'affichage
            display_columns = ['timestamp', 'event_type', 'description']
            available_columns = [col for col in display_columns if col in df.columns]
            
            if available_columns:
                df_display = df[available_columns].head(30).copy()  # Limiter à 30 pour l'affichage
                
                # Renommer
                column_names = {
                    'timestamp': 'Heure',
                    'event_type': 'Type',
                    'description': 'Description'
                }
                
                df_display = df_display.rename(columns={k: v for k, v in column_names.items() if k in df_display.columns})
                
                st.dataframe(df_display, use_container_width=True, height=300)
            else:
                st.warning("Aucune colonne d'événement disponible")
        else:
            st.warning("Aucune donnée d'événement disponible")
    
    def run(self):
        """Interface principale cohérente"""
        self.display_header()
        
        # Contrôles sidebar
        st.sidebar.markdown("## ⚙️ Contrôles")
        auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh", value=True)
        if auto_refresh:
            refresh_rate = st.sidebar.slider("Fréquence (secondes)", 1, 10, 3)
        
        # Métriques principales
        self.display_metrics()
        
        # Onglets des données
        tab1, tab2, tab3, tab4 = st.tabs(["✈️ Vols", "👥 Passagers", "🏪 Services", "📡 Événements"])
        
        with tab1:
            self.display_flights_table()
        
        with tab2:
            self.display_passengers_table()
        
        with tab3:
            self.display_services_table()
        
        with tab4:
            self.display_events_table()
        
        # Footer
        st.markdown("---")
        current_time = datetime.now().strftime("%H:%M:%S")
        st.markdown(f"""
        <div style="text-align: center; color: #7f8c8d; padding: 1rem;">
            🕐 Dernière mise à jour: {current_time} | 
            ✈️ CDG Dashboard Cohérent V2.0
        </div>
        """, unsafe_allow_html=True)
        
        # Auto-refresh
        if auto_refresh:
            time.sleep(refresh_rate)
            st.rerun()

def main():
    """Fonction principale"""
    dashboard = CDGDashboardV2()
    dashboard.run()

if __name__ == "__main__":
    main()
