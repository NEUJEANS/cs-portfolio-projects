const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs/promises');
const os = require('os');
const path = require('path');
const {
  bucketFor,
  organize,
  writeManifest,
  undoFromManifest,
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

test('writeManifest persists organize results and undo restores files plus empty bucket cleanup', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-'));
  const manifestPath = path.join(tmp, 'artifacts', 'organize-manifest.json');
  await fs.writeFile(path.join(tmp, 'notes.txt'), 'draft');

  const organizeResult = await organize(tmp);
  const manifest = await writeManifest(organizeResult, manifestPath);
  const undoResult = await undoFromManifest(manifestPath);

  assert.equal(manifest.manifestPath, path.resolve(manifestPath));
  const restored = await fs.readFile(path.join(tmp, 'notes.txt'), 'utf8');
  assert.equal(restored, 'draft');
  assert.equal(await fs.readFile(path.join(manifestPath), 'utf8').then(Boolean), true);
  await assert.rejects(fs.access(path.join(tmp, 'documents')));
  assert.equal(undoResult.summary.restored, 1);
  assert.equal(undoResult.summary.removedDirectories, 1);
});

test('undo dry-run previews restore work without mutating the filesystem', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-'));
  const manifestPath = path.join(tmp, 'undo-manifest.json');
  await fs.writeFile(path.join(tmp, 'song.mp3'), 'audio');

  const organizeResult = await organize(tmp);
  await writeManifest(organizeResult, manifestPath);
  const undoResult = await undoFromManifest(manifestPath, { dryRun: true });

  const stillOrganized = await fs.readFile(path.join(tmp, 'audio', 'song.mp3'), 'utf8');
  assert.equal(stillOrganized, 'audio');
  await assert.rejects(fs.access(path.join(tmp, 'song.mp3')));
  assert.equal(undoResult.dryRun, true);
  assert.equal(undoResult.summary.restored, 1);
  assert.equal(undoResult.summary.removedDirectories, 0);
});

test('undo renames restore target when the original source path is occupied', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-'));
  const manifestPath = path.join(tmp, 'undo-manifest.json');
  await fs.writeFile(path.join(tmp, 'notes.txt'), 'first');

  const organizeResult = await organize(tmp);
  await writeManifest(organizeResult, manifestPath);
  await fs.writeFile(path.join(tmp, 'notes.txt'), 'replacement');

  const undoResult = await undoFromManifest(manifestPath);

  const restored = await fs.readFile(path.join(tmp, 'notes (1).txt'), 'utf8');
  const replacement = await fs.readFile(path.join(tmp, 'notes.txt'), 'utf8');
  assert.equal(restored, 'first');
  assert.equal(replacement, 'replacement');
  assert.equal(undoResult.summary.restoreRenamed, 1);
});

test('undo rejects manifests created from dry-run results', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-'));
  const manifestPath = path.join(tmp, 'undo-manifest.json');
  await fs.writeFile(path.join(tmp, 'notes.txt'), 'draft');

  const organizeResult = await organize(tmp, { dryRun: true });
  await writeManifest(organizeResult, manifestPath);

  await assert.rejects(
    undoFromManifest(manifestPath),
    /Cannot undo a dry-run manifest/,
  );
});

test('parseArgs supports manifest-out and undo flags', () => {
  const organizeArgs = parseArgs(['~/Downloads', '--dry-run', '--recursive', '--json', '--manifest-out', 'runs/latest.json']);
  assert.equal(organizeArgs.targetDir, '~/Downloads');
  assert.deepEqual(organizeArgs.options, {
    dryRun: true,
    recursive: true,
    json: true,
    manifestOut: 'runs/latest.json',
    undoManifest: null,
  });

  const undoArgs = parseArgs(['--undo', 'runs/latest.json', '--dry-run', '--json']);
  assert.equal(undoArgs.targetDir, '.');
  assert.deepEqual(undoArgs.options, {
    dryRun: true,
    recursive: false,
    json: true,
    manifestOut: null,
    undoManifest: 'runs/latest.json',
  });

  assert.throws(
    () => parseArgs(['--undo', 'runs/latest.json', '--manifest-out', 'other.json']),
    /--manifest-out cannot be used with --undo/,
  );
});

test('formatTextReport includes manifest and undo summary details', () => {
  const organizeReport = formatTextReport({
    action: 'organize',
    rootDir: '/tmp/demo',
    dryRun: true,
    recursive: false,
    manifestPath: '/tmp/demo/manifests/latest.json',
    summary: { total: 1, renamed: 1, byBucket: { documents: 1 } },
    moves: [{ from: '/tmp/demo/a.txt', to: '/tmp/demo/documents/a (1).txt', renamed: true }],
  });

  const undoReport = formatTextReport({
    action: 'undo',
    rootDir: '/tmp/demo',
    dryRun: false,
    manifestPath: '/tmp/demo/manifests/latest.json',
    summary: { total: 1, restored: 1, missing: 0, restoreRenamed: 1, removedDirectories: 1, byBucket: { documents: 1 } },
    moves: [{ from: '/tmp/demo/documents/a.txt', to: '/tmp/demo/a (1).txt', requestedRestore: '/tmp/demo/a.txt', restoreRenamed: true, status: 'restored', bucket: 'documents' }],
  });

  assert.match(organizeReport, /manifest: \/tmp\/demo\/manifests\/latest\.json/);
  assert.match(organizeReport, /renamed to avoid collisions: 1/);
  assert.match(undoReport, /action: undo/);
  assert.match(undoReport, /renamed to avoid restore collisions: 1/);
  assert.match(undoReport, /restore-renamed from \/tmp\/demo\/a\.txt/);
});
