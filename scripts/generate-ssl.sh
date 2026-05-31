#!/bin/bash
# Generate Let's Encrypt SSL certificate using Certbot
# Usage: sudo bash scripts/generate-ssl.sh your-domain.com your@email.com

DOMAIN=${1:-"shield.local"}
EMAIL=${2:-"admin@example.com"}

if [[ "$DOMAIN" == "shield.local" ]]; then
  echo "Generating self-signed certificate for $DOMAIN..."
  mkdir -p docker/nginx/ssl
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout docker/nginx/ssl/shield.key \
    -out docker/nginx/ssl/shield.crt \
    -subj "/CN=$DOMAIN" 2>/dev/null
  echo "Done: docker/nginx/ssl/shield.{crt,key}"
else
  echo "Getting Let's Encrypt certificate for $DOMAIN..."
  docker run --rm \
    -v "$(pwd)/docker/nginx/ssl:/etc/letsencrypt" \
    -p 80:80 \
    certbot/certbot certonly --standalone \
    -d "$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --non-interactive
  cp "docker/nginx/ssl/live/$DOMAIN/fullchain.pem" docker/nginx/ssl/shield.crt
  cp "docker/nginx/ssl/live/$DOMAIN/privkey.pem" docker/nginx/ssl/shield.key
  echo "Certificate installed."
fi
