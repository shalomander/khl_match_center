from pathlib import Path


def get_modules(path):
    fs = [f for f in Path(path).rglob('*.py') if not f.name.startswith('_')]
    return [str(f).replace('/', '.')[:-3] for f in fs]

