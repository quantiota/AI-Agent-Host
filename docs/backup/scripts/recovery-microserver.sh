#!/bin/bash


# Step 1: Validate input
if [ -z "$SELECTED_BACKUP" ]; then
    echo "Error: SELECTED_BACKUP variable is not set."
    exit 1
fi

# Step 2: Remove old directories
rm -rf /home /opt

# Step 3: Restore from the selected hourly backup
cp -pr "/backup/rsnapshot/$SELECTED_BACKUP/localhost/home" /
cp -pr "/backup/rsnapshot/$SELECTED_BACKUP/localhost/opt" /

# Step 4: Get the invoking user's home directory
USER_HOME=$(eval echo "~$SUDO_USER")

# Step 5: Change directory to where docker-compose.yml is located
cd "$USER_HOME/AI-Agent-Lab/docker" || exit

# Step 6: Rebuild and start Docker containers
docker compose up --build -d

