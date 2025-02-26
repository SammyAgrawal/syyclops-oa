#!/bin/bash
if [ "$1" = "new" ]; then
    # Create new volume with timestamp
    docker compose up
elif [ -n "$1" ]; then
    # Use specified volume
    DB_VOLUME=$1 docker compose up
else
    echo "Usage: ./start-db.sh [new|volume-name]"
    exit 1
fi