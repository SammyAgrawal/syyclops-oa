#!/bin/bash
if [ "$1" = "new" ]; then
    # Create new volume with timestamp
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    DB_VOLUME=postgres-data-$TIMESTAMP DB_VOLUME_EXTERNAL=false docker compose up
elif [ -n "$1" ]; then
    # Use specified existing volume
    DB_VOLUME=$1 DB_VOLUME_EXTERNAL=true docker compose up
else
    echo "Usage: ./start_service.sh [new|volume-name]"
    exit 1
fi