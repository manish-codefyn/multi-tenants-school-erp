.PHONY: install test run migrate deploy backup

install:
	pip install -r requirements.txt

migrate:
	python manage.py migrate_schemas --shared

test:
	pytest --cov=apps

run:
	python manage.py runserver

deploy:
	scripts/deploy.sh

backup:
	scripts/backup_db.sh

security-scan:
	scripts/security_scan.py