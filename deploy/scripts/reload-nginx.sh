#!/bin/bash
# Post-renewal hook for Certbot
# Location: /etc/letsencrypt/renewal-hooks/post/reload-nginx.sh
# chmod +x this file

systemctl reload nginx
systemctl reload gunicorn || true
