# CLAUDE.md

Guidance for AI assistants (Claude Code and others) working in this repository.

## What this project is

**NOAH-HQ** is a small, self-contained Python toolkit that builds a repeatable
**"Noah OS Sandbox"** scaffold inside an existing **ClickUp** Space via the
ClickUp API v2. It is a personal-productivity operating-system scaffold for a
mortgage-industry professional, spanning both business domains (leads, loan
pipeline, partner CRM, events, internal team, reporting) and personal domains
(finance, household, health, relationships, hobbies, development).

The project is deliberately **conservative and idempotent**: it creates only
the ClickUp primitives that are reliably available through the public API
(folders, lists, tasks with markdown descriptions). Features that vary by
ClickUp plan or are UI-only — custom fields, tags, dashboards, automations,
recurring rules, native templates, relationship fields, docs — are **not**
created programmatically. Instead the builder creates durable task-based
placeholders and a "Manual Setup Required" checklist, and documents the rest.

There is **no application server, web frontend, database, or test suite.** It is
a pair of command-line scripts plus a JSON blueprint.

## Repository layout

```
build_clickup_noah_os.py   # Idempotent builder (main entry point)
verify_clickup_noah_os.py  # Verifier; writes verification_report.md
noah_os_blueprint.json     # Source of truth: folders, lists, tasks, descriptions
requirements.txt           # requests, python-dotenv (both optional at runtime)
.env.example               # Environment variable template (copy to .env)
README.md                  # User-facing setup + run instructions
manual_setup.md            # Checklist for ClickUp features that must be done in the UI
continuation_prompt.md     # Prompt to hand off remaining manual setup to an AI agent
run_log_example.md         # Example run sequence and expected outputs
```

Generated at runtime (not committed source — do not treat as inputs):
`build_log.json`, `build_report.md`, `verification_report.md`.

> Note: there is currently **no `.gitignore`**. The generated files above, and
> especially a real `.env` (which holds the ClickUp API token), must never be
> committed. If you add generated output or touch env handling, add a
> `.gitignore` covering `.env`, `build_log.json`, `build_report.md`, and
> `verification_report.md`.

## Architecture and key conventions

### The blueprint is the source of truth

`noah_os_blueprint.json` drives everything. Its top-level keys:

- `sandbox_prefix` — the string `"Noah OS Sandbox"`, embedded in folder names.
  At runtime it is replaced by the `CLICKUP_SANDBOX_PREFIX` env value via a
  single `.replace(bp['sandbox_prefix'], cfg[...], 1)`, so the prefix is
  configurable without editing the blueprint.
- `api_notes` — documents `base_url`, `verified_endpoints`, and `manual_features`.
- `folders` — list of 15 folder objects, each `{name, description, lists[]}`;
  each list is `{name, description}`.
- `command_center_tasks`, `daily_tasks`, `review_tasks` — arrays of task
  **names** (strings) placed into fixed lists (`Noah Command Center`,
  `Daily Operating Tasks`, `Weekly Monthly Quarterly Reviews`).
- `reference_tasks`, `template_tasks`, `sample_capture_tasks`,
  `manual_setup_tasks` — arrays of `{list, name, description}` objects; the
  `list` field names the destination list (matched by name).

**To change what gets built, edit the blueprint, not the Python.** Add lists,
edit descriptions, or add template/sample/manual tasks there, then re-run the
builder. Keep names stable to preserve idempotent reuse.

### Idempotency is the core invariant

Every create operation first does a **parent-scoped lookup by name** and reuses
the existing item if found. Folders are matched within the Space, lists within
their folder, tasks within their list. This makes the builder safe to re-run
and makes `--resume` a no-op guarantee rather than special logic. **Preserve
this pattern** in any change: never create without first checking for an
existing same-named item under the same parent. Renaming a blueprint item
orphans the old one (it is not deleted) and creates a new one.

### Dependency-optional runtime

Both scripts import `requests` and `dotenv` inside `try/except` and fall back to
Python stdlib (`urllib.request`) and a no-op `load_dotenv` when they are absent.
`requirements.txt` pins them for convenience, but **the scripts must keep
running with neither installed.** If you add HTTP or env logic, maintain the
stdlib fallback (`_stdlib_request` / `_stdlib_get`) so the tools work in a bare
Python environment.

### API client conventions

