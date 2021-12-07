#!/bin/bash

# This is used as the Customization Script to automate some of the setup on Wikimedia Cloud
# when creating a new instance via Horizon.

# Create a wikiwho user
useradd -m wikiwho
# Set default shell
usermod --shell /bin/bash wikiwho

# Install prerequisites
apt-get install -y python3-dev graphviz libgraphviz-dev pkg-config python3-venv postgresql libpq-dev libxml2-dev libxslt-dev virtualenvwrapper

