from pathlib import Path
import sys

p = Path('templates/index.html')
if not p.exists():
    print('FAIL: templates/index.html not found')
    raise SystemExit(2)
text = p.read_text(encoding='utf-8')
required = [
    '<!-- PATCH: WORKSPACE-TABS-RESTORE START -->',
    'data-workspace-tab="home"',
    'data-workspace-tab="project-wbs"',
    'data-workspace-tab="event-detail"',
    'data-workspace-tab="asset"',
    'data-workspace-tab="settings"',
]
for token in required:
    if token not in text:
        print(f'FAIL: missing {token}')
        raise SystemExit(1)
for forbidden in ['>Event</a>', '>Task</a>', '>Goal</a>', '>Project</a>']:
    if forbidden in text:
        print(f'WARN: deprecated entity-tab-looking markup found: {forbidden}')
print('PASS: workspace tabs patch markers and five intended tabs are present.')
