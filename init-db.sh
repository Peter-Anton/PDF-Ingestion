#!/bin/bash
# init-db.sh — Mounted into postgres /docker-entrypoint-initdb.d/
# Enables the pgvector extension for vector similarity search.

set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";
EOSQL
