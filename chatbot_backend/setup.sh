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

# Init django
sudo apt update
sudo apt install python3-venv -y
python3 -m venv env
source env/bin/activate
pip3 install -r requirements.txt

# Init the .env file
sudo echo "# Database configurations
DB_NAME=$db_name
DB_USER=$db_user
DB_PASSWORD=$db_password
DB_HOST=$db_host
DB_PORT=$db_port


# Possible values: DEV, PRE_PROD, PROD
STAGE=PRE_PROD

# Chatbot configurations
MODEL_CONTEXT=32000
PINECONE_API_KEY=pcsk_4pDifc_NrPuZfCHDqT84rtX4zYbbFaFiGAVXweHmiD9FxTdyBpFRnjutcpRehwgmrN5HfS
INDEX_NAME=test-webchatbot
MEMORY_LENGTH=70
SUMMARY_LENGTH=1000
CLOUD=True
DEBUG=False
" > .env


# Create a systemd service file for server. The service name is chatbot.service
sudo echo "[Unit]
Description=Chatbot websocket server
After=network.target

[Service]
Type=simple
User=chatbot
WorkingDirectory=/srv/chatbot
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=/srv/chatbot/.env
ExecStart=/srv/chatbot/venv/bin/python server.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target" > /etc/systemd/system/chatbot.service

sudo systemctl daemon-reload
sudo systemctl enable --now chatbot
sudo systemctl status chatbot