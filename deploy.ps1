#requires -Version 5.1
<#
  Build locally, ship the .output artifact to EC2, swap it into place, restart pm2.
  Windows PowerShell port of deploy.sh (originally written for macOS).

  Run from the repo root:
      .\deploy.ps1

  Requirements on your machine:
    - Node 24+ and npm (build runs locally; .output still runs on the server's Node 20)
    - OpenSSH client on PATH (ssh + scp) — ships with Windows 10/11
      (Settings > System > Optional features > "OpenSSH Client" if missing)

  NOTE: server runtime secrets (AWS creds, AWS_API_BASE, AWS_REGION) and the
  public Cloudflare Turnstile site key are read from frontend/.env at BUILD time
  and baked into .output — the EC2 box has no .env of its own. Build with .env present.

  Differences from the bash original (functionally equivalent):
    - rsync  -> scp. The remote staging dir is wiped first, which is all that
      rsync's --delete was guarding against (it's moved into place each run).
    - The bash key-permission convention is enforced here via icacls, because
      OpenSSH on Windows refuses a private key that other accounts can read.
#>

$ErrorActionPreference = 'Stop'

$Root   = $PSScriptRoot
$Key    = Join-Path $Root 'cosmin.pem'
$Remote = 'ec2-user@ec2-63-183-193-23.eu-central-1.compute.amazonaws.com'

# Shared ssh/scp options (array splat keeps quoting sane on Windows).
$SshOpts = @('-i', $Key, '-o', 'StrictHostKeyChecking=accept-new')

function Assert-LastExit($what) {
    if ($LASTEXITCODE -ne 0) { throw "$what failed (exit code $LASTEXITCODE)" }
}

function Protect-KeyFile($path) {
    # OpenSSH refuses keys that are readable by other accounts
    # ("UNPROTECTED PRIVATE KEY FILE"). Restrict the .pem to the current user.
    if (-not (Test-Path $path)) { throw "SSH key not found: $path" }
    icacls $path /inheritance:r | Out-Null
    icacls $path /grant:r "$($env:USERNAME):(R)" | Out-Null
    foreach ($who in 'BUILTIN\Users', 'Authenticated Users', 'Everyone') {
        # Best-effort: not every account is present on every box.
        cmd /c "icacls `"$path`" /remove `"$who`" >nul 2>&1"
    }
}

# 0. Make sure OpenSSH is available and the key is locked down.
if (-not (Get-Command ssh -ErrorAction SilentlyContinue)) {
    throw "ssh not found on PATH. Install the 'OpenSSH Client' optional feature."
}
Protect-KeyFile $Key

# 1. Production build (Nuxt loads frontend/.env automatically).
Push-Location (Join-Path $Root 'frontend')
try {
    node -v            # expect v24+ locally; output still runs on the server's Node 20
    npm run build
    Assert-LastExit 'npm run build'
}
finally {
    Pop-Location
}

# 2. Upload the fresh build to a staging dir on the server.
#    (Wipe first: scp has no --delete, and a clean dir is moved into place below.)
ssh @SshOpts $Remote 'rm -rf /tmp/output-new'
Assert-LastExit 'remote staging cleanup'

scp @SshOpts -r (Join-Path $Root 'frontend\.output') "${Remote}:/tmp/output-new"
Assert-LastExit 'scp .output'

# 2b. Sync the nginx site config (source of truth lives in deploy/nginx/).
#     Uploaded to a temp path; the remote step backs up the live config, swaps
#     it in, validates with `nginx -t`, and only reloads if the test passes —
#     otherwise it restores the backup so a bad edit can't take the site down.
scp @SshOpts (Join-Path $Root 'deploy\nginx\sterilizari.conf') "${Remote}:/tmp/sterilizari.conf.new"
Assert-LastExit 'scp nginx config'

# 3. Atomically swap into /opt/sterilizari, keep the previous build for rollback,
#    restart pm2, then apply the nginx config (validate-before-reload).
#    Single-quoted here-string: this runs verbatim on the REMOTE shell — keep
#    PowerShell out of its $(...) and ${...}.
$RemoteScript = @'
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
'@

ssh @SshOpts $Remote $RemoteScript
Assert-LastExit 'remote swap/restart'

Write-Host ''
Write-Host 'Deployed. Verify:  curl -I https://sterilizarigratuite.ro'
Write-Host 'Roll back (previous build is kept in /opt/sterilizari-old):'
Write-Host "  ssh -i `"$Key`" $Remote 'sudo mv /opt/sterilizari /opt/sterilizari-bad && sudo mv /opt/sterilizari-old /opt/sterilizari && pm2 restart sterilizari'"
