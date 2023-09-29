#!/usr/bin/env bash
systemctl restart ww_celery.service
systemctl restart ww_flower.service
systemctl restart ww_events_stream.service
systemctl restart ww_events_stream_deletion.service
