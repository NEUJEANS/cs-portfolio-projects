import argparse, json, uuid
from pathlib import Path

class TaskTracker:
    def __init__(self, storage_path='tasks.json'):
        self.path = Path(storage_path)
        self.tasks = self._load()

    def _load(self):
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text())

    def _save(self):
        self.path.write_text(json.dumps(self.tasks, indent=2))

    def add(self, title, priority='medium'):
        task = {'id': str(uuid.uuid4())[:8], 'title': title, 'priority': priority, 'done': False}
        self.tasks.append(task)
        self._save()
        return task

    def list(self, include_done=True):
        return [t for t in self.tasks if include_done or not t['done']]

    def complete(self, task_id):
        for task in self.tasks:
            if task['id'] == task_id:
                task['done'] = True
                self._save()
                return task
        raise ValueError('task not found')

    def remove(self, task_id):
        before = len(self.tasks)
        self.tasks = [t for t in self.tasks if t['id'] != task_id]
        if len(self.tasks) == before:
            raise ValueError('task not found')
        self._save()


def build_parser():
    p = argparse.ArgumentParser(description='Task tracker CLI')
    p.add_argument('--storage', default='tasks.json')
    sub = p.add_subparsers(dest='cmd', required=True)
    add = sub.add_parser('add')
    add.add_argument('title')
    add.add_argument('--priority', choices=['low', 'medium', 'high'], default='medium')
    sub.add_parser('list').add_argument('--pending-only', action='store_true')
    done = sub.add_parser('done')
    done.add_argument('task_id')
    rm = sub.add_parser('remove')
    rm.add_argument('task_id')
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    tracker = TaskTracker(args.storage)
    if args.cmd == 'add':
        t = tracker.add(args.title, args.priority)
        print(f"added {t['id']}: {t['title']}")
    elif args.cmd == 'list':
        tasks = tracker.list(include_done=not args.pending_only)
        for t in tasks:
            mark = 'x' if t['done'] else ' '
            print(f"[{mark}] {t['id']} {t['title']} ({t['priority']})")
    elif args.cmd == 'done':
        t = tracker.complete(args.task_id)
        print(f"completed {t['id']}")
    elif args.cmd == 'remove':
        tracker.remove(args.task_id)
        print(f'removed {args.task_id}')

if __name__ == '__main__':
    main()
