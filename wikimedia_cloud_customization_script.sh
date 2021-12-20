#!/bin/bash

# This is used as the Customization Script to automate some of the setup on Wikimedia Cloud
# when creating a new instance via Horizon.

# Create a wikiwho user
useradd -m wikiwho
# Set default shell
usermod --shell /bin/bash wikiwho

# Set up the directory structure (except for the pickles, which live on a Cinder volume)
mkdir /home/wikiwho/dumps
chown -R wikiwho /home/wikiwho

mkdir /var/log/django
chown wikiwho /var/log/django

# Install Python prerequisites
apt-get install -y python3-dev graphviz libgraphviz-dev pkg-config python3-venv postgresql libpq-dev libxml2-dev libxslt-dev virtualenvwrapper
# Install production webservice prerequisites
apt-get install -y nginx memcached libcache-memcached-perl libanyevent-perl rabbitmq-server p7zip-full

# Per wiki: Change the swappiness to a lower value to better use of RAM memory and not swap
sysctl -w vm.swappiness=5
echo "vm.swappiness=5" >> /etc/sysctl.conf

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


# Add nginx config and enable it
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
rm /etc/nginx/sites-enabled/default
ln -s /etc/nginx/sites-available/wikiwho /etc/nginx/sites-enabled/wikiwho

# Set up rabbitmq
rabbitmqctl add_user ww_worker ww_worker_password
rabbitmqctl add_vhost ww_vhost
rabbitmqctl set_user_tags ww_worker ww_tag
rabbitmqctl set_permissions -p ww_vhost ww_worker ".*" ".*" ".*"
rabbitmq-plugins enable rabbitmq_management
rabbitmq-server -detached

# Add Celery config
# This is the latest (as of 2021) generic daemon config from the celery/celery repo on GitHub
# See https://github.com/celery/celery/blob/master/extra/generic-init.d/celeryd
curl https://raw.githubusercontent.com/celery/celery/af270f074acdd417df722d9b387ea959b5d9b653/extra/generic-init.d/celeryd -o /etc/init.d/celeryd
chmod 755 /etc/init.d/celeryd

echo """
# CELERY Conf for init script /etc/init.d/celeryd
CELERYD_NODES="worker_default worker_user worker_long"
CELERY_BIN="/home/wikiwho/wikiwho_api/env/bin/celery"
CELERY_APP="wikiwho_api"
CELERYD_CHDIR="/home/wikiwho/wikiwho_api"
CELERYD_OPTS="--hostname=ww_host -Q:worker_default default -c:worker_default 8 -Q:worker_user user -c:worker_user 4 -Q:worker_long long -c:worker_long 4"
CELERYD_LOG_LEVEL="WARNING"
CELERYD_LOG_FILE="/var/log/celery/%n%I.log"
CELERYD_PID_FILE="/var/run/celery/%n.pid"
CELERYD_USER="wikiwho"
CELERYD_GROUP="wikiwho"
CELERY_CREATE_DIRS=1
BROKER_HEARTBEAT=0
""" > /etc/default/celeryd

mkdir /var/log/celery
chown wikiwho /var/log/celery
mkdir /var/run/celery
chown wikiwho /var/run/celery

# Add Flower config for monitoring Celery
# FIXME: This configuration doesn't seem to work; no logs are produced.
echo """
[Unit]
Description=Flower service for monitoring Celery
After=network.target

[Service]
User=wikiwho
Group=www-data
WorkingDirectory=/home/wikiwho/wikiwho_api
ExecStart=/home/wikiwho/wikiwho_api/env/bin/flower --address=localhost --conf='deployment/flower_config.py' --log_file_prefix=/var/log/celery/flower.log --basic_auth=ww_worker:ww_worker_password --broker_api=http://guest:guest@localhost:15672/api/

[Install]
WantedBy=multi-user.target
""" > /etc/systemd/system/ww_flower.service


# Add event-stream listening service
echo """
[Unit]
Description=events_stream daemon
After=network.target

[Service]
User=wikiwho
Group=www-data
WorkingDirectory=/home/wikiwho/wikiwho_api
ExecStart=/home/wikiwho/wikiwho_api/env/bin/python manage.py celery_changed_articles

[Install]
WantedBy=multi-user.target
""" > /etc/systemd/system/ww_events_stream.service

mkdir /var/log/django/events_streamer
chown wikiwho:www-data /var/log/django/events_streamer
