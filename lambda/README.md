# API Lambda (`process-user-data`)

The single Python Lambda behind the API Gateway HTTP API — all public, magic-link
and admin routes for sterilizari-gratuite.ro. Lives here so it's versioned with
the frontend that calls it.

```
lambda/
├── lambda_function.py   # thin entry — re-exports api.router.lambda_handler
├── api/                 # the implementation package
│   ├── config.py        # env vars, per-environment selection, constants, active-env state
│   ├── helpers.py       # DB, HTTP responses, security/captcha, tokens, email, SMS
│   ├── models.py        # Pydantic request models + validation-error mapping
│   ├── public_handlers.py  # public + magic-link route handlers
│   ├── admin.py         # admin auth helpers + admin route handlers
│   ├── reports.py       # admin CSV report handlers
│   └── router.py        # ROUTES/DISPATCH + lambda_handler (env select, admin gate)
├── email_templates.py   # branded transactional emails (organizer + citizen)
├── sms_templates.py     # short SMS bodies (messengeros)
├── migrations/          # one-off SQL migrations (run manually against RDS)
├── requirements.txt     # psycopg, pydantic, email-validator (boto3 is in the runtime)
├── deploy.sh            # build matching-platform wheels + bundle api/ + update-function-code
└── .env.example         # documents the function's env vars (no secrets)
```

The AWS handler is still `lambda_function.lambda_handler` (unchanged function
config). Cross-module shared state (the active environment) lives only in
`config` behind `set_active_env()` / `current_env()` / `current_origin()`.

## Deploy

```bash
./lambda/deploy.sh
```

Needs an authenticated `aws` CLI, `python3`, `pip`, `zip`. The script reads the
function's **current runtime + architecture** from AWS and bundles dependency
wheels that match it, so you never ship a mac-built binary to Linux. It updates
**code only** — never environment variables.

Override the target if needed:

```bash
LAMBDA_FUNCTION_NAME=process-user-data AWS_REGION=eu-central-1 ./lambda/deploy.sh
```

Function ARN: `arn:aws:lambda:eu-central-1:873372010066:function:process-user-data`

## Environment variables

See [`.env.example`](./.env.example). Secrets (DB passwords, `TOKEN_PEPPER`,
`TURNSTILE_SECRET`) should be backed by Secrets Manager / SSM, not literal
values. `deploy.sh` does not manage these; set them in the console or via a
separate, reviewed `update-function-configuration` call.

## Captcha = Cloudflare Turnstile

Verification happens **here**, server-side, in `verify_turnstile()` (Cloudflare
`siteverify`). The frontend renders the Turnstile widget and forwards the token
(`turnstileToken` in the request body) through the Nuxt proxy unchanged — the
secret never leaves the Lambda.

- Set `TURNSTILE_SECRET` to the secret that pairs with the frontend's public
  site key (`NUXT_PUBLIC_TURNSTILE_SITE_KEY`).
- For a non-breaking cutover the code also accepts the legacy `HCAPTCHA_SECRET`
  / `HCAPTCHA_ENABLED` names as a fallback, so you can deploy the code first and
  rename the env vars after.
- A failed/blank token returns `400 captcha_failed` (the frontend maps that to
  Romanian copy).
