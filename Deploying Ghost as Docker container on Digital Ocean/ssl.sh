#!/bin/bash
sudo certbot certonly \
    -d nonsense.fyi \
    -d www.nonsense.fyi \
    --dns-cloudflare \
    --dns-cloudflare-credentials /home/roxedus/cf-creds.ini
sudo nginx -s reload