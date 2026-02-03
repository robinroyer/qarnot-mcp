.PHONY: build up down logs restart clean test

COMPOSE_LOCAL = docker compose -f docker-compose.local.yml
COMPOSE_PROD  = docker compose -f docker-compose.prod.yml

## Build the Docker image
build:
	$(COMPOSE_LOCAL) build

## Start the local stack (server + cloudflare tunnel)
up:
	$(COMPOSE_LOCAL) up -d

## Stop the local stack
down:
	$(COMPOSE_LOCAL) down

## Show logs (follow mode)
logs:
	$(COMPOSE_LOCAL) logs -f

## Restart the local stack
restart: down up

## Remove containers, images and volumes
clean:
	$(COMPOSE_LOCAL) down --rmi local -v

## Send an MCP initialize request to verify the server is running
test:
	./scripts/test_initialize.sh

## Start the production stack
prod-up:
	$(COMPOSE_PROD) up -d

## Stop the production stack
prod-down:
	$(COMPOSE_PROD) down
