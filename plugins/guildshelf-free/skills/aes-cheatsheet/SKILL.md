---
name: aes-cheatsheet
description: One-page reference for the OpenSSL "Salted__" AES-256-CBC
  password format — byte layout, EVP_BytesToKey key/IV derivation (MD5 and
  SHA-256 variants), openssl CLI ground-truth one-liners, minimal Python and
  PHP recipes, a ranked table of cross-language failure modes ("bad decrypt",
  U2FsdGVkX1 prefix, hex-vs-raw digest bytes, URL-safe base64, PKCS#7
  padding), and a KDF discriminator (is it really this format, or PBKDF2?).
  Use when debugging why ciphertext encrypted in one language fails to
  decrypt in another, or when identifying whether a base64 blob is this
  format. Not for designing new encryption (use AES-GCM + PBKDF2/Argon2 for
  new systems), TLS/HTTPS setup, password hashing (bcrypt/argon2), JWT
  signing, or file checksums. A drop-in browser/Node JS module (Web Crypto
  has no MD5) with CLI-verified test vectors is in the full AES Interop Kit.
---

# OpenSSL "Salted__" AES-CBC Cheatsheet

Everything you need to recognize, debug, and reproduce the OpenSSL
password-based AES-256-CBC format — on one page.

> **Security scope.** MD5-based EVP_BytesToKey is a **legacy construction**.
> This page exists for **interoperability with existing systems**, not for
> new designs. If you control both ends and are building something new, use
> AES-GCM with PBKDF2 or Argon2 instead. All example passphrases here
> (`example-passphrase`) are dummy values — never ship a hard-coded password.

## 1. The format in 10 lines

```
output = base64( ASCII("Salted__") + salt(8 bytes) + AES-256-CBC ciphertext )

Key/IV from password (OpenSSL EVP_BytesToKey, MD5 digest, 1 iteration):
  D_1 = MD5(password || salt)
  D_2 = MD5(D_1 || password || salt)
  D_3 = MD5(D_2 || password || salt)          ... until >= 48 bytes
  Key (32 bytes) = first 32        IV (16 bytes) = bytes 32..48

Plaintext is PKCS#7-padded. Base64 is the STANDARD alphabet (+/), not URL-safe.
```

Because the 8-byte magic header is constant, every ciphertext in this format
starts with the recognizable base64 prefix **`U2FsdGVkX1`**. If you see that
at the start of a token, you are almost certainly looking at this format.

## 2. Byte layout

```
offset   size   content
------   ----   -------------------------------------------
0        8      ASCII magic header: "Salted__"
8        8      salt — random bytes, fresh per message
16       n      AES-256-CBC ciphertext (PKCS#7-padded plaintext)
```

Note the unusual property: the IV is *derived from the KDF*, not
random-and-transmitted. Freshness comes entirely from the 8-byte salt — one
reason this construction is considered legacy.

## 3. Digest variants — and the KDF discriminator

- **MD5** — the historical default (`openssl enc` before 1.1.0, Dart
  `encrypt` package flows, most legacy backends).
- **SHA-256** — the `openssl enc` default **since OpenSSL 1.1.0**. Same
  algorithm with SHA-256 (32 bytes/round, so 2 rounds reach 48 bytes).
- If two stacks disagree on the digest, you get `bad decrypt` even though
  both are "OpenSSL compatible". **Always pin the digest** (`-md md5` /
  `-md sha256`).
- **Is it even this format?** `openssl enc -pbkdf2` / `-iter N` output
  *still* starts with `Salted__`, but the KDF is PBKDF2 — EVP_BytesToKey
  will derive the wrong key. If the encrypting command included `-pbkdf2`
  or `-iter`, use PBKDF2 (natively supported by Web Crypto), not this page.

## 4. Ground truth with the openssl CLI

```bash
# encrypt
printf '%s' 'hello' | openssl enc -aes-256-cbc -md md5 -a -pass pass:example-passphrase
# decrypt
echo 'U2FsdGVkX1...' | openssl enc -d -aes-256-cbc -md md5 -a -pass pass:example-passphrase
```

