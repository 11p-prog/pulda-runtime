# CR-0015 Daily Activity correction delivery

Baseline: `origin/main` at `a8e4cb2`. Prepared 2026-07-21; not deployed.

## Apply and verify

1. Back up the current repository folder, then extract this ZIP at the repository root.
2. Review the GitHub Desktop diff. Run `pytest -q`; expected result: `39 passed`.
3. Commit and push with a message such as `fix: correct CR-0015 daily activity circulation`.
4. Deploy that commit to Replit. Confirm `/api/health` is `status=ok` and PostgreSQL.
5. Before changing 2026-07-19 data, run:
   `python scripts/migrate_daily_activity_20260719.py --backup daily-activity-2026-07-19-backup.json`
   Keep the backup outside public Git and verify the dry-run reports Event ID 1,
   nine items, and exactly one test item.
6. Apply once with `--apply` plus a new backup filename. Do not rerun `--apply`.
7. Trigger one authenticated Notion pull. Verify `ok=true`, returned `event_ids`,
   `added_count`, empty `errors`, and a non-empty `checkpoint`. Trigger it again;
   it must add zero items.

Runtime migration and user verification remain pending until steps 4–7 are observed.