- Base URL: `https://api.clickup.com/api/v2`. Auth is the raw personal token in
  the `Authorization` header (no `Bearer` prefix — ClickUp's convention).
- ClickUp API v2 uses `team_id` to mean **Workspace ID**. The env var is named
  `CLICKUP_WORKSPACE_ID` for clarity but maps to the `/team` endpoints.
- The builder's `Client.req` retries on HTTP 429 and 5xx up to 6 attempts,
  honoring `Retry-After` and otherwise using capped exponential backoff. Keep
  new API calls going through `req` so they inherit retry/backoff and logging.
- Task listing paginates 100 per page (`include_closed=true`).
- Only the endpoints in `api_notes.verified_endpoints` are known-good. Do not
  add calls to plan-dependent endpoints (custom fields, automations, etc.)
  without confirming availability — the whole design avoids those on purpose.

### Logging and reports

The builder's `Logger` accumulates structured events and writes `build_log.json`
plus a human-readable `build_report.md`. Each event carries a `status`
(`created`, `reused`, `skipped`, `failed`, `warning`, `manual`). The verifier
writes `verification_report.md` with a Complete/Partial/Missing summary and
exits `0` only when everything is Complete (else `1`). Match this logging style
for new operations rather than using bare `print`.

## Development workflow

### Setup

```bash
python -m pip install -r requirements.txt   # optional; stdlib fallback exists
cp .env.example .env                         # then fill in CLICKUP_API_TOKEN
```

Required env vars (see `.env.example`): `CLICKUP_API_TOKEN`,
`CLICKUP_WORKSPACE_ID`, `CLICKUP_SPACE_ID`. Optional: `CLICKUP_SANDBOX_PREFIX`
(default `Noah OS Sandbox`), `CLICKUP_DEFAULT_ASSIGNEE_ID`, `TIMEZONE`
(default `America/New_York`).

### Run

```bash
python build_clickup_noah_os.py --dry-run              # validate + preview, no writes
python build_clickup_noah_os.py --apply                # create/reuse in ClickUp
python build_clickup_noah_os.py --apply --resume       # re-run safely (resume is always safe)
python verify_clickup_noah_os.py                        # check scaffold, write report
```

`--dry-run` and `--apply` are mutually exclusive and one is **required**.
`--dry-run` still contacts ClickUp read-only (to list workspaces/spaces/existing
items) but performs no writes. If `CLICKUP_WORKSPACE_ID`/`CLICKUP_SPACE_ID` are
missing, the builder prints available workspaces and spaces to help you fill
them in, then exits `2`.

### Verifying changes

There is no automated test suite or CI. To validate a change:

1. Run `python build_clickup_noah_os.py --dry-run` — it must reach the
   "would create / reuse" logging without errors given valid credentials, or
   exit cleanly with the workspace/space help text when IDs are absent.
2. Byte-check the scripts still parse and the blueprint is valid JSON:
   `python -c "import json,ast; json.load(open('noah_os_blueprint.json')); ast.parse(open('build_clickup_noah_os.py').read()); ast.parse(open('verify_clickup_noah_os.py').read())"`
3. If you changed blueprint content, confirm the builder and verifier agree on
   the same `list`/`name` strings — the verifier re-reads the blueprint and will
   report `Missing` for any name mismatch.

Do not attempt live `--apply` runs against ClickUp unless the user has provided
credentials and asked for it; those calls mutate a real workspace.

## Code style

- Python 3, `from __future__ import annotations`, standard-library-first.
- The existing scripts favor **dense, single-line definitions** (many
  statements per line, compact helpers). Match the surrounding density when
  editing a file rather than reformatting it to a different style.
- Keep functionality within the two scripts; there is no package structure.
- Fail loud on unexpected HTTP errors (`ClickUpError`), but degrade gracefully
  for per-item create failures (log `failed`, continue) so one bad item does
  not abort the whole build.

## Guardrails

- **Never commit secrets.** `.env` holds a live ClickUp token. Only
  `.env.example` (empty values) belongs in git.
- **Do not delete or rename scaffold items** in ClickUp without explicit
  instruction — idempotency depends on stable names.
- **Do not add plan-dependent ClickUp API calls** as the default path. The MVP
  intentionally routes those to `manual_setup.md` and "Manual Setup Required"
  tasks. New capabilities of that kind should be additive and clearly guarded.
- When extending the scaffold, prefer editing `noah_os_blueprint.json` over
  hardcoding names in Python.
