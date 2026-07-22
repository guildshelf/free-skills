# OpenSSL AES-CBC Cheatsheet

A single reference page for the OpenSSL **"Salted__" AES-256-CBC** password
format — the one behind every `U2FsdGVkX1...` base64 blob and most
"works in language A, `bad decrypt` in language B" mysteries.

On the page (`SKILL.md`):

- The format in 10 lines + exact byte layout
- EVP_BytesToKey key/IV derivation, MD5 and SHA-256 variants
- The KDF discriminator: is it really this format, or PBKDF2 in disguise?
- `openssl` CLI ground-truth one-liners
- A minimal Python recipe (PyCryptodome has no built-in mode for this) and
  the PHP raw-bytes gotcha
- 8 failure modes ranked by how often they bite
- Security notes: why this is legacy-interop only

## Use as an agent skill

Drop this folder into your agent's skills directory (for Claude Code:
`~/.claude/skills/aes-cheatsheet/`). It triggers on "bad decrypt",
"Salted__", "EVP_BytesToKey", and cross-language AES-CBC interop questions —
and deliberately does NOT trigger for new-system crypto design, TLS,
password hashing, or JWTs.

## What the cheatsheet deliberately leaves out

Honest scope: this is the reference page only. The full **AES Interop Kit**
ships the part you cannot copy off a page: a drop-in zero-dependency JS
module for browsers and Node >= 20 (Web Crypto has no MD5 — the kit embeds
a pure-JS one) with both `encryptOpenSSL` and `decryptOpenSSL`, test vectors
verified against the `openssl` CLI in both directions, and the full
cross-language recipe matrix including Dart and Node `crypto`.

## License

Apache License 2.0 — see `LICENSE.txt`. Not affiliated with Anthropic;
Claude is a trademark of Anthropic, referenced only to describe
compatibility.

---

Full version — the AES Interop Kit with the browser/Node JS module and
CLI-verified test vectors — is part of the Guildshelf library at
https://guildshelf.com
