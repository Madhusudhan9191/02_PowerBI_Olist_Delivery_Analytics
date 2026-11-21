-- ============================================================================
-- SCRIPT 00: Create Database
-- PROJECT: Olist E-commerce Delivery Performance & Customer Satisfaction
-- ENVIRONMENT: PostgreSQL 16+
-- AUTHOR: Independent Portfolio Project
-- USAGE IN PSQL:
--   psql -U postgres -d postgres -f sql/00_create_database.sql
-- ============================================================================

-- Terminate active connections if recreating
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE datname = 'olist_db' AND pid <> pg_backend_pid();

DROP DATABASE IF EXISTS olist_db;

CREATE DATABASE olist_db
    WITH 
    ENCODING = 'UTF8';

COMMENT ON DATABASE olist_db IS 'Analytical warehouse for Olist E-commerce Delivery Performance & Customer Satisfaction project';
