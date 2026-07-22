# Changelog

All notable changes to the OpenSSL AES-CBC Cheatsheet are documented here.
This project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-07-18

### Added

- Initial open-source release of the **OpenSSL AES-CBC Cheatsheet**
  (Apache-2.0), the free single-page edition of the Guildshelf AES Interop
  Kit.
- `SKILL.md` — one-page reference: format in 10 lines, byte layout,
  EVP_BytesToKey derivation (MD5/SHA-256), KDF discriminator
  (PBKDF2-in-disguise check), `openssl` CLI ground-truth one-liners, minimal
  Python recipe + PHP raw-bytes gotcha, 8 ranked failure modes, and security
  notes.
- `eval/cases.md` — 20 trigger / non-trigger evaluation cases.
- `LICENSE.txt` — Apache License 2.0.

### Notes

- Reference page only — no scripts. The drop-in browser/Node JS module
  (embedded pure-JS MD5, encrypt + decrypt), CLI-verified test vectors, and
  the full cross-language recipe matrix are in the full AES Interop Kit.
