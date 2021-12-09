#!/bin/bash

# This is used as the Customization Script to automate some of the setup on Wikimedia Cloud
# when creating a new instance via Horizon.

# Create a wikiwho user
useradd -m wikiwho
# Set default shell
usermod --shell /bin/bash wikiwho

# Set up the directory structure
mkdir -p /home/wikiwho/p_disk/{en,eu,es,de,tr}
mkdir /home/wikiwho/dumps
chown -R wikiwho /home/wikiwho

mkdir /var/log/django
chown wikiwho /var/log/django

# Install Python prerequisites
apt-get install -y python3-dev graphviz libgraphviz-dev pkg-config python3-venv postgresql libpq-dev libxml2-dev libxslt-dev virtualenvwrapper
# Install production webservice prerequisites
apt-get install -y nginx memcached libcache-memcached-perl libanyevent-perl

# Per wiki: Change the swappiness to a lower value to better use of RAM memory and not swap
sysctl -w vm.swappiness=5

# Add gunicorn service
echo """
[Unit]
Description=gunicorn daemon for wikiwho api
After=network.target

[Service]
User=wikiwho
Group=www-data
WorkingDirectory=/home/wikiwho/wikiwho_api
ExecStart=/home/wikiwho/wikiwho_api/env/bin/gunicorn --config /home/wikiwho/wikiwho_api/deployment/gunicorn_config.py wikiwho_api.wsgi:application

[Install]
WantedBy=multi-user.target
""" > /etc/systemd/system/ww_gunicorn.service

echo """
server {
    listen 80;
    server_name wikiwho.toolforge.org;

    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;

    access_log off;  # turn off access log
    root /home/wikiwho/wikiwho_api;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static {
            root /home/wikiwho/wikiwho_api;
    }

    location / {
            include proxy_params;
            proxy_pass http://unix:/home/wikiwho/wikiwho_api/ww_api_gunicorn.sock;
            proxy_read_timeout 360s;  # default is 60s
    }
}
""" > /etc/nginx/sites-available/wikiwho
