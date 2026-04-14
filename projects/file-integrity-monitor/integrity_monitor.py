import argparse, hashlib, json
from pathlib import Path


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def snapshot_dir(directory):
    base = Path(directory)
    data = {}
    for path in sorted(base.rglob('*')):
        if path.is_file():
            data[str(path.relative_to(base))] = sha256_file(path)
    return data


def diff_snapshots(old, new):
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    changed = sorted(k for k in set(old) & set(new) if old[k] != new[k])
    return {'added': added, 'removed': removed, 'changed': changed}


def main(argv=None):
    p = argparse.ArgumentParser(description='File integrity monitor')
    p.add_argument('command', choices=['scan', 'diff'])
    p.add_argument('path')
    p.add_argument('--baseline')
    args = p.parse_args(argv)
    if args.command == 'scan':
        print(json.dumps(snapshot_dir(args.path), indent=2))
    else:
        old = json.loads(Path(args.baseline).read_text())
        new = snapshot_dir(args.path)
        print(json.dumps(diff_snapshots(old, new), indent=2))

if __name__ == '__main__':
    main()
