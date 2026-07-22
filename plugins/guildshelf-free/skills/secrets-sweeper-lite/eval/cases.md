# Secrets Sweeper Lite — trigger / non-trigger evaluation cases

20 cases: 10 that SHOULD trigger this skill, 10 that should NOT. Acceptance
target: >= 9/10 correct triggers, <= 1/10 false triggers. Adapted from the
full Secrets Hygiene Sweeper spec; cases that depend on full-only features
(denylist, JSON report) were rewritten to Lite scope.

## Should trigger (10)

| # | Prompt | Why it triggers |
|---|---|---|
| 1 | "Scan this skill folder for hardcoded secrets before I publish it." | Core case: pre-publish secrets scan. |
| 2 | "Can you check if there are any leaked API keys in this repo?" | Leaked-key check. |
| 3 | "I'm about to open-source this project — run a sanitization check." | Pre-release check. |
| 4 | "Is it safe to share this SKILL.md publicly? I might have left a key in it." | Safe-to-share question about credentials. |
| 5 | "Quick check on ./client-handoff — flag any API keys or tokens before I send it." | Handoff credential check. |
| 6 | "Before we push this to the marketplace, make sure there are no credentials anywhere in it." | Pre-publish credential gate. |
| 7 | "Audit my dotfiles repo for anything sensitive like keys or tokens." | Credential audit of a directory. |
| 8 | "I think I hardcoded a Stripe key somewhere in this project — find it." | Locate a specific hardcoded key. |
| 9 | "Run a quick secrets check on my .claude directory before I zip it up and share it." | Pre-share scan of an agent config dir. |
| 10 | "Check this agent config for any private keys or JWTs before I send it to the contractor." | Credential types this Lite edition covers. |

## Should NOT trigger (10)

| # | Prompt | Why it does not trigger |
|---|---|---|
| 11 | "Rotate my AWS access keys and update the CI variables." | Remediation action, not scanning. |
| 12 | "Set up HashiCorp Vault for our team secrets." | Runtime secret management. |
| 13 | "Scan my git history for secrets committed last year." | Working tree only — explicitly out. |
| 14 | "Generate a strong password for my new account." | Credential creation, not detection. |
| 15 | "Check this skill for prompt injection vulnerabilities." | Security-adjacent but a different product. |
| 16 | "Encrypt this config file with AES before I email it." | Encryption task, not scanning. |
| 17 | "My OpenAI API key stopped working — debug why." | Key debugging, not leak detection. |
| 18 | "Add my API key to the .env file and load it in the app." | Configuration task, not scanning. |
| 19 | "What's the best way to store secrets in GitHub Actions?" | Consulting question, not a scan. |
| 20 | "Scan this repo for malware." | Malware detection — out of scope by design. |

## Boundary note

Prompts about PII (emails, phone numbers, names), IP addresses, or denylist
terms belong to the full Secrets Hygiene Sweeper. If the Lite skill triggers
on them, it should scan what it can and state plainly that PII/denylist
coverage is not included in this edition.
