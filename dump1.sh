#!/bin/bash

# =============================
# CONFIGURATION
# =============================
SERVER_USER="praveen"            # SSH user on server
SERVER_IP="192.168.50.85"        # Server IP
SERVER_DB="lab_inventory"        # Server database name
SERVER_PG_USER="lab_user"        # Server PostgreSQL user
SERVER_PG_PASS="admin"           # Server PostgreSQL password

LOCAL_DB="lab_inventory"         # Local database name
LOCAL_PG_USER="lab_user"         # Local PostgreSQL user
LOCAL_PG_PASS="admin"            # Local PostgreSQL password
LOCAL_PG_PORT=5432               # Local PostgreSQL port

SSH_TUNNEL_PORT=5433              # Local port for SSH tunnel

# =============================
# Step 0: Make sure PostgreSQL 14 client is used
# =============================
export PATH=/usr/local/pgsql/bin:$PATH
echo "Using pg_dump version: $(pg_dump --version)"

# =============================
# Step 1: Kill any existing SSH tunnel
# =============================
pkill -f "ssh -L ${SSH_TUNNEL_PORT}:localhost:5432"
sleep 1

# =============================
# Step 2: Drop and recreate local database
# =============================
echo "Dropping local database (if exists)..."
dropdb -U $LOCAL_PG_USER $LOCAL_DB 2>/dev/null
echo "Creating fresh local database..."
createdb -U $LOCAL_PG_USER $LOCAL_DB

# =============================
# Step 3: Start SSH tunnel
# =============================
echo "Starting SSH tunnel..."
ssh -f -N -L ${SSH_TUNNEL_PORT}:localhost:5432 ${SERVER_USER}@${SERVER_IP}
sleep 2

# =============================
# Step 4: Dump & restore database
# =============================
echo "Syncing server DB to local..."
PGPASSWORD=$SERVER_PG_PASS pg_dump -h localhost -p ${SSH_TUNNEL_PORT} -U $SERVER_PG_USER $SERVER_DB | PGPASSWORD=$LOCAL_PG_PASS psql -h localhost -U $LOCAL_PG_USER $LOCAL_DB

# =============================
# Step 5: Close SSH tunnel
# =============================
echo "Closing SSH tunnel..."
pkill -f "ssh -L ${SSH_TUNNEL_PORT}:localhost:5432"

echo "Database sync completed successfully! ✅"
