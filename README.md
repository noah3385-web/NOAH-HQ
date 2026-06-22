# Noah OS Sandbox ClickUp Builder

This local Python package builds a repeatable **Noah OS Sandbox** inside an existing ClickUp Space. It uses the ClickUp API for the reliable MVP pieces: folders, lists, task descriptions, reference tasks, template tasks, sample capture tasks, manual setup tasks, and verification reports.

The builder is intentionally conservative. ClickUp plan features such as dashboards, automations, native task templates, recurring rules, relationship fields, tags, docs, and custom fields can vary by account and are not all reliably available through the public API. Instead of failing, this project creates clear manual setup tasks in ClickUp and documents the remaining UI work.

## Files

- `build_clickup_noah_os.py` - idempotent builder for the sandbox scaffold.
- `verify_clickup_noah_os.py` - checks the expected scaffold and writes `verification_report.md`.
- `noah_os_blueprint.json` - editable source of truth for folders, lists, tasks, and descriptions.
- `.env.example` - environment variable template.
- `manual_setup.md` - UI setup checklist for ClickUp features that are manual in this MVP.
- `continuation_prompt.md` - prompt to paste into ChatGPT Agent after the API scaffold is built.
- `run_log_example.md` - example run sequence and expected outputs.

Generated files after running:

- `build_log.json`
- `build_report.md`
- `verification_report.md`

## What it creates

Inside the selected existing ClickUp Space, the script creates 15 sandbox folders prefixed with `Noah OS Sandbox`, including Command Center, Mortgage Pipeline, Partner CRM, Events, Internal Team, Reporting, Career, Personal Finance, Household, Health, Relationships, Hobbies, Personal Development, Sensitive Data Index, and Archive.

It then creates the lists, useful folder/list descriptions, Command Center placeholder tasks, Universal Capture samples, template tasks, reference tasks, daily/review tasks, and Manual Setup Required tasks defined in `noah_os_blueprint.json`.

## Get a ClickUp API token

1. Open ClickUp.
2. Go to **Settings**.
3. Open **Apps** or **ClickUp API**.
4. Generate or copy a personal API token.
5. Keep it private. Do not commit `.env`.

## Get workspace and space IDs

ClickUp API v2 uses `team_id` to mean Workspace ID. This project names the variable `CLICKUP_WORKSPACE_ID` because that is clearer for users.

Fastest path:

1. Copy `.env.example` to `.env`.
2. Fill in only `CLICKUP_API_TOKEN`.
3. Run `python build_clickup_noah_os.py --dry-run`.
4. The script will print available workspaces and spaces.
5. Copy the desired IDs into `.env`.

## Configure `.env`

```bash
cp .env.example .env
```

Edit `.env`:

```dotenv
CLICKUP_API_TOKEN=pk_your_token_here
CLICKUP_WORKSPACE_ID=123456
CLICKUP_SPACE_ID=789012
CLICKUP_SANDBOX_PREFIX=Noah OS Sandbox
CLICKUP_DEFAULT_ASSIGNEE_ID=
TIMEZONE=America/New_York
```

`CLICKUP_DEFAULT_ASSIGNEE_ID` is optional. If present, newly-created tasks are assigned to that ClickUp user ID.

## Install dependencies

```bash
python -m pip install -r requirements.txt
```

## Dry run

```bash
python build_clickup_noah_os.py --dry-run
```

Dry run validates credentials, confirms the target workspace/space, loads existing folders/lists, and prints what would be created without writing to ClickUp.

## Build

```bash
python build_clickup_noah_os.py --apply
```

The builder is idempotent: it searches by name within the expected parent before creating anything. Re-running it reuses existing folders/lists/tasks rather than duplicating them.

## Resume or re-run safely

```bash
python build_clickup_noah_os.py --apply --resume
```

`--resume` is accepted for user clarity. The script is always resume-safe because every create operation first performs a parent-scoped lookup by name.

## Verify

```bash
python verify_clickup_noah_os.py
```

The verifier reads `noah_os_blueprint.json`, queries ClickUp, checks folders/lists/key tasks, prints a summary table, and writes `verification_report.md`.

## Manual setup

After the API scaffold exists, open the **Manual Setup Required** list in ClickUp and work through the tasks. Also read `manual_setup.md`. These items cover native custom fields, tags, dashboards/views, automations, recurring tasks, native templates, relationships, and statuses/stages.

## MVP limitations

This MVP does not directly create native ClickUp dashboards, automations, recurring schedules, native templates, relationship fields, custom fields, docs/pages, or tags. It creates durable task-based placeholders and manual setup instructions instead. This avoids brittle behavior across ClickUp plans and keeps the scaffold repeatable.

## Editing the blueprint

Most content lives in `noah_os_blueprint.json`. You can add lists, edit descriptions, or add template/sample/manual tasks there, then re-run the builder. Keep names stable if you want idempotent reuse.
