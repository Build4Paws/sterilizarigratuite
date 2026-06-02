#!/usr/bin/env bash
set -euo pipefail

# Build locally, ship the .output artifact to EC2, swap it into place, restart pm2.
# Run from the repo root:  ./deploy.sh
#
# NOTE: server runtime secrets (AWS creds, AWS_API_BASE, AWS_REGION) and the
# public hCaptcha site key are read from frontend/.env at BUILD time and baked
# into .output — the EC2 box has no .env of its own. Build with .env present.

ROOT="$(cd "$(dirname "$0")" && pwd)"
KEY="$ROOT/cosmin.pem"
HOST="ec2-user@ec2-63-183-193-23.eu-central-1.compute.amazonaws.com"

# 1. Production build (Nuxt loads frontend/.env automatically).
cd "$ROOT/frontend"
node -v   # expect v24+ locally; output still runs on the server's Node 20
npm run build

# 2. Upload the fresh build to a staging dir on the server.
rsync -avz --delete -e "ssh -i $KEY -o StrictHostKeyChecking=accept-new" \
  .output/ "$HOST:/tmp/output-new/"

# 3. Atomically swap into /opt/sterilizari, keep the previous build for rollback,
#    and restart the pm2 process.
ssh -i "$KEY" -o StrictHostKeyChecking=accept-new "$HOST" '
  set -e
  sudo rm -rf /opt/sterilizari-old
  [ -d /opt/sterilizari ] && sudo mv /opt/sterilizari /opt/sterilizari-old || true
  sudo mv /tmp/output-new /opt/sterilizari
  sudo chown -R ec2-user:ec2-user /opt/sterilizari
  pm2 restart sterilizari
  pm2 save
'

echo
echo "Deployed. Verify:  curl -I https://sterilizarigratuite.ro"
echo "Roll back (previous build is kept in /opt/sterilizari-old):"
echo "  ssh -i \"$KEY\" \"$HOST\" 'sudo mv /opt/sterilizari /opt/sterilizari-bad && sudo mv /opt/sterilizari-old /opt/sterilizari && pm2 restart sterilizari'"
