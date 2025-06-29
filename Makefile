.PHONY: help build start stop restart logs test test-unit test-integration clean setup

# Variables
COMPOSE_FILE = docker-compose.yml
PROJECT_NAME = cdg-airport

help: ## Afficher l'aide
	@echo "🛫 Système de Gestion Aéroport CDG"
	@echo ""
	@echo "Commandes disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Configuration initiale du projet
	@echo "📝 Configuration initiale..."
	@cp .env.example .env 2>/dev/null || true
	@echo "✅ Fichier .env créé (modifiez-le selon vos besoins)"

build: ## Construire les images Docker
	@echo "🏗️ Construction des images Docker..."
	docker-compose build

start: setup ## Démarrer tous les services
	@echo "🚀 Démarrage du système CDG..."
	docker-compose up -d
	@echo "⏳ Attente du démarrage des services..."
	@sleep 10
	@make status
	@echo ""
	@echo "🎉 Système démarré!"
	@echo "   • API Documentation: http://localhost:8000/docs"
	@echo "   • Dashboard:         http://localhost:8501"

stop: ## Arrêter tous les services
	@echo "🛑 Arrêt des services..."
	docker-compose down

restart: ## Redémarrer tous les services
	@echo "🔄 Redémarrage des services..."
	docker-compose restart

logs: ## Afficher les logs de tous les services
	docker-compose logs -f

logs-app: ## Afficher les logs de l'API
	docker-compose logs -f app

logs-frontend: ## Afficher les logs du dashboard
	docker-compose logs -f frontend

logs-generator: ## Afficher les logs du générateur
	docker-compose logs -f generator

logs-db: ## Afficher les logs de la base de données
	docker-compose logs -f db

status: ## Afficher le statut des services
	@echo "📊 Statut des services:"
	@docker-compose ps

test: test-unit ## Lancer tous les tests

test-unit: ## Lancer les tests unitaires
	@echo "🧪 Tests unitaires..."
	docker-compose exec app pytest tests/ -v

test-integration: ## Lancer les tests d'intégration
	@echo "🧪 Tests d'intégration..."
	@echo "⚠️ Assurez-vous que les services sont démarrés avec 'make start'"
	python tests/integration/test_full_system.py

test-coverage: ## Tests avec couverture de code
	@echo "🧪 Tests avec couverture..."
	docker-compose exec app pytest tests/ --cov=app --cov-report=html

lint: ## Vérification du code avec flake8
	@echo "🔍 Vérification du code..."
	docker-compose exec app flake8 app/

format: ## Formatage du code avec black (si installé)
	@echo "✨ Formatage du code..."
	docker-compose exec app black app/ || echo "Black non installé"

shell-app: ## Ouvrir un shell dans le conteneur API
	docker-compose exec app bash

shell-db: ## Ouvrir un shell dans la base de données
	docker-compose exec db psql -U cdg_user -d airport

clean: ## Nettoyer les ressources Docker
	@echo "🧹 Nettoyage..."
	docker-compose down -v --remove-orphans
	docker system prune -f

clean-all: ## Nettoyage complet (images, volumes, etc.)
	@echo "🧹 Nettoyage complet..."
	docker-compose down -v --remove-orphans
	docker system prune -af
	docker volume prune -f

backup-db: ## Sauvegarder la base de données
	@echo "💾 Sauvegarde de la base de données..."
	@mkdir -p backups
	docker-compose exec db pg_dump -U cdg_user airport > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Sauvegarde créée dans backups/"

restore-db: ## Restaurer la base de données (usage: make restore-db FILE=backup.sql)
	@echo "📥 Restauration de la base de données..."
	@if [ -z "$(FILE)" ]; then echo "❌ Spécifiez le fichier: make restore-db FILE=backup.sql"; exit 1; fi
	docker-compose exec -T db psql -U cdg_user airport < $(FILE)
	@echo "✅ Base de données restaurée"

dev-setup: ## Configuration pour le développement
	@echo "🛠️ Configuration développement..."
	@pip install -r requirements/api.txt -r requirements/test.txt || echo "⚠️ Installez les dépendances manuellement"
	@echo "✅ Environnement de développement prêt"

monitoring: ## Afficher les métriques des conteneurs
	@echo "📈 Métriques des conteneurs:"
	docker stats --no-stream

api-health: ## Vérifier la santé de l'API
	@echo "🏥 Vérification de la santé de l'API..."
	@curl -s http://localhost:8000/health | python -m json.tool || echo "❌ API non accessible"

dashboard-open: ## Ouvrir le dashboard dans le navigateur
	@echo "🌐 Ouverture du dashboard..."
	@xdg-open http://localhost:8501 2>/dev/null || open http://localhost:8501 2>/dev/null || echo "Ouvrez http://localhost:8501 dans votre navigateur"

docs-open: ## Ouvrir la documentation API
	@echo "📖 Ouverture de la documentation API..."
	@xdg-open http://localhost:8000/docs 2>/dev/null || open http://localhost:8000/docs 2>/dev/null || echo "Ouvrez http://localhost:8000/docs dans votre navigateur"

# Commandes de développement rapide
dev: start logs ## Démarrage rapide en mode développement

quick-test: ## Test rapide sans rebuild
	docker-compose exec app pytest tests/test_api.py::test_health_check -v

# Aide par défaut
default: help
