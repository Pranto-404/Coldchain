"""Print the interpreter identity without PowerShell native-command string quoting."""
import sys
from pathlib import Path

def main():
    if '--check' in sys.argv:
        arch = 64 if sys.maxsize > 2**32 else 32
        print(f'{sys.version_info.major}.{sys.version_info.minor}.{arch}')
    elif '--path' in sys.argv:
        print(str(Path(sys.executable).resolve()))
    else:
        print('Use --check or --path', file=sys.stderr)
        return 2
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
