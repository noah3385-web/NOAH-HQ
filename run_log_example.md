# Example Run Log

## 1. Install

```bash
python -m pip install -r requirements.txt
```

Expected result: `requests` and `python-dotenv` install successfully.

## 2. Configure

```bash
cp .env.example .env
```

Fill in `CLICKUP_API_TOKEN`, `CLICKUP_WORKSPACE_ID`, and `CLICKUP_SPACE_ID`.

## 3. Dry run

```bash
python build_clickup_noah_os.py --dry-run
```

Expected result: the script prints the target workspace/space and logs dry-run folder/list/task actions. It writes `build_log.json` and `build_report.md`.

## 4. Apply

```bash
python build_clickup_noah_os.py --apply
```

Expected result: folders, lists, and tasks are created or reused. API rate limits are retried with backoff.

## 5. Resume safely

```bash
python build_clickup_noah_os.py --apply --resume
```

Expected result: existing items are reused; missing items are created.

## 6. Verify

```bash
python verify_clickup_noah_os.py
```

Expected result: a Complete/Partial/Missing summary is printed and `verification_report.md` is written.
