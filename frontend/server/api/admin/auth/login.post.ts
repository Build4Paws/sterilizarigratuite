import {
  cognitoIdp,
  secretHash,
  setAdminSession,
  type CognitoTokens,
} from '~~/server/utils/admin-auth'

/**
 * Admin login. One route, several phases driven by the request body:
 *
 *  1. { email, password }              → InitiateAuth (USER_PASSWORD_AUTH)
 *  2a { email, session, setupCode }    → first-time TOTP enrollment:
 *        VerifySoftwareToken → RespondToAuthChallenge(MFA_SETUP)
 *  2b { email, session, code }         → steady-state TOTP: RespondToAuthChallenge(SOFTWARE_TOKEN_MFA)
 *
 * On success tokens go into httpOnly cookies; they're never in the response body.
 * The Cognito `session` is a short-lived challenge handle (not a credential),
 * safe to round-trip to the client. The TOTP `secretCode` shown during enrollment
 * is the user's own MFA seed — returned over HTTPS for manual entry, never logged
 * and never sent to any third party (no hosted-QR services).
 */
interface AuthResult {
  AuthenticationResult?: {
    IdToken: string
    AccessToken: string
    RefreshToken?: string
    ExpiresIn: number
  }
  ChallengeName?: string
  Session?: string
}

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const region = config.cognitoRegion as string
  const clientId = config.cognitoClientId as string
  const clientSecret = config.cognitoClientSecret as string
  if (!region || !clientId || !clientSecret) {
    throw createError({ statusCode: 500, statusMessage: 'Cognito is not configured.' })
  }

  // Responses can carry a session / TOTP secret — never cache them.
  setResponseHeader(event, 'cache-control', 'no-store')

  const body = (await readBody(event)) as {
    email?: string
    password?: string
    newPassword?: string
    code?: string
    setupCode?: string
    session?: string
  } | null

  const email = String(body?.email ?? '').trim().toLowerCase()
  if (!email) {
    throw createError({ statusCode: 400, statusMessage: 'Email lipsă', data: { error: 'validation_failed' } })
  }
  const hash = secretHash(email, clientId, clientSecret)

  /**
   * Turn an InitiateAuth/RespondToAuthChallenge result into the client response:
   * issue cookies on success, or surface the next challenge step.
   */
  async function finalize(result: AuthResult) {
    // First-time enrollment: register a TOTP secret, then ask the client to confirm it.
    if (result.ChallengeName === 'MFA_SETUP' && result.Session) {
      const assoc = await cognitoIdp<{ SecretCode?: string; Session?: string }>(
        'AssociateSoftwareToken',
        { Session: result.Session },
        region,
      )
      if (!assoc.SecretCode || !assoc.Session) {
        throw createError({ statusCode: 500, statusMessage: 'MFA setup failed', data: { error: 'auth_failed' } })
      }
      const label = encodeURIComponent(`Build4Paws Admin:${email}`)
      return {
        mfaSetupRequired: true,
        session: assoc.Session,
        secretCode: assoc.SecretCode,
        otpauthUri: `otpauth://totp/${label}?secret=${assoc.SecretCode}&issuer=Build4Paws%20Admin`,
      }
    }

    // Steady-state: the user already has a registered authenticator.
    if (result.ChallengeName === 'SOFTWARE_TOKEN_MFA' && result.Session) {
      return { mfaRequired: true, session: result.Session }
    }

    // First sign-in after an invite: the temporary password must be replaced.
    if (result.ChallengeName === 'NEW_PASSWORD_REQUIRED' && result.Session) {
      return { newPasswordRequired: true, session: result.Session }
    }

    // Anything else (NEW_PASSWORD_REQUIRED, …) isn't handled — provision the user fully in Cognito.
    if (result.ChallengeName) {
      throw createError({
        statusCode: 409,
        statusMessage: `Cont incomplet (${result.ChallengeName})`,
        data: { error: 'account_setup_required' },
      })
    }

    const auth = result.AuthenticationResult
    if (!auth?.IdToken) {
      throw createError({ statusCode: 401, statusMessage: 'Autentificare eșuată', data: { error: 'auth_failed' } })
    }
    const tokens: CognitoTokens = {
      idToken: auth.IdToken,
      accessToken: auth.AccessToken,
      refreshToken: auth.RefreshToken,
      expiresIn: auth.ExpiresIn,
    }
    setAdminSession(event, tokens, email)
    return { ok: true }
  }

  // --- Phase 1b: replace the temporary password (first sign-in after invite) ---
  // The result may cascade straight into MFA_SETUP, which `finalize` then handles.
  if (body?.newPassword && body?.session) {
    const result = await cognitoIdp<AuthResult>('RespondToAuthChallenge', {
      ChallengeName: 'NEW_PASSWORD_REQUIRED',
      ClientId: clientId,
      Session: body.session,
      ChallengeResponses: { USERNAME: email, NEW_PASSWORD: body.newPassword, SECRET_HASH: hash },
    }, region)
    return finalize(result)
  }

  // --- Phase 2a: confirm a freshly enrolled TOTP secret ---
  if (body?.setupCode && body?.session) {
    const verify = await cognitoIdp<{ Status?: string; Session?: string }>(
      'VerifySoftwareToken',
      { Session: body.session, UserCode: String(body.setupCode).trim(), FriendlyDeviceName: 'Authenticator' },
      region,
    )
    if (verify.Status !== 'SUCCESS' || !verify.Session) {
      throw createError({ statusCode: 401, statusMessage: 'Cod incorect', data: { error: 'mfa_invalid' } })
    }
    const result = await cognitoIdp<AuthResult>('RespondToAuthChallenge', {
      ChallengeName: 'MFA_SETUP',
      ClientId: clientId,
      Session: verify.Session,
      ChallengeResponses: { USERNAME: email, SECRET_HASH: hash },
    }, region)
    return finalize(result)
  }

  // --- Phase 2b: answer a steady-state TOTP challenge ---
  if (body?.code && body?.session) {
    const result = await cognitoIdp<AuthResult>('RespondToAuthChallenge', {
      ChallengeName: 'SOFTWARE_TOKEN_MFA',
      ClientId: clientId,
      Session: body.session,
      ChallengeResponses: {
        USERNAME: email,
        SOFTWARE_TOKEN_MFA_CODE: String(body.code).trim(),
        SECRET_HASH: hash,
      },
    }, region)
    return finalize(result)
  }

  // --- Phase 1: username + password ---
  if (!body?.password) {
    throw createError({ statusCode: 400, statusMessage: 'Parolă lipsă', data: { error: 'validation_failed' } })
  }
  const result = await cognitoIdp<AuthResult>('InitiateAuth', {
    AuthFlow: 'USER_PASSWORD_AUTH',
    ClientId: clientId,
    AuthParameters: { USERNAME: email, PASSWORD: body.password, SECRET_HASH: hash },
  }, region)
  return finalize(result)
})
