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

4. Become the wikiwho user: `sudo su wikiwho`
5. `cd /home/wikiwho`
6. `unzip wikiwho_api.zip`
7. `cd wikiwho_api`
8. Set up a virtualenv:
   1. `python3 -m venv env`
   2. `. env/bin/activate`
9. Install the Python dependencies: `pip3 install -r requirements.txt -r requirements_local.txt -r requirements_test.txt`
