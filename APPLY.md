# CR-0018 NEW tab correction

1. Extract this ZIP at the `pulda-runtime` repository root and allow the
   matching files to be replaced.
2. Review the diff.
3. Run `pytest -q`.
4. Commit and push with a message such as
   `fix: open workspace picker in new tab`.
5. Deploy the pushed `main` commit to Replit.

Expected behavior:

- `+` opens a temporary `NEW` tab.
- The entire center workspace shows the descriptive screen cards.
- Selecting a card adds and opens that screen tab.
- Returning to Today does not break `+`.
- The workspace tab strip has no horizontal scrollbar.
- The left panel is an initial favorites area, not a second navigation tree.
- Workspaces and Project depth use breadcrumbs/back links.
