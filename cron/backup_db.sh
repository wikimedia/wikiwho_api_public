#!/bin/bash
HOSTNAME="localhost"
USERNAME="postgres"

function perform_backups()
{
    BACKUP_DIR="/home/wikiwho/db_disk/postgres_backups/ww_api_live/"
    if ! mkdir -p $BACKUP_DIR; then
        echo "Cannot create backup directory in $BACKUP_DIR. Go and fix it!" 1>&2
        exit 1;
    fi;

    BACKUP_FILE=$BACKUP_DIR"/`date +\%Y-\%m-\%d`-"
    DB_LIST="ww_api_live"  # comma separated
    for DATABASE in ${DB_LIST//,/ }
    do
        if ! pg_dump -Fp -h "$HOSTNAME" -U "$USERNAME" "$DATABASE" | gzip > $BACKUP_FILE"$DATABASE".sql.gz.in_progress; then
            echo "[!!ERROR!!] Failed to produce plain backup database $DATABASE" 1>&2
        else
            rm -f $BACKUP_DIR*.sql.gz  # delete old one when new one is created
            mv $BACKUP_FILE"$DATABASE".sql.gz.in_progress $BACKUP_FILE"$DATABASE".sql.gz  # rename new one
        fi
    done

    echo -e "\nAll database backups complete!"
}

perform_backups
