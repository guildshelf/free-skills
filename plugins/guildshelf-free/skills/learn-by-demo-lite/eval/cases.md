# Learn-by-Demo Lite — trigger / non-trigger evaluation cases

20 cases: 10 that SHOULD trigger this skill, 10 that should NOT. Acceptance
target: >= 9/10 correct triggers, <= 1/10 false triggers. Adapted from the
full Learn-by-Demo spec; two full-only prompts (replay scaffolding, batch
scaling) were replaced with Lite-scope capture/draft prompts.

## Should trigger (10)

| # | Prompt | Why it triggers |
|---|---|---|
| 1 | "I need to automate pulling weekly reports from our internal admin portal but there's no API documentation anywhere. Can you watch me do it once and work out the API from that?" | Core case: no docs, demonstrate once. |
| 2 | "My script keeps getting 401s on what I think is the right endpoint for our CRM, but I'm logged in fine in my own browser. How do we get the real request?" | Guessed-endpoint 401 symptom. |
| 3 | "Let me show you how I export the data by hand — record my steps and then automate it." | "Let me show you" trigger phrase. |
| 4 | "This legacy SPA has zero docs. How do I find out exactly what request the Save button fires?" | Action-to-request mapping. |
| 5 | "Every time the AI guesses our internal API paths it gets HTML back instead of JSON. I want a method that doesn't involve guessing." | HTML-instead-of-JSON symptom. |
| 6 | "I have a HAR file of my session doing the task manually. Turn it into an endpoint summary I can build automation from." | HAR-to-draft — the Lite tool verbatim. |
| 7 | "Capture the network traffic while I click through the dashboard once, and write down which requests fire for each step." | Capture + action mapping. |
| 8 | "Watch me do this once in the browser and list every API call it makes, with the auth type." | Capture + draft output. |
| 9 | "Our vendor portal has no docs — I'll demonstrate the workflow now; note the requests including which header carries the auth." | Demonstration + auth observation. |
| 10 | "Export a HAR from DevTools of me submitting the form, then tell me the endpoint, method, and body fields it used." | DevTools HAR path — Lite workflow. |

## Should NOT trigger (10)

| # | Prompt | Why it does not trigger |
|---|---|---|
| 11 | "Write a script using the Stripe API to list last month's charges." | Documented public API — read the docs. |
| 12 | "Help me get past the CAPTCHA on this login page so my bot can continue." | Red line: bot-detection bypass (decline). |
| 13 | "Generate Playwright end-to-end tests for my React app's checkout flow." | UI test generation — codegen's job. |
| 14 | "Scrape every listing from this property portal I don't have an account on." | Unauthorized third-party scraping. |
| 15 | "How does fetch() work in JavaScript? Show me an example." | General programming question. |
| 16 | "Record my screen and turn it into a tutorial video with captions." | Screen recording, not network capture. |
| 17 | "Set up a scheduled task to run my existing sync script every night without popping a console window." | Scheduling/background execution — different skill. |
| 18 | "My GitHub Actions OAuth token keeps expiring — fix the refresh logic in this workflow file." | Documented API auth debugging. |
| 19 | "Auto-post to Instagram whenever I publish a new blog article." | Platform ToS red-line scenario. |
| 20 | "Decompile this Android APK and extract the API keys from the binary." | Mobile reverse engineering — explicitly out. |

## Boundary note

Prompts that ask for a *generated replay script*, CDP attachment to a live
logged-in browser, or batch scaling (pagination, token refresh) belong to
the full Learn-by-Demo. The Lite skill should still capture and draft, then
state plainly that scaffolding and hardening are in the full edition.
