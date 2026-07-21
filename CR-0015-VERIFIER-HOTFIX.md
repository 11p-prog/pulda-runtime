# CR-0015 verifier hotfix — 2026-07-21

## Scope

- Replaces only `scripts/migrate_daily_activity_20260719.py`.
- Does not change Runtime data by itself.
- Do not run `--apply` again.

## Correction

The verifier now recognizes a valid post-migration state when:

- the operational batch has 8 items and no known test item;
- the separated test batch has exactly the known test item;
- the test envelope exists with `data_class=test`.

It returns `status=already_migrated` for that state and
`status=inconsistent_post_migration` when those invariants do not match.

## Verification command

```bash
python scripts/migrate_daily_activity_20260719.py --backup daily-activity-2026-07-19-backup.json
```

Expected fields include:

```json
{"status":"already_migrated","operational_item_count":8,"test_item_count":1}
```

The existing backup must be retained until Runtime verification is complete.
