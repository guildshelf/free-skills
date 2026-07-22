#!/usr/bin/env python3
"""har_draft.py -- turn a browser HAR capture into a redacted endpoint draft.

Reads a HAR file (browser DevTools -> Network -> "Save all as HAR"), keeps
the API-looking traffic, groups it into endpoints, and prints a Markdown
draft: method, URL template, auth type, query parameters, body field names,
and statuses seen. Credentials (Authorization, Cookie, API-key headers,
token-ish query parameters) are ALWAYS redacted -- there is no off switch in
this Lite edition.

Python 3.8+, standard library only. Nothing is sent anywhere.

Usage:
    python har_draft.py capture.har
    python har_draft.py capture.har -o draft.md
    python har_draft.py capture.har --host api.example.com --all

Exit codes: 0 draft produced | 2 execution error (unreadable/invalid HAR).

Copyright 2026 Guildshelf. Licensed under the Apache License, Version 2.0.
This is the free Lite edition; the full Learn-by-Demo adds a Playwright
capture harness (CDP attach to your logged-in browser), JSONL captures,
machine-readable endpoint specs, and a replay-script scaffold generator.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import OrderedDict
from urllib.parse import urlsplit

REDACTED = "<REDACTED>"

SENSITIVE_HEADERS = {
    "authorization", "proxy-authorization", "cookie", "set-cookie",
    "x-api-key", "api-key", "apikey", "x-auth-token", "x-access-token",
    "x-session-token", "x-csrf-token", "x-xsrf-token",
}

SENSITIVE_QUERY_PARAMS = {
    "token", "access_token", "refresh_token", "id_token", "api_key",
    "apikey", "key", "auth", "session", "sessionid", "session_id",
    "sig", "signature", "password",
}

STATIC_EXT_RE = re.compile(
    r"\.(png|jpe?g|gif|svg|webp|ico|css|woff2?|ttf|eot|map|mp4|webm)(\?|$)",
    re.I,
)
_NUM_SEG = re.compile(r"^\d+$")
_UUID_SEG = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I
)
_HASH_SEG = re.compile(r"^[0-9a-f]{16,}$", re.I)
_AUTH_SCHEME_RE = re.compile(
    r"^(Bearer|Basic|Digest|Token|ApiKey)\s+.+$", re.IGNORECASE
)


# --------------------------------------------------------------------------
# Loading and filtering
# --------------------------------------------------------------------------

def load_entries(path: str):
    with open(path, "r", encoding="utf-8-sig") as fh:
        har = json.load(fh)
    entries = har.get("log", {}).get("entries", [])
    records = []
    for entry in entries:
        req = entry.get("request", {})
        resp = entry.get("response", {})
        post = req.get("postData") or {}
        records.append({
            "method": req.get("method", "GET"),
            "url": req.get("url", ""),
            "status": resp.get("status"),
            "resource_type": (entry.get("_resourceType") or "").lower(),
            "request_headers": _headers_to_dict(req.get("headers")),
            "request_body": post.get("text") or "",
            "request_mime": post.get("mimeType") or "",
            "response_mime": ((resp.get("content") or {}).get("mimeType") or ""),
        })
    return records


def _headers_to_dict(headers):
    if not headers:
        return {}
    return {str(h.get("name", "")).lower(): h.get("value", "") for h in headers}


def looks_like_api(rec: dict) -> bool:
    """Heuristic: keep requests that look like API calls, drop static assets."""
    url = rec["url"]
    if STATIC_EXT_RE.search(url):
        return False
    if rec.get("resource_type") in ("xhr", "fetch"):
        return True
    mime = (rec.get("response_mime") or "").lower()
    if "json" in mime or "xml" in mime:
        return True
    if rec["method"] in ("POST", "PUT", "PATCH", "DELETE"):
        return True
    if "/api/" in url or "/rest/" in url or "/graphql" in url:
        return True
    return False


# --------------------------------------------------------------------------
# Redaction (always on)
# --------------------------------------------------------------------------

def redact_header_value(name: str, value: str) -> str:
    if name.lower() not in SENSITIVE_HEADERS:
        return value
    m = _AUTH_SCHEME_RE.match(value or "")
    if m:
        return "%s %s" % (m.group(1), REDACTED)
    return REDACTED


def redact_url(url: str) -> str:
    if not url or "?" not in url:
        return url
    base, _, query = url.partition("?")
    parts = []
    for pair in query.split("&"):
        key, sep, _val = pair.partition("=")
        if sep and key.lower() in SENSITIVE_QUERY_PARAMS:
            parts.append("%s=%s" % (key, REDACTED))
        else:
            parts.append(pair)
    return base + "?" + "&".join(parts)


# --------------------------------------------------------------------------
# Endpoint grouping
# --------------------------------------------------------------------------

def path_template(url: str) -> str:
    """Normalize volatile path segments (ids, uuids, hashes) to placeholders."""
    parts = urlsplit(url)
    segments = []
    for seg in parts.path.split("/"):
        if _NUM_SEG.match(seg):
            segments.append("{id}")
        elif _UUID_SEG.match(seg) or _HASH_SEG.match(seg):
            segments.append("{uuid}")
        else:
            segments.append(seg)
    return "/".join(segments) or "/"


def detect_auth(headers: dict) -> str:
    auth = headers.get("authorization", "")
    if auth:
        scheme = auth.split(" ", 1)[0].lower()
        if scheme == "bearer":
            return "bearer token (Authorization header)"
        if scheme == "basic":
            return "HTTP basic (Authorization header)"
        return "Authorization header (%s)" % scheme
    for key in ("x-api-key", "api-key", "apikey", "x-auth-token",
                "x-access-token"):
        if key in headers:
            return "API key header (%s)" % key
    if "cookie" in headers:
        return "session cookie"
    return "none observed"


def body_field_names(body: str, mime: str):
    """Top-level field names of a JSON body -- names only, never values."""
    if not body:
        return []
    if "json" not in (mime or "").lower() and body.lstrip()[:1] not in ("{", "["):
        return []
    try:
        data = json.loads(body)
    except (ValueError, TypeError):
        return []
    if isinstance(data, dict):
        return sorted(data.keys())
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return sorted(data[0].keys())
    return []


def build_draft(records, host_filter=None, keep_all=False):
    endpoints = OrderedDict()
    for rec in records:
        if not rec["url"]:
            continue
        parts = urlsplit(rec["url"])
        if host_filter and parts.netloc != host_filter:
            continue
        if not keep_all and not looks_like_api(rec):
            continue
        key = (rec["method"],
               parts.scheme + "://" + parts.netloc + path_template(rec["url"]))
        ep = endpoints.setdefault(key, {
            "method": rec["method"],
            "url_template": key[1],
            "auth": detect_auth(rec["request_headers"]),
            "query_params_seen": [],
            "body_fields_seen": [],
            "statuses_seen": [],
            "sample_url": redact_url(rec["url"]),
        })
        if parts.query:
            for pair in parts.query.split("&"):
                name = pair.partition("=")[0]
                if name and name not in ep["query_params_seen"]:
                    ep["query_params_seen"].append(name)
        for field in body_field_names(rec["request_body"], rec["request_mime"]):
            if field not in ep["body_fields_seen"]:
                ep["body_fields_seen"].append(field)
        if rec["status"] not in ep["statuses_seen"]:
            ep["statuses_seen"].append(rec["status"])
    return list(endpoints.values())


def render_markdown(endpoints, source_path: str) -> str:
    lines = []
    ap = lines.append
    ap("# Endpoint draft (from observed traffic)")
    ap("")
    ap("- Source capture: `%s`" % source_path)
    ap("- Endpoints found: %d" % len(endpoints))
    ap("- Credentials: redacted (always on in the Lite edition)")
    ap("")
    if not endpoints:
        ap("No API-looking requests found. Re-run with `--all` to keep every "
           "request, or check that the capture was taken with the Network "
           "panel recording.")
        ap("")
    for i, ep in enumerate(endpoints, 1):
        ap("## %d. `%s %s`" % (i, ep["method"], ep["url_template"]))
        ap("")
        ap("- **Auth:** %s" % ep["auth"])
        if ep["query_params_seen"]:
            ap("- **Query params seen:** %s" % ", ".join(
                "`%s`" % q for q in ep["query_params_seen"]))
        if ep["body_fields_seen"]:
            ap("- **Request body fields:** %s" % ", ".join(
                "`%s`" % f for f in ep["body_fields_seen"]))
        ap("- **Statuses seen:** %s" % ", ".join(
            str(s) for s in ep["statuses_seen"]))
        ap("- **Sample URL (redacted):** `%s`" % ep["sample_url"])
        ap("")
    ap("---")
    ap("")
    ap("Next: reproduce ONE of these calls exactly as captured (same headers, "
       "same body shape) before parameterizing anything. Build replay from "
       "facts, not guesses.")
    ap("")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="har_draft.py",
        description="Convert a browser HAR capture into a redacted Markdown "
                    "endpoint draft (method, URL template, auth type, query "
                    "params, body field names). Credentials are always "
                    "redacted. Stdlib only, nothing is sent anywhere.",
        epilog="Exit codes: 0 draft produced | 2 execution error. This is "
               "the free Lite edition of the Guildshelf Learn-by-Demo skill.")
    parser.add_argument("capture", help="Path to a .har file (DevTools export)")
    parser.add_argument("-o", "--output",
                        help="Write the draft here (default: stdout)")
    parser.add_argument("--host",
                        help="Only include requests to this host, "
                             "e.g. api.example.com")
    parser.add_argument("--all", action="store_true",
                        help="Keep every request (default: API-looking "
                             "traffic only)")
    args = parser.parse_args(argv)

    try:
        records = load_entries(args.capture)
    except OSError as e:
        print("error: cannot read capture: %s" % e, file=sys.stderr)
        return 2
    except (ValueError, KeyError) as e:
        print("error: not a valid HAR file: %s" % e, file=sys.stderr)
        return 2

    endpoints = build_draft(records, host_filter=args.host, keep_all=args.all)
    text = render_markdown(endpoints, args.capture)
    if args.output:
        with open(args.output, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print("Draft written to: %s (%d endpoints)"
              % (args.output, len(endpoints)), file=sys.stderr)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
