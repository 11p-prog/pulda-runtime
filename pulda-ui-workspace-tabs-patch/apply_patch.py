from pathlib import Path
import sys

TARGET = Path('templates/index.html')
MARKER_START = '<!-- PATCH: WORKSPACE-TABS-RESTORE START -->'
MARKER_END = '<!-- PATCH: WORKSPACE-TABS-RESTORE END -->'
ANCHOR = '    </header>\n\n    <div class="max-w-4xl mx-auto w-full px-10 py-10 pb-36 flex flex-col gap-14">'

BLOCK = '''    </header>\n\n    <!-- PATCH: WORKSPACE-TABS-RESTORE START -->\n    <!-- 2026-07-19: Restore the central workspace navigation removed by the UI regression.\n         This is purpose-based workspace navigation, not the deprecated Event/Task/Goal/Project entity tab set. -->\n    <nav id="workspace-tabs" aria-label="작업 화면"\n      class="sticky top-[76px] z-30 px-10 bg-surface-bright/90 glass-blur border-b border-outline-variant/10">\n      <div class="max-w-4xl mx-auto flex items-center gap-1 overflow-x-auto py-2">\n        <a href="/" data-workspace-tab="home"\n          class="workspace-tab whitespace-nowrap rounded-lg px-4 py-2 text-[12px] font-semibold transition-colors {{ 'bg-primary text-on-primary' if page == 'home' else 'text-on-surface-variant hover:bg-surface-container-low' }}">\n          Home\n        </a>\n        <a href="/projects" data-workspace-tab="project-wbs"\n          class="workspace-tab whitespace-nowrap rounded-lg px-4 py-2 text-[12px] font-semibold transition-colors {{ 'bg-primary text-on-primary' if page == 'projects' else 'text-on-surface-variant hover:bg-surface-container-low' }}">\n          Project WBS\n        </a>\n        <a href="#event-detail" data-workspace-tab="event-detail"\n          class="workspace-tab whitespace-nowrap rounded-lg px-4 py-2 text-[12px] font-semibold text-on-surface-variant hover:bg-surface-container-low transition-colors">\n          Event detail\n        </a>\n        <a href="#asset" data-workspace-tab="asset"\n          class="workspace-tab whitespace-nowrap rounded-lg px-4 py-2 text-[12px] font-semibold text-on-surface-variant hover:bg-surface-container-low transition-colors">\n          Asset\n        </a>\n        <a href="#settings" data-workspace-tab="settings"\n          class="workspace-tab whitespace-nowrap rounded-lg px-4 py-2 text-[12px] font-semibold text-on-surface-variant hover:bg-surface-container-low transition-colors">\n          Settings\n        </a>\n      </div>\n    </nav>\n    <!-- PATCH: WORKSPACE-TABS-RESTORE END -->\n\n    <div class="max-w-4xl mx-auto w-full px-10 py-10 pb-36 flex flex-col gap-14">'''


def main() -> int:
    if not TARGET.exists():
        print(f'ERROR: {TARGET} not found. Run from the repository root.', file=sys.stderr)
        return 2

    text = TARGET.read_text(encoding='utf-8')
    if MARKER_START in text:
        print('SKIP: workspace tabs patch is already applied.')
        return 0
    if ANCHOR not in text:
        print('ERROR: expected header/content anchor not found; file was not changed.', file=sys.stderr)
        return 3

    backup = TARGET.with_suffix(TARGET.suffix + '.before-workspace-tabs.bak')
    backup.write_text(text, encoding='utf-8')
    TARGET.write_text(text.replace(ANCHOR, BLOCK, 1), encoding='utf-8')
    print(f'PATCHED: {TARGET}')
    print(f'BACKUP:  {backup}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
