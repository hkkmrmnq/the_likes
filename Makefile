devup:
	docker-compose -f docker-compose.dev.yml up --build

devadmin:
	docker exec -it backend uv run python prepare.py superuser

devdown:
	docker-compose -f docker-compose.dev.yml down -v