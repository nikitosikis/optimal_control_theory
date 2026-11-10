"""Install the reviewed personal lab style and a scoped global preference."""
from pathlib import Path
import hashlib
import json
import shutil

STAGE = Path(__file__).resolve().parent
SOURCE = STAGE / 'personal-skills' / 'lab-report-style'
TARGET = Path('C:/Users/jopajack/.codex/skills/lab-report-style')
GLOBAL_RULES = Path('C:/Users/jopajack/.codex/AGENTS.md')
SNIPPET = STAGE / 'global-lab-preference.md'
FILES = [
    'SKILL.md', 'agents/openai.yaml', 'assets/lab-report.tex',
    'references/lsau-lab4.pdf', 'references/title-page.png',
    'references/body-page.png', 'references/author.md',
]

assert TARGET.parent.resolve() == Path('C:/Users/jopajack/.codex/skills').resolve()
if TARGET.exists():
    raise FileExistsError(f'Existing skill will not be overwritten: {TARGET}')
for relative in FILES:
    if not (SOURCE / relative).is_file():
        raise FileNotFoundError(SOURCE / relative)
snippet = SNIPPET.read_bytes().rstrip() + b'\n'
marker = '## Личные предпочтения для лабораторных отчётов'.encode('utf-8')
existing = GLOBAL_RULES.read_bytes() if GLOBAL_RULES.exists() else b''
if marker in existing:
    raise RuntimeError('A global lab preference already exists; inspect it before editing.')

for relative in FILES:
    destination = TARGET / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE / relative, destination)
    assert hashlib.sha256(destination.read_bytes()).digest() == hashlib.sha256((SOURCE / relative).read_bytes()).digest()
with GLOBAL_RULES.open('ab') as f:
    if existing:
        f.write(b'\n\n')
    f.write(snippet)
assert GLOBAL_RULES.read_bytes().startswith(existing)
assert marker in GLOBAL_RULES.read_bytes()
print(json.dumps({'skill':str(TARGET),'global_preferences':str(GLOBAL_RULES),
                  'files_verified':len(FILES),'implicit_invocation':True},ensure_ascii=False))
