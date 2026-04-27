.PHONY: up down logs build shell-api shell-worker seed-data

# Start all services
up:
	docker-compose -f infra/docker-compose.yml up -d

# Stop all services
down:
	docker-compose -f infra/docker-compose.yml down

# View logs for all services
logs:
	docker-compose -f infra/docker-compose.yml logs -f

# Rebuild all images
build:
	docker-compose -f infra/docker-compose.yml build

# Open a shell in the API container
shell-api:
	docker-compose -f infra/docker-compose.yml exec api /bin/sh

# Open a shell in the worker container
shell-worker:
	docker-compose -f infra/docker-compose.yml exec worker /bin/sh

# Run the seed data script (assuming it's run locally or inside a container)
seed-data:
	docker-compose -f infra/docker-compose.yml exec api python scripts/seed_demo_data.py
