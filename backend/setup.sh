#!/bin/bash
# This script sets up the Django project, migrates the database, creates a superuser, and starts the Gunicorn server. It also creates a systemd service for Gunicorn to run on startup.
# FIXME: Do not use this script in production. It is for deployement testing purposes only. In production, use a more secure method to set environment variables and manage secrets.
# Command line arguments: admin_username, admin_password, db_name, db_user, db_password, db_host, db_port, secret_key, allowed_origins

admin_username=$1
admin_password=$2
db_name=$3
db_user=$4
db_password=$5
db_host=$6
db_port=$7
secret_key=$8
allowed_origins=$9

tax=0.1

# Init django
python3 -m venv env
source env/bin/activate
pip3 install -r requirements.txt
cd restaurantAPI

# Init the .env file
echo "# Database configurations
DB_NAME=$db_name
DB_USER=$db_user
DB_PASSWORD=$db_password
DB_HOST=$db_host
DB_PORT=$db_port

SECRET_KEY='$secret_key'


# Allowed host and origins
ALLOWED_ORIGINS=$allowed_origins



# BUSINESS CUSTOMIZATION
TAX=$tax" > ./restaurantAPI/.env

# migrate database
python3 manage.py makemigrations
python3 manage.py migrate

# Create a superuser
export DJANGO_SUPERUSER_USERNAME=$admin_username
export DJANGO_SUPERUSER_EMAIL=$admin_username@example.com
export DJANGO_SUPERUSER_PASSWORD=$admin_password
python3 manage.py shell -c "
from django.contrib.auth import get_user_model
import os
U = get_user_model()
# Check if the superuser already exists before creating it
if not U.objects.filter(username=os.environ['DJANGO_SUPERUSER_USERNAME']).exists():
    U.objects.create_superuser(
        os.environ['DJANGO_SUPERUSER_USERNAME'],
        os.environ['DJANGO_SUPERUSER_EMAIL'],
        os.environ['DJANGO_SUPERUSER_PASSWORD'],
    )
"





# Set gunicorn to run on startup (for Linux systems)
# Create a systemd service file for gunicorn. The service name is restaurantAPI.service
sudo echo "[Unit]
Description=Gunicorn for restaurantAPI
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/srv/Restaurant-full-stack-project/backend/restaurantAPI
EnvironmentFile=/srv/Restaurant-full-stack-project/backend/restaurantAPI/restaurantAPI/.env
ExecStart=/srv/Restaurant-full-stack-project/backend/env/bin/gunicorn restaurantAPI.wsgi:application -c gunicorn.conf.py
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3
KillMode=mixed

[Install]
WantedBy=multi-user.target" > /etc/systemd/system/restaurantAPI.service

sudo systemctl daemon-reload
sudo systemctl enable --now restaurantAPI
sudo systemctl status restaurantAPI