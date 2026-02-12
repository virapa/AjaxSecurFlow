#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Starting backend entrypoint..."

# Navigate to the backend directory where alembic.ini is located
# The Dockerfile WORKDIR is /app, and the code is in /app/backend
cd /app/backend

# Wait for database to be ready (optional but recommended for robustness)
# Here we just attempt the migration
echo "Running database migrations..."
alembic upgrade head

echo "Database migrations completed successfully."

# Move back to /app if needed, though uvicorn can run from /app
cd /app

# Execute the CMD passed to docker run
echo "Starting application server..."
exec "$@"
