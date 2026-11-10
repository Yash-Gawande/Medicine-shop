-- Runs once on first container start. Creates the test database used by pytest.
CREATE DATABASE pharmacy_test OWNER pharmacy;
\connect pharmacy
CREATE EXTENSION IF NOT EXISTS pg_trgm;
\connect pharmacy_test
CREATE EXTENSION IF NOT EXISTS pg_trgm;
