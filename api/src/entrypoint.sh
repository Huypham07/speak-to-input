#!/bin/bash
set -e

# Wait for databases
echo "Waiting for databases..."
sleep 5

cd /app/alembic

# Migrate Workflow Database (Schema)
echo "Migrating Workflow database schema..."
alembic -c alembic_workflow.ini upgrade head

# Migrate Prism Database (Schema)
echo "Migrating Prism database schema..."
alembic -c alembic_prism.ini upgrade head

echo "All migrations completed."

cd /app

# Start application
exec "$@"
