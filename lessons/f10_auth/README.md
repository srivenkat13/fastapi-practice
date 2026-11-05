# F10 · Auth: password hashing, JWT, current user, roles

> This is where interviewers look for **security judgement**. Use a slow salted hash, pin the JWT algorithm, never trust client-provided identity, return the same error for "no such user" and "wrong password", and authorize on the server **every time**.

## 🧠 Concepts

### Three separate jobs
| | Question | Here |
|---|---|---|
| Authentication | who are you? | `POST /auth/token` checks the password and issues a JWT |
| Session/token | remember them | `Authorization: Bearer <jwt>` on each request |
| Authorization | may they do this? | `require_role("admin")`, ownership checks in queries |

### Password hashing
```python
from pwdlib import PasswordHash
ph = PasswordHash.recommended()        # Argon2id
ph.hash("pw") → "$argon2id$v=19$m=65536,t=3,p=4$<salt>$<hash>"
ph.verify("pw", stored)
```
Never use plaintext, MD5/SHA-256 (too fast, so they're GPU-crackable), or unsalted hashes. Argon2id or bcrypt are deliberately **slow** and **salted**. (Older tutorials use `passlib`, which is unmaintained. FastAPI's docs now use `pwdlib`.)

### JWT access tokens
`header.payload.signature`, base64url-encoded. The payload is **readable by anyone**, only tamper-proof. Never put secrets in it.
```python
jwt.encode({"sub": "42", "role": "user", "iat": now, "exp": now + 15min}, SECRET, algorithm="HS256")
jwt.decode(token, SECRET, algorithms=["HS256"])     # ← always pin the algorithm list
```
- **Pinning `algorithms`** blocks the `alg: none` attack and RS/HS algorithm-confusion attacks.
- Keep access tokens **short-lived** (5–15 min). Long sessions use a **refresh token**: long-lived, stored server-side so it can be revoked, rotated on use, and sent as an httpOnly cookie.
- Revocation is hard with stateless JWTs. Options: short TTLs, a denylist of `jti`s, or a token version per user.
- **Re-load the user from the DB** in `get_current_user`, so deleted or disabled users and changed roles take effect.

### FastAPI's security helpers
```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")   # parses the Bearer header, 401 if missing, and adds Authorize to /docs

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User: ...
CurrentUser = Annotated[User, Depends(get_current_user)]

@app.post("/auth/token")
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()]): ...   # form fields: username, password
```
Using the OAuth2 password flow means the **Authorize** button in `/docs` works. Try it: `python run.py f10 --solution`, log in as `admin@example.com` / `adminpass123`, then call `/admin/users`.

### Cookies vs Authorization header (for a React SPA)
| | Bearer header (token in JS memory) | httpOnly cookie |
|---|---|---|
| XSS can steal it | yes, if stored in localStorage | no |
| CSRF risk | none | yes, so use `SameSite=Lax/Strict` and CSRF tokens |
| Works cross-domain / mobile | easily | needs CORS credentials setup |
A common setup: a short-lived access token in memory, plus a refresh token in an httpOnly cookie.

## 🏋️ Exercise
1. `security.py`: real Argon2 hashing, `create_access_token`, and `decode_access_token` (pinned algorithm, required claims, every `PyJWTError` → `InvalidToken`).
2. `deps.py`: replace the "trust the `X-User-Id` header" bug with `OAuth2PasswordBearer` + JWT decoding + a user lookup (401 + `WWW-Authenticate: Bearer`). Implement `require_role` (403).

```bash
python check.py f10
```

## 💼 Interview angle
- *"How do you store passwords?"*: Argon2id or bcrypt (slow, salted, with tunable cost), with a constant-time verify. Also cover rate limiting and lockout on login.
- *"JWT vs server-side sessions?"*: JWTs are stateless and scale without a session store, but revocation is hard. Sessions are revocable and simple, but every request needs a lookup (Redis). Many systems use both: short JWTs and revocable refresh tokens.
- *"What attacks apply to JWTs?"*: `alg:none`, algorithm confusion, weak HS secrets (brute-forceable), missing `exp` checks, and sensitive data in the payload.
- *"401 vs 403?"*: unauthenticated vs authenticated but forbidden.
- *"How do you do resource-level authorization?"*: scope queries to the owner (`WHERE owner_id = :me`) and return 404 rather than 403 for other people's resources, so IDs aren't leaked. You'll see this in the capstone.
- *"OAuth2 vs OIDC?"*: OAuth2 is delegated authorization (access tokens). OpenID Connect adds identity (an ID token, user info) on top. "Login with Google" is OIDC.
