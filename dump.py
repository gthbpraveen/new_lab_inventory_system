#!/bin/bash

# =============================
# CONFIGURATION - Update these
# =============================
SERVER_USER="lab_user"          # PostgreSQL user on server
SERVER_IP="192.168.50.85"      # Server IP or hostname
SERVER_DB="lab_inventory"       # Database name on server

LOCAL_USER="lab_user"           # Your local PostgreSQL user
LOCAL_DB="lab_inventory"        # Your local database name
LOCAL_DUMP_PATH="$HOME/Downloads/lab_inventory.dump"  # Temp dump file location

# =============================
# Step 1: Dump server database
# =============================
echo "Dumping server database..."
ssh $SERVER_USER@$SERVER_IP "pg_dump -U $SERVER_USER -d $SERVER_DB -F c -b -v -f /tmp/lab_inventory.dump"
if [ $? -ne 0 ]; then
    echo "Error: Failed to dump server database."
    exit 1
fi

# =============================
# Step 2: Copy dump to local
# =============================
echo "Copying dump to local machine..."
scp $SERVER_USER@$SERVER_IP:/tmp/lab_inventory.dump $LOCAL_DUMP_PATH
if [ $? -ne 0 ]; then
    echo "Error: Failed to copy dump from server."
    exit 1
fi

# =============================
# Step 3: Restore dump into local PostgreSQL
# =============================
echo "Restoring dump to local database..."
pg_restore -U $LOCAL_USER -d $LOCAL_DB -v $LOCAL_DUMP_PATH
if [ $? -ne 0 ]; then
    echo "Error: Failed to restore dump to local database."
    exit 1
fi

echo "Database sync complete! ✅"

# Optional: remove dump file
rm -f $LOCAL_DUMP_PATH
0
