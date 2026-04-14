const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs/promises');
const os = require('os');
const path = require('path');
const {
  bucketFor,
  organize,
  parseArgs,
  formatTextReport,
  uniqueDestination,
} = require('./organizer');

test('bucketFor categorizes by extension', () => {
  assert.equal(bucketFor('photo.png'), 'images');
  assert.equal(bucketFor('notes.md'), 'documents');
  assert.equal(bucketFor('main.py'), 'code');
  assert.equal(bucketFor('archive.zip'), 'archives');
  assert.equal(bucketFor('mystery.bin'), 'other');
});

test('uniqueDestination appends numbered suffix when file exists', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-'));
  const target = path.join(tmp, 'notes.txt');
  await fs.writeFile(target, 'existing');
  const candidate = await uniqueDestination(target);
  assert.equal(candidate, path.join(tmp, 'notes (1).txt'));
});

test('organize moves files into folders and preserves existing targets', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-'));
  await fs.mkdir(path.join(tmp, 'documents'), { recursive: true });
  await fs.writeFile(path.join(tmp, 'documents', 'a.txt'), 'existing');
  await fs.writeFile(path.join(tmp, 'a.txt'), 'new');

  const result = await organize(tmp);

  assert.equal(result.summary.total, 1);
  assert.equal(result.summary.renamed, 1);
  const moved = await fs.readFile(path.join(tmp, 'documents', 'a (1).txt'), 'utf8');
  const existing = await fs.readFile(path.join(tmp, 'documents', 'a.txt'), 'utf8');
  assert.equal(moved, 'new');
  assert.equal(existing, 'existing');
});

test('organize dry-run reports work without mutating the filesystem', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-'));
  await fs.writeFile(path.join(tmp, 'song.mp3'), 'audio');

  const result = await organize(tmp, { dryRun: true });

  assert.equal(result.dryRun, true);
  assert.equal(result.summary.total, 1);
  await assert.rejects(fs.access(path.join(tmp, 'audio', 'song.mp3')));
  const original = await fs.readFile(path.join(tmp, 'song.mp3'), 'utf8');
  assert.equal(original, 'audio');
});

test('organize recursively handles nested folders but skips bucket folders', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-'));
  await fs.mkdir(path.join(tmp, 'semester1'), { recursive: true });
  await fs.mkdir(path.join(tmp, 'images'), { recursive: true });
  await fs.writeFile(path.join(tmp, 'semester1', 'script.js'), 'code');
  await fs.writeFile(path.join(tmp, 'images', 'kept.png'), 'img');

  const result = await organize(tmp, { recursive: true });

  assert.equal(result.summary.total, 1);
  const nestedMoved = await fs.readFile(path.join(tmp, 'semester1', 'code', 'script.js'), 'utf8');
  const bucketPreserved = await fs.readFile(path.join(tmp, 'images', 'kept.png'), 'utf8');
  assert.equal(nestedMoved, 'code');
  assert.equal(bucketPreserved, 'img');
});

test('parseArgs supports dry-run recursive and json flags', () => {
  const parsed = parseArgs(['~/Downloads', '--dry-run', '--recursive', '--json']);
  assert.equal(parsed.targetDir, '~/Downloads');
  assert.deepEqual(parsed.options, { dryRun: true, recursive: true, json: true });
});

test('formatTextReport includes summary details', () => {
  const report = formatTextReport({
    rootDir: '/tmp/demo',
    dryRun: true,
    recursive: false,
    summary: { total: 1, renamed: 1, byBucket: { documents: 1 } },
    moves: [{ from: '/tmp/demo/a.txt', to: '/tmp/demo/documents/a (1).txt', renamed: true }],
  });

  assert.match(report, /mode: dry-run/);
  assert.match(report, /bucket documents: 1/);
  assert.match(report, /renamed to avoid collisions: 1/);
});
