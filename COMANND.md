🟦 STEP 1 — Create Project Structure
mkdir my-multitenant-starter
cd my-multitenant-starter

🟦 STEP 2 — Create Virtual Environment
python -m venv .venv
source .venv/Scripts/activate     # Windows

🟦 STEP 3 — Install Required Packages
pip install django psycopg2-binary
pip install django-tenants djangorestframework


❌ Do NOT install django-tenant-users
(because your system uses tenant-isolated users, not shared users)

🟦 STEP 4 — Create Django Project
django-admin startproject config .

🟦 STEP 5 — Create Apps in Correct Locations
python manage.py startapp core
python manage.py startapp tenants
python manage.py startapp users
python manage.py startapp dashboard


Move them manually into apps/ folder:

apps/core
apps/tenants
apps/users
apps/dashboard

🟦 STEP 6 — Create PostgreSQL Database (Correct Script)
psql -U postgres

Create database + user
CREATE DATABASE eduerp_v6;
CREATE USER codefyn WITH PASSWORD 'Jaimaa@007';

ALTER ROLE codefyn SET client_encoding TO 'utf8';
ALTER ROLE codefyn SET default_transaction_isolation TO 'read committed';
ALTER ROLE codefyn SET timezone TO 'Asia/Kolkata';

GRANT ALL PRIVILEGES ON DATABASE eduerp_v6 TO codefyn;
\q

🟦 STEP 7 — Configure Django-Tenants Settings (VERY IMPORTANT)

In config/settings.py:

✔ SHARED_APPS
SHARED_APPS = [
    "django_tenants",
    "django.contrib.contenttypes",
    "django.contrib.admin",

    "apps.tenants",   # tenant model is public
    "apps.core",
]

✔ TENANT_APPS
TENANT_APPS = [
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "apps.users",
    "apps.dashboard",
]

✔ INSTALLED_APPS
INSTALLED_APPS = SHARED_APPS + TENANT_APPS

🟦 STEP 8 — Run PUBLIC Schema Migrations
python manage.py migrate_schemas --schema=public


This creates:

✔ tenants table
✔ domain table
✔ core tables

🟦 STEP 9 — Create Public Tenant (Owner Layer)
python manage.py create_public_tenant

🟦 STEP 10 — Create Domains
python manage.py setup_public_domains


This adds:

localhost

127.0.0.1

public.localhost

🟦 STEP 11 — Create First Tenant
python manage.py create_tenant \
    --schema=abc_school \
    --domain=abc-school.localhost \
    --name="ABC Public School"

🟦 STEP 12 — Run ALL Tenant Migrations
python manage.py migrate_schemas


This will:

✔ Create schema abc_school
✔ Run TENANT_APPS migrations inside abc_school

🟦 STEP 13 — Create Tenant Superuser
python manage.py create_tenant_superuser \
    --tenant=abc_school \
    --email=admin@abcschool.com \
    --password=admin123

🟦 STEP 14 — Add Hosts Entries

Add this manually:

127.0.0.1    public.localhost
127.0.0.1    abc-school.localhost

🟦 STEP 15 — Start Server
python manage.py runserver


Access:

PUBLIC ADMIN (Platform Owner)
http://public.localhost:8000/admin/

TENANT ADMIN
http://abc-school.localhost:8000/admin/