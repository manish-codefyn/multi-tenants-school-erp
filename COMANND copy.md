
mkdir my-multitenant-starter
cd my-multitenant-starter

python -m venv .venv
source .venv/scripts/activate
pip install django psycopg2-binary
pip install django django-tenants django-tenant-users djangorestframework
django-admin startproject config .


python manage.py startapp core  apps/core
python manage.py startapp tenant apps/tenant
python manage.py startapp  users apps/users
python manage.py startapp dashboard apps/dashboard


# Create database (make sure PostgreSQL is running)
 1. psql -U postgres

-- Create a new database
CREATE DATABASE eduerp_db_v6;

-- Create a new user
CREATE USER codefyn WITH PASSWORD 'Jaimaa@007';

-- Configure user defaults (recommended)
ALTER ROLE codefyn SET client_encoding TO 'utf8';
ALTER ROLE codefyn SET default_transaction_isolation TO 'read committed';
ALTER ROLE codefyn SET timezone TO 'Asia/Kolkata';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE eduerp_db TO codefyn;
\q

1. psql -U postgres
DROP DATABASE eduerpdb_v6;
CREATE DATABASE eduerpdb_v6;

\c eduerpdb_v6;

-- Give ownership of schema public

ALTER SCHEMA public OWNER TO codefyn;

-- Give all privileges on the database
GRANT ALL PRIVILEGES ON DATABASE eduerpdb_v6 TO codefyn;

-- Give privileges to create tables inside public schema
GRANT ALL ON SCHEMA public TO codefyn;

-- Optionally allow creating objects in the schema
GRANT CREATE ON SCHEMA public TO codefyn;
\q

# 1. Apply to public schema first
python manage.py migrate_schemas --schema=public

# 2. Create a tenant to test
python manage.py create_tenant --schema=test --domain=test.localhost --name="Test Tenant"

# 3. Apply migrations to all tenants
python manage.py migrate_schemas


# In Django shell or management command
# TO LAOD DATA  INITIALS
# Create new organization
python manage.py load_all_tenant_data
or
python manage.py setup_tenants
or
python manage.py setup_public_domains



 python manage.py setup_tenants
🚀 Starting Complete System Setup...
==================================================

📋 Step 1: Setting up Public Tenant...
←[32;1m   ✅ Public tenant exists: public←[0m
←[33;1m   ⚠️ Domain exists: localhost←[0m
←[33;1m   ⚠️ Domain exists: 127.0.0.1←[0m
←[33;1m   ⚠️ Domain exists: public.localhost←[0m

📦 Step 2: Creating Modules in Public Schema...
←[31;1m   ❌ Error creating modules: Unknown command: 'create_public_modules'←[0m

🏫 Step 3: Loading Tenant Data...
←[33;1m⚠️  Skipping ABC Public School - already exists←[0m
←[33;1m⚠️  Skipping XYZ College of Engineering - already exists←[0m
←[32;1m
🎉 Successfully created 0 tenants with all data, skipped 2←[0m
←[32;1m   ✅ Tenant data loaded successfully←[0m
==================================================
←[32;1m🎉 System Setup Complete!←[0m

============================================================
←[32;1m🏫 TENANT INFORMATION←[0m
============================================================

←[32;1m1. ABC Public School←[0m
   ←[33;1m🌐 URL:←[0m     http://abc-school.localhost:8000/
   ←[33;1m👤 Admin:←[0m   admin@abcschool.com
   ←[33;1m🔑 Password:←[0m admin123
   ←[33;1m🎨 Theme:←[0m   Blue (#3B82F6)

←[32;1m2. XYZ College of Engineering←[0m
   ←[33;1m🌐 URL:←[0m     http://xyz-college.localhost:8000/
   ←[33;1m👤 Admin:←[0m   admin@xyzcollege.com
   ←[33;1m🔑 Password:←[0m admin123
   ←[33;1m🎨 Theme:←[0m   Green (#10B981)

←[32;1m3. Public Schema←[0m
   ←[33;1m🌐 URL:←[0m     http://localhost:8000/admin/
   ←[33;1m👤 Admin:←[0m   admin@public.com
   ←[33;1m🔑 Password:←[0m admin123
   ←[33;1m🎨 Theme:←[0m   Default

============================================================
←[32;1m🔧 SETUP INSTRUCTIONS←[0m
============================================================

1. Add to your hosts file:
   127.0.0.1   abc-school.localhost
   127.0.0.1   xyz-college.localhost
   127.0.0.1   public.localhost

2. Access the URLs above in your browser

3. Use the admin credentials to login

←[32;1m🚀 Your multi-tenant system is ready to use!←[0m

# Load all data
python manage.py load_dummy_data --schema=abc_public_school
or
# Load only courses
python manage.py load_courses --schema=abc_public_school
or
# Load only subjects
python manage.py load_subjects --schema=abc_public_school
or
# Load only fees
python manage.py load_fees --schema=abc_public_school
or
# Load with custom file
python manage.py load_courses --schema=abc_public_school --file=academics/my_courses.json

# Using tenant code (if available)
python manage.py createsuperuser_tenant --email=admin@xyzce.com --tenant=xyz_college_of_engineering --password=admin123 --first-name=College --last-name=Admin

python manage.py listtenantsuperusers

# Filter by tenant
python manage.py listtenantsuperusers --tenant="XYZ College of Engineering"

# JSON output
python manage.py listtenantsuperusers --format=json

# CSV output  
python manage.py listtenantsuperusers --format=csv


# Add specific permission
python manage.py updatetenantpermissions --email=admin@codfyn.com --tenant=3 --add-permission=can_manage_library --add-permission=can_manage_hostel

# Remove permission
python manage.py updatetenantpermissions --email=admin@codfyn.com --tenant=3 --remove-permission=can_manage_finances

# Reset to default
python manage.py updatetenantpermissions --email=admin@codfyn.com --tenant=3 --reset-permissions

<!-- tenent access -->

python manage.py checktenantaccess --email=admin@codfyn.com --tenant=3

# 1. Create public tenant
python manage.py create_public_tenant

# 2. Setup public domains (your existing command)


# 3. Run migrations for all tenants
python manage.py migrate_schemas


# Now run the manual setup


python manage.py runserver




option public 
python setup_public_tenant.py

  Access the public site:
http://localhost:8000/

Create a new organization:

Click "Sign Up"

Fill in the form

You should be redirected to your new tenant's dashboard

Access existing tenants directly:

http://demo.localhost:8000/

http://test.localhost:8000/

F. Quick Fix for Current Issue
If you're still getting the 404 error, try accessing these URLs directly:

Go to the login page directly:
http://demo.localhost:8000/accounts/login/

Login with:

Email: admin@demo.com

Password: demopassword123

You should be redirected to:
http://demo.localhost:8000/dashboard/

The main issues were:

Missing authentication URLs in tenant schemas

Incorrect login redirects

Template path issues

Missing session configuration

back all db 
pg_dump -U postgres -Fc -d eduerp_db -f backup_$(date +%F).dump

pg_dump -U postgres -Fc -d eduerp_db -f multitenant_backup.dump

pg_dump -U postgres -n demo -d eduerp_db -f demo_schema.sql



pg_dump -U postgres -n codefyn_solutions -n codefyn_solutions1 -n demo -n ss_solutions -d eduerp_db -f tenants_backup.sql

This should now work properly!

find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete

pip uninstall django==4.2.7 
pip install django==4.2.7 


