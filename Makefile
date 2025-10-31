devup:
	docker-compose -f docker-compose.dev.yml up --build

devdown:
	docker-compose -f docker-compose.dev.yml down

devfulldown:
	docker-compose -f docker-compose.dev.yml down -v

devadmin:
	docker exec -it backend uv run python prepare.py superuser

testval:
	docker exec -it backend uv run python prepare.py testval
