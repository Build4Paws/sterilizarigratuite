#!/usr/bin/env bash
set -euo pipefail

# Build locally, ship the .output artifact to EC2, swap it into place, restart pm2.
# Run from the repo root:  ./deploy.sh
#
# NOTE: server runtime secrets (AWS creds, AWS_API_BASE, AWS_REGION) and the
# public Cloudflare Turnstile site key are read from frontend/.env at BUILD time
# and baked into .output — the EC2 box has no .env of its own. Build with .env present.

ROOT="$(cd "$(dirname "$0")" && pwd)"
KEY="$ROOT/wip1.pem"
HOST="ec2-user@ec2-35-159-120-82.eu-central-1.compute.amazonaws.com"

# 1. Production build (Nuxt loads frontend/.env automatically).
cd "$ROOT/frontend"
node -v   # expect v24+ locally; output still runs on the server's Node 20
npm run build

# 2. Upload the fresh build to a staging dir on the server.
rsync -avz --delete -e "ssh -i $KEY -o StrictHostKeyChecking=accept-new" \
  .output/ "$HOST:/tmp/output-new/"

# 2b. Sync the nginx site config (source of truth lives in deploy/nginx/).
#     Uploaded to a temp path; the remote step backs up the live config, swaps
#     it in, validates with `nginx -t`, and only reloads if the test passes —
#     otherwise it restores the backup so a bad edit can't take the site down.
rsync -avz -e "ssh -i $KEY -o StrictHostKeyChecking=accept-new" \
  "$ROOT/deploy/nginx/sterilizari.conf" "$HOST:/tmp/sterilizari.conf.new"

# 3. Atomically swap into /opt/sterilizari, keep the previous build for rollback,
#    restart pm2, then apply the nginx config (validate-before-reload).
ssh -i "$KEY" -o StrictHostKeyChecking=accept-new "$HOST" '
  set -e
  sudo rm -rf /opt/sterilizari-old
  [ -d /opt/sterilizari ] && sudo mv /opt/sterilizari /opt/sterilizari-old || true
  sudo mv /tmp/output-new /opt/sterilizari
  sudo chown -R ec2-user:ec2-user /opt/sterilizari
  pm2 restart sterilizari
  pm2 save

  # nginx: back up, swap, validate, reload — restore on failure.
  CONF=/etc/nginx/conf.d/sterilizari.conf
  sudo cp "$CONF" "${CONF}.bak.$(date +%Y%m%d-%H%M%S)"
  sudo cp /tmp/sterilizari.conf.new "$CONF"
  if sudo nginx -t; then
    sudo systemctl reload nginx
    echo "nginx config applied and reloaded."
  else
    echo "nginx -t FAILED — restoring previous config, NOT reloading." >&2
    sudo cp "$(ls -1t ${CONF}.bak.* | head -1)" "$CONF"
    exit 1
  fi
'

echo
echo "Deployed. Verify:  curl -I https://dev.sterilizari-gratuite.ro"
echo "Roll back (previous build is kept in /opt/sterilizari-old):"
echo "  ssh -i \"$KEY\" \"$HOST\" 'sudo mv /opt/sterilizari /opt/sterilizari-bad && sudo mv /opt/sterilizari-old /opt/sterilizari && pm2 restart sterilizari'"
