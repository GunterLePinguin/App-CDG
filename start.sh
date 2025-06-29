#!/bin/bash

# Script de démarrage pour le système CDG
echo "🛫 Démarrage du système de gestion CDG..."

# Vérifier que Docker et Docker Compose sont installés
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

# Créer le fichier .env s'il n'existe pas
if [ ! -f .env ]; then
    echo "📝 Création du fichier .env..."
    cp .env.example .env
    echo "✅ Fichier .env créé. Vous pouvez le modifier selon vos besoins."
fi

# Arrêter les services existants
echo "🛑 Arrêt des services existants..."
docker-compose down

# Construire et démarrer les services
echo "🏗️ Construction et démarrage des services..."
docker-compose up --build -d

# Attendre que les services soient prêts
echo "⏳ Attente du démarrage des services..."
sleep 10

# Vérifier l'état des services
echo "🔍 Vérification de l'état des services..."
docker-compose ps

# Attendre que l'API soit prête
echo "⏳ Attente de l'API..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ API prête!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ L'API n'a pas démarré dans les temps"
        exit 1
    fi
    sleep 2
done

# Afficher les URLs d'accès
echo ""
echo "🎉 Système CDG démarré avec succès!"
echo ""
echo "📍 URLs d'accès:"
echo "   • API Documentation: http://localhost:8000/docs"
echo "   • API Health Check:  http://localhost:8000/health"
echo "   • Dashboard:         http://localhost:8501"
echo ""
echo "🐳 Commandes Docker utiles:"
echo "   • Voir les logs:     docker-compose logs -f"
echo "   • Arrêter:          docker-compose down"
echo "   • Redémarrer:       docker-compose restart"
echo ""
echo "🧪 Pour lancer les tests:"
echo "   • Tests unitaires:  docker-compose exec app pytest tests/"
echo "   • Tests intégration: python tests/integration/test_full_system.py"
echo ""

# Optionnel: ouvrir le navigateur (Linux avec xdg-open)
if command -v xdg-open &> /dev/null; then
    echo "🌐 Ouverture du dashboard dans le navigateur..."
    xdg-open http://localhost:8501 &
fi
