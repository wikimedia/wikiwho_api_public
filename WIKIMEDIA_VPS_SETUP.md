1. Create a VPS on horizon.wikimedia.org
   * 24 core, 122GB RAM machine
   * Debian 11
   * `webservice` security group
   * Paste or upload Customization Script: `wikimedia_cloud_customization_script.sh`
2. Configure a Cinder volume on horizon.wikimedia.org
   * 5000 GB
   * attach to the VPS
3. Add a Web Proxy on Horizon (`wikiwho-api.wmcloud.org` or something else from the `settings_wmcloud.py` hosts entry)
4. SSH into the VPS
5. Prepare the Cinder volume.
   1. `sudo wmcs-prepare-cinder-volume`
   2. mount it to `/pickles`
   3. `sudo mkdir -p /pickles/{en,eu,es,de,tr}`
   4. `sudo chown -R wikiwho /pickles`
6. Transfer the wikiwho_api codebase to the VPS and copy it to `/home/wikiwho`. (FIXME: Use git once the repo is public.)
   1. Zip it into wikiwho_api.zip
   2. From home: `scp wikiwho_api.zip ragesoss@wikiwho-api:/home/ragesoss`
   3. On the VPS: `sudo mv wikiwho_api.zip /home/wikiwho`

7. Create the wikiwho postgres user and database:
   1. `sudo su postgres`
   2. `psql`
      1. `create user wikiwho with password 'wikiwho';`
      2. `create database wikiwho;`
      3. `grant all privileges on database wikiwho to wikiwho;`
      4. `exit;`
   3. `exit`
8. Become the wikiwho user: `sudo su wikiwho`
9.  `cd /home/wikiwho`
10. `unzip wikiwho_api.zip`
11. `cd wikiwho_api`
12.  Set up a virtualenv:
   1. `python3 -m venv env`
   2. `. env/bin/activate`
13.  Install the Python dependencies: `pip install -r requirements.txt -r requirements_local.txt -r requirements_test.txt`
14.  Create `wikiwho_api/settings.py` (in the wikiwho_api subdirectory, not the top git directory), with an import from `settings_wmcloud` plus SECRET_KEY, WP_CONSUMER_TOKEN, WP_CONSUMER_SECRET, WP_ACCESS_TOKEN, WP_ACCESS_SECRET, and DATABASES.
     1. Generate a secret key: `python manage.py generate_secret_key`
15. `python manage.py migrate`
16. `python manage.py collectstatic --noinput -c`
17. As a user with sudo, start the Gunicorn webserver:
    1.  `sudo systemctl enable ww_gunicorn`
    2.  `sudo systemctl start ww_gunicorn`
    3.  `sudo systemctl status ww_gunicorn` to check if it's running
    4.  API and homepage should be working now.
18. Start Celery:
    1.  `sudo /etc/init.d/celeryd start`
19. Import dumps (as user `wikiwho`)
    1.  `sudo su wikiwho`
    2.  `mkdir -p /pickles/{en,eu,es,de,tr}`
    3.  Download the latest dumps for each of the languages to import, eg:
        1.  `cd `/pickles/dumps/en`
        2.  `wget -r -np -nd -c -A 7z https://dumps.wikimedia.your.org/enwiki/20211201/`
    4.  For each language, generate pickles from the XML dumps, eg:
        1.  `cd ~/wikiwho_api`
        2.  `. env/bin/activate`
        1.  `nohup python manage.py generate_articles_from_wp_xmls -p '/pickles/dumps/en/' -t 30 -m 24 -lang en -c
20. Start Flower and event_stream services
    1.  `sudo systemctl enable ww_flower.service`
    2.  `sudo systemctl start ww_flower.service`
    3.  `sudo systemctl status ww_flower.service` to check if it's running
    4.  `sudo systemctl enable ww_events_stream.service`
    5.  `systemctl start ww_events_stream.service`
    6.  `systemctl status ww_events_stream.service` to check if it's running