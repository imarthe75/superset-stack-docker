#!/bin/bash

# Function to create user
create_user() {
  local username=$1
  local firstname=$2
  local lastname=$3
  local email=$4

  echo "Creating user: $username ($firstname $lastname)"
  docker exec superset-project-superset-1 superset fab create-user \
    --username "$username" \
    --firstname "$firstname" \
    --lastname "$lastname" \
    --email "$email" \
    --password "password" \
    --role "Gamma"
}

# Create users
create_user "ana.mendez" "Ana" "Mendez" "ana.mendez@example.com"
create_user "carlos.ruiz" "Carlos" "Ruiz" "carlos.ruiz@example.com"
create_user "luisa.fernandez" "Luisa" "Fernandez" "luisa.fernandez@example.com"
create_user "jorge.santos" "Jorge" "Santos" "jorge.santos@example.com"
create_user "maria.gomez" "Maria" "Gomez" "maria.gomez@example.com"
create_user "pedro.lopez" "Pedro" "Lopez" "pedro.lopez@example.com"

echo "All users created."
