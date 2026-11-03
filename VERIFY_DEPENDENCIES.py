"""Windows installation verifier. No native shell escaping required."""
from __future__ import annotations
import importlib
from importlib import metadata
from pathlib import Path
import sys


def main() -> int:
    quiet = '--quiet' in sys.argv
    requirements_path = Path(__file__).resolve().with_name('requirements.txt')
    try:
        from packaging.requirements import Requirement
    except Exception as exc:
        if not quiet:
            print(f'Packaging library not ready: {exc}')
        return 1

    errors = []
    for line in requirements_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        try:
            requirement = Requirement(line)
            installed_version = metadata.version(requirement.name)
            if installed_version not in requirement.specifier:
                errors.append(f'{requirement.name} {installed_version} does not satisfy {requirement.specifier}')
        except Exception as exc:
            errors.append(f'{line}: {exc}')

    for name in ('fastapi','uvicorn','jwt','bcrypt','sklearn','joblib','qrcode',
                 'numpy','dotenv','paho.mqtt.client','pytest','httpx','reportlab'):
        try:
            importlib.import_module(name)
        except Exception as exc:
            errors.append(f'Cannot import {name}: {type(exc).__name__}: {exc}')

    if errors:
        if not quiet:
            print('ColdChain dependency verification failed:')
            for error in errors:
                print('  - ' + error)
        return 1
    if not quiet:
        print('ColdChain package versions and imports: OK')
    return 0


if __name__ == '__main__':
    sys.exit(main())
