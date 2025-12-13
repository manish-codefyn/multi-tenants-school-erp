#!/bin/bash
# reset_database.sh
# Automated script to reset database and migrations

# Configuration
DB_NAME="eduerpdb_v6"
DB_USER="postgres"
DB_OWNER="codefyn"
POSTGRES_PASSWORD="Jaimaa@007"
DJANGO_VERSION="4.2.7"

# Set password for PostgreSQL
export PGPASSWORD="$POSTGRES_PASSWORD"

echo "============================================================"
echo "Starting Automated Database Reset"
echo "============================================================"

# Ask for confirmation
read -p "Do you want to proceed? This will reset your database. (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Operation cancelled."
    exit 1
fi

# Function to run commands with error checking
run_cmd() {
    echo "Running: $1"
    if eval "$1"; then
        echo "✓ Success"
    else
        echo "✗ Failed"
        exit 1
    fi
}

# 1. Reset PostgreSQL database
echo ""
echo "1. Resetting PostgreSQL Database..."
run_cmd "psql -U $DB_USER -c \"DROP DATABASE IF EXISTS $DB_NAME;\""
run_cmd "psql -U $DB_USER -c \"CREATE DATABASE $DB_NAME;\""
run_cmd "psql -U $DB_USER -d $DB_NAME -c \"ALTER SCHEMA public OWNER TO $DB_OWNER;\""
run_cmd "psql -U $DB_USER -d $DB_NAME -c \"GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_OWNER;\""
run_cmd "psql -U $DB_USER -d $DB_NAME -c \"GRANT ALL ON SCHEMA public TO $DB_OWNER;\""
run_cmd "psql -U $DB_USER -d $DB_NAME -c \"GRANT CREATE ON SCHEMA public TO $DB_OWNER;\""

# 2. Clean Django migrations
echo ""
echo "2. Cleaning Django migration files..."
run_cmd "find . -path \"*/migrations/*.py\" -not -name \"__init__.py\" -delete"
run_cmd "find . -path \"*/migrations/*.pyc\" -delete"
run_cmd "find . -path \"*/migrations/__pycache__\" -type d -exec rm -rf {} + 2>/dev/null || true"

# 3. Reinstall Django
echo ""
echo "3. Reinstalling Django $DJANGO_VERSION..."
run_cmd "pip uninstall django==$DJANGO_VERSION -y"
run_cmd "pip install django==$DJANGO_VERSION"

# 4. Apply migrations
echo ""
echo "4. Applying Django migrations..."
run_cmd "python manage.py makemigrations"
run_cmd "python manage.py migrate_schemas"

echo ""
echo "============================================================"
echo "ALL OPERATIONS COMPLETED SUCCESSFULLY!"
echo "============================================================"