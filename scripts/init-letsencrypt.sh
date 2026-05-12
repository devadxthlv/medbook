#!/bin/bash
# init-letsencrypt.sh
# Automates the creation of dummy certificates and then fetches real Let's Encrypt certificates.

if ! [ -x "$(command -v docker-compose)" ] && ! [ -x "$(command -v docker)" ]; then
  echo 'Error: docker or docker-compose is not installed.' >&2
  exit 1
fi

COMPOSE_FILE="docker-compose.prod.yml"
DOMAINS=("3-27-246-227.nip.io" "medbook.3-27-246-227.nip.io" "3.27.246.227.nip.io") # Using nip.io for wildcard DNS routing to our EC2 IP
RSA_KEY_SIZE=4096
DATA_PATH="./certbot"
EMAIL="admin@3-27-246-227.nip.io"
STAGING=0 # Set to 1 if testing to avoid Let's Encrypt rate limits

if [ -d "$DATA_PATH/conf/live/$DOMAINS" ]; then
  echo "### Existing data found for ${DOMAINS[*]}. Proceeding with replacement..."
fi

if [ ! -e "$DATA_PATH/conf/options-ssl-nginx.conf" ] || [ ! -e "$DATA_PATH/conf/ssl-dhparams.pem" ]; then
  echo "### Downloading recommended TLS parameters ..."
  mkdir -p "$DATA_PATH/conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "$DATA_PATH/conf/options-ssl-nginx.conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "$DATA_PATH/conf/ssl-dhparams.pem"
  echo
fi

echo "### Creating dummy certificate for ${DOMAINS[*]} ..."
path="/etc/letsencrypt/live/$DOMAINS"
mkdir -p "$DATA_PATH/conf/live/$DOMAINS"
docker compose -f $COMPOSE_FILE run --rm --entrypoint "\
  openssl req -x509 -nodes -newkey rsa:$RSA_KEY_SIZE -days 1\
    -keyout '$path/privkey.pem' \
    -out '$path/fullchain.pem' \
    -subj '/CN=localhost'" certbot
echo

echo "### Starting nginx ..."
docker compose -f $COMPOSE_FILE up --force-recreate -d nginx
echo

echo "### Deleting dummy certificate for ${DOMAINS[*]} ..."
docker compose -f $COMPOSE_FILE run --rm --entrypoint "\
  rm -Rf /etc/letsencrypt/live/$DOMAINS && \
  rm -Rf /etc/letsencrypt/archive/$DOMAINS && \
  rm -Rf /etc/letsencrypt/renewal/$DOMAINS.conf" certbot
echo

echo "### Requesting Let's Encrypt certificate for ${DOMAINS[*]} ..."
domain_args=""
for domain in "${DOMAINS[@]}"; do
  domain_args="$domain_args -d $domain"
done

case "$EMAIL" in
  "") email_arg="--register-unsafely-without-email" ;;
  *) email_arg="--email $EMAIL" ;;
esac

if [ $STAGING != "0" ]; then staging_arg="--staging"; fi

docker compose -f $COMPOSE_FILE run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    $staging_arg \
    $email_arg \
    $domain_args \
    --rsa-key-size $RSA_KEY_SIZE \
    --agree-tos \
    --force-renewal \
    --non-interactive" certbot
echo

echo "### Reloading nginx ..."
docker compose -f $COMPOSE_FILE exec nginx nginx -s reload