If the original plaintext comes back, your implementation is byte-exact.
(OpenSSL prints a "deprecated key derivation" warning — expected; legacy
interop is the point.)

## 5. Minimal Python recipe (hashlib + PyCryptodome)

PyCryptodome has **no built-in mode for this format** — roll the KDF:

```python
import base64, hashlib, os
from Crypto.Cipher import AES              # pip install pycryptodome
from Crypto.Util.Padding import pad, unpad

def evp_bytes_to_key(password: bytes, salt: bytes, key_len=32, iv_len=16):
    d, last = b"", b""
    while len(d) < key_len + iv_len:
        last = hashlib.md5(last + password + salt).digest()   # RAW bytes
        d += last
    return d[:key_len], d[key_len:key_len + iv_len]

def encrypt_openssl(plain: str, password: bytes) -> str:
    salt = os.urandom(8)
    key, iv = evp_bytes_to_key(password, salt)
    ct = AES.new(key, AES.MODE_CBC, iv).encrypt(pad(plain.encode(), 16))
    return base64.b64encode(b"Salted__" + salt + ct).decode()

def decrypt_openssl(b64: str, password: bytes) -> str:
    raw = base64.b64decode(b64)
    if raw[:8] != b"Salted__":
        raise ValueError("not OpenSSL salted format")
    salt, ct = raw[8:16], raw[16:]
    key, iv = evp_bytes_to_key(password, salt)
    return unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(ct), 16).decode()
```

**PHP note:** the same KDF loop works with `md5($d . $password . $salt,
true)` — the second argument `true` (RAW output) is the line everyone gets
wrong; without it you concatenate hex strings and derive a different key.

## 6. Failure modes, ranked by how often they bite

| # | Symptom | Root cause | Fix |
|---|---|---|---|
| 1 | `bad decrypt`; base64 does NOT start with `U2FsdGVkX1` | `"Salted__"` header never prepended | Assemble `header + salt + ciphertext` **before** base64 |
| 2 | `bad decrypt` though both sides "use OpenSSL format" | Digest mismatch: MD5 vs SHA-256 | Pin the digest on both sides |
| 3 | Derived key differs between languages | MD5 output consumed as **hex string**, not raw 16 bytes | Raw digest bytes everywhere |
| 4 | One side can't base64-decode the other's output | URL-safe base64 (`-_`) vs standard (`+/`) | Standard alphabet |
| 5 | Plaintext + trailing `\x0f\x0f...` garbage | PKCS#7 padding not stripped (or stripped twice) | Unpad exactly once |
| 6 | Same plaintext → same ciphertext every time | Fixed salt left over from a test | 8 fresh random bytes per message |
| 7 | Works for ASCII, breaks on CJK/emoji | Non-UTF-8 encoding of password or plaintext | UTF-8 everywhere; test with a multi-byte vector |
| 8 | Browser build fails on `require('crypto')` / `window.crypto` | Environment assumptions | Use `globalThis.crypto` |

## 7. Security notes

- Single-iteration MD5 key derivation is fast to brute-force by modern
  standards; it survives only because deployed systems speak it.
- CBC without a MAC is malleable — **no integrity protection**. If the
  surrounding protocol does not authenticate the message, that is a real
  vulnerability.
- For new systems: AES-GCM + PBKDF2 (high iteration count) or Argon2id.
  Web Crypto supports both natively.

## 8. Cheatsheet vs. full kit

Browser JavaScript is the hard target — **Web Crypto has no MD5**, so this
KDF cannot be implemented with `crypto.subtle` alone. The full
**AES Interop Kit** ships a drop-in zero-dependency ES module for browsers
and Node >= 20 (embedded pure-JS MD5, `encryptOpenSSL` + `decryptOpenSSL`,
MD5/SHA-256 option, descriptive errors), CLI-verified test vectors run in
both directions, and the full cross-language recipe matrix (Dart `encrypt`
package, PHP, Python, Node `crypto`, CLI) with an output-comparison
checklist.

## Disclaimer

Not affiliated with, endorsed by, or sponsored by Anthropic. "Claude" is a
trademark of Anthropic, PBC, used here solely to describe compatibility.
