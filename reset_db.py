#!/usr/bin/env python3
"""
Automated script to reset database and migrations for Django with PostgreSQL.
Password for PostgreSQL is automatically provided.
"""

import os
import subprocess
import sys
import time

# Configuration
DB_NAME = "eduerpdb_v6"
DB_USER = "postgres"
DB_OWNER = "codefyn"
POSTGRES_PASSWORD = "Jaimaa@007"
DJANGO_VERSION = "4.2.7"
DJANGO_PROJECT_PATH = os.getcwd()  # Current directory, change if needed

def run_command(command, env=None, input_text=None, check=True, shell=True):
    """Run a shell command and return the result."""
    print(f"Running: {command}")
    
    # Set up environment with PostgreSQL password
    process_env = os.environ.copy()
    if env:
        process_env.update(env)
    
    # Always set PGPASSWORD for PostgreSQL commands
    if any(cmd in command for cmd in ['psql', 'dropdb', 'createdb']):
        process_env['PGPASSWORD'] = POSTGRES_PASSWORD
    
    try:
        if input_text:
            result = subprocess.run(
                command,
                shell=shell,
                input=input_text.encode(),
                env=process_env,
                check=check,
                capture_output=True
            )
        else:
            result = subprocess.run(
                command,
                shell=shell,
                env=process_env,
                check=check,
                capture_output=True,
                text=True
            )
        print(f"✓ Success: {command}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"✗ Error running command: {command}")
        print(f"Error output: {e.stderr}")
        return None

def reset_postgresql_database():
    """Reset PostgreSQL database with proper permissions."""
    print("\n" + "="*60)
    print("Resetting PostgreSQL Database")
    print("="*60)
    
    # Connect to PostgreSQL and execute commands
    sql_commands = f"""
DROP DATABASE IF EXISTS {DB_NAME};
CREATE DATABASE {DB_NAME};

\\c {DB_NAME};

-- Give ownership of schema public
ALTER SCHEMA public OWNER TO {DB_OWNER};

-- Give all privileges on the database
GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_OWNER};

-- Give privileges to create tables inside public schema
GRANT ALL ON SCHEMA public TO {DB_OWNER};

-- Optionally allow creating objects in the schema
GRANT CREATE ON SCHEMA public TO {DB_OWNER};
"""
    
    # Execute PostgreSQL commands
    run_command(f'psql -U {DB_USER} -c "DROP DATABASE IF EXISTS {DB_NAME};"')
    run_command(f'psql -U {DB_USER} -c "CREATE DATABASE {DB_NAME};"')
    
    # Connect to the new database and run all commands
    run_command(f'psql -U {DB_USER} -d {DB_NAME} -c "ALTER SCHEMA public OWNER TO {DB_OWNER};"')
    run_command(f'psql -U {DB_USER} -d {DB_NAME} -c "GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_OWNER};"')
    run_command(f'psql -U {DB_USER} -d {DB_NAME} -c "GRANT ALL ON SCHEMA public TO {DB_OWNER};"')
    run_command(f'psql -U {DB_USER} -d {DB_NAME} -c "GRANT CREATE ON SCHEMA public TO {DB_OWNER};"')
    
    print("✓ PostgreSQL database reset complete!")

def clean_django_migrations():
    """Remove Django migration files."""
    print("\n" + "="*60)
    print("Cleaning Django Migration Files")
    print("="*60)
    
    # Delete migration files
    migrations_delete_cmd = 'find . -path "*/migrations/*.py" -not -name "__init__.py" -delete'
    pyc_delete_cmd = 'find . -path "*/migrations/*.pyc" -delete'
    
    run_command(migrations_delete_cmd)
    run_command(pyc_delete_cmd)
    
    # Also delete __pycache__ directories in migrations
    pycache_cmd = 'find . -path "*/migrations/__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true'
    run_command(pycache_cmd)
    
    print("✓ Migration files cleaned!")

def reinstall_django():
    """Reinstall Django to specified version."""
    print("\n" + "="*60)
    print(f"Reinstalling Django {DJANGO_VERSION}")
    print("="*60)
    
    run_command(f"pip uninstall django=={DJANGO_VERSION} -y")
    run_command(f"pip install django=={DJANGO_VERSION}")
    
    print(f"✓ Django {DJANGO_VERSION} reinstalled!")

def apply_migrations():
    """Apply Django migrations to the public schema."""
    print("\n" + "="*60)
    print("Applying Django Migrations")
    print("="*60)
    
    # Make sure we're in the Django project directory
    os.chdir(DJANGO_PROJECT_PATH)
    
    # First create migrations
    run_command("python manage.py makemigrations")
    
    # Apply migrations to public schema
    run_command("python manage.py migrate_schemas")
    
    print("✓ Migrations applied!")

def run_all_commands_in_one_psql_session():
    """Alternative: Run all PostgreSQL commands in a single session."""
    print("\n" + "="*60)
    print("Alternative: Running all PostgreSQL commands in one session")
    print("="*60)
    
    sql_script = f"""DROP DATABASE IF EXISTS {DB_NAME};
CREATE DATABASE {DB_NAME};

\\c {DB_NAME};

ALTER SCHEMA public OWNER TO {DB_OWNER};
GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_OWNER};
GRANT ALL ON SCHEMA public TO {DB_OWNER};
GRANT CREATE ON SCHEMA public TO {DB_OWNER};"""
    
    # Save SQL to temp file and execute
    with open('/tmp/reset_db.sql', 'w') as f:
        f.write(sql_script)
    
    run_command(f'psql -U {DB_USER} -f /tmp/reset_db.sql')
    
    # Clean up temp file
    run_command('rm -f /tmp/reset_db.sql')

def main():
    """Main function to run all operations."""
    print("="*60)
    print("AUTOMATED DATABASE RESET SCRIPT")
    print("="*60)
    print(f"Database: {DB_NAME}")
    print(f"PostgreSQL User: {DB_USER}")
    print(f"Owner: {DB_OWNER}")
    print(f"Django Version: {DJANGO_VERSION}")
    print("="*60)
    
    # Ask for confirmation
    response = input("\nDo you want to proceed? This will reset your database. (y/N): ")
    if response.lower() != 'y':
        print("Operation cancelled.")
        return
    
    try:
        # Step 1: Reset PostgreSQL database
        reset_postgresql_database()
        
        # Step 2: Clean Django migrations
        clean_django_migrations()
        
        # Step 3: Reinstall Django
        reinstall_django()
        
        # Step 4: Apply migrations
        apply_migrations()
        
        print("\n" + "="*60)
        print("ALL OPERATIONS COMPLETED SUCCESSFULLY!")
        print("="*60)
        
    except Exception as e:
        print(f"\n✗ Error occurred: {str(e)}")
        sys.exit(1)

def create_bash_script():
    """Create a bash script alternative."""
    bash_script = f"""#!/bin/bash
# Automated Database Reset Script
# PostgreSQL password will be automatically provided

export PGPASSWORD="{POSTGRES_PASSWORD}"

echo "============================================================"
echo "Resetting PostgreSQL Database"
echo "============================================================"

# Reset database
psql -U {DB_USER} -c "DROP DATABASE IF EXISTS {DB_NAME};"
psql -U {DB_USER} -c "CREATE DATABASE {DB_NAME};"
psql -U {DB_USER} -d {DB_NAME} -c "ALTER SCHEMA public OWNER TO {DB_OWNER};"
psql -U {DB_USER} -d {DB_NAME} -c "GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_OWNER};"
psql -U {DB_USER} -d {DB_NAME} -c "GRANT ALL ON SCHEMA public TO {DB_OWNER};"
psql -U {DB_USER} -d {DB_NAME} -c "GRANT CREATE ON SCHEMA public TO {DB_OWNER};"

echo "============================================================"
echo "Cleaning Django Migration Files"
echo "============================================================"

find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete
find . -path "*/migrations/__pycache__" -type d -exec rm -rf {{}} + 2>/dev/null || true

echo "============================================================"
echo "Reinstalling Django {DJANGO_VERSION}"
echo "============================================================"

pip uninstall django=={DJANGO_VERSION} -y
pip install django=={DJANGO_VERSION}

echo "============================================================"
echo "Applying Django Migrations"
echo "============================================================"

python manage.py makemigrations
python manage.py migrate_schemas

echo "============================================================"
echo "ALL OPERATIONS COMPLETED SUCCESSFULLY!"
echo "============================================================"
"""
    
    with open('reset_database.sh', 'w') as f:
        f.write(bash_script)
    
    # Make it executable
    os.chmod('reset_database.sh', 0o755)
    print("✓ Bash script created: reset_database.sh")
    print("Run with: ./reset_database.sh")

if __name__ == "__main__":
    # Check if user wants bash script instead
    if len(sys.argv) > 1 and sys.argv[1] == "--create-bash":
        create_bash_script()
    else:
        main()