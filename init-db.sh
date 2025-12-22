#!/bin/bash
set -e

# This script runs automatically when PostgreSQL container starts for the first time

echo "Creating readonly user..."

# Create readonly user
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create readonly user
    CREATE USER readonly_user WITH PASSWORD 'readonly_password';
    
    -- Grant CONNECT privilege
    GRANT CONNECT ON DATABASE $POSTGRES_DB TO readonly_user;
    
    -- Grant USAGE on public schema
    GRANT USAGE ON SCHEMA public TO readonly_user;
    
    -- Grant SELECT on all existing tables
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
    
    -- Grant SELECT on all future tables (for tables created by migrations)
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly_user;
    
    -- Revoke all other privileges (just to be explicit)
    REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA public FROM readonly_user;
    
    -- Make sure user cannot create objects
    REVOKE CREATE ON SCHEMA public FROM readonly_user;
EOSQL

echo "Readonly user created successfully!"
echo "Username: readonly_user"
echo "Password: readonly_password"
echo "Permissions: SELECT only"