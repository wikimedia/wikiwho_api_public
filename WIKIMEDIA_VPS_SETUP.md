1. Create a VPS on horizon.wikimedia.org
   * 24 core, 122GB RAM machine
   * Debian 11
   * `webservice` security group
   * Paste or upload Customization Script: `wikimedia_cloud_customization_script.sh`

2. SSH into the VPS
3. Transfer the wikiwho_api codebase to the VPS and copy it to `/home/wikiwho`. (FIXME: Use git once the repo is public.)
   1. Zip it into wikiwho_api.zip
   2. From home: `scp wikiwho_api.zip ragesoss@wikiwho-api:/home/ragesoss`
   3. On the VPS: `sudo mv wikiwho_api.zip /home/wikiwho`

4. Create the wikiwho postgres user and database:
   1. `sudo su postgres`
   2. `psql`
      1. `create user wikiwho with password 'wikiwho';`
      2. `create database wikiwho;`
      3. `grant all privileges on database wikiwho to wikiwho;`
      4. `exit;`
   3. `exit`
5. Become the wikiwho user: `sudo su wikiwho`
6. `cd /home/wikiwho`
7. `unzip wikiwho_api.zip`
8. Create the directory structure for the pickles and dumps:
9.  `cd wikiwho_api`
10.  Set up a virtualenv:
   1. `python -m venv env`
   2. `. env/bin/activate`
11.  Install the Python dependencies: `pip install -r requirements.txt -r requirements_local.txt -r requirements_test.txt`
12.  Generate a secret key: `python manage.py generate_secret_key`
13.  Create `wikiwho_api/settings.py` (in the wikiwho_api subdirectory, not the top git directory), with an import from one of the environment-specific settings files plus SECRET_KEY, WP_CONSUMER_TOKEN, WP_CONSUMER_SECRET, WP_ACCESS_TOKEN, WP_ACCESS_SECRET, and DATABASES (at least).
14. `python manage.py migrate`
15. `python manage.py collectstatic --noinput -c`
16. As a user with sudo, start the Gunicorn webserver:
    1.  `sudo systemctl enable ww_gunicorn`
    2.  `sudo systemctl start ww_gunicorn`
    3.  `sudo systemctl status ww_gunicorn` to check if it's running
