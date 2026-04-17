const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs/promises');
const os = require('os');
const path = require('path');
const {
  buildBucketConfig,
  bucketFor,
  organize,
  writeManifest,
  undoFromManifest,
  parseArgs,
  formatTextReport,
  uniqueDestination,
  loadBucketConfig,
  lintBucketConfig,
  previewNormalizedBucketConfig,
  writeNormalizedBucketConfig,
  listPresetCatalog,
  loadPresetBucketConfig,
  writePresetConfig,
} = require('./organizer');

test('bucketFor categorizes by default extension groups', () => {
  assert.equal(bucketFor('photo.png'), 'images');
  assert.equal(bucketFor('notes.md'), 'documents');
  assert.equal(bucketFor('main.py'), 'code');
  assert.equal(bucketFor('archive.zip'), 'archives');
  assert.equal(bucketFor('mystery.bin'), 'other');
});

test('buildBucketConfig merges custom buckets before defaults and normalizes extensions', () => {
  const bucketConfig = buildBucketConfig({
    buckets: {
      datasets: ['csv', '.JSON', '.csv'],
      slides: ['ppt', '.pptx'],
    },
  });

  assert.equal(bucketFor('results.csv', bucketConfig), 'datasets');
  assert.equal(bucketFor('report.json', bucketConfig), 'datasets');
  assert.equal(bucketFor('lecture.pptx', bucketConfig), 'slides');
  assert.equal(bucketFor('notes.txt', bucketConfig), 'documents');
  assert.deepEqual(bucketConfig.customBuckets.datasets, ['.csv', '.json']);
});

test('buildBucketConfig rejects duplicate custom extensions across buckets', () => {
  assert.throws(
    () => buildBucketConfig({
      buckets: {
        datasets: ['.csv'],
        spreadsheets: ['csv'],
      },
    }),
    /assigned to multiple custom buckets/,
  );
});

test('loadBucketConfig reads JSON config files from disk', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-config-'));
  const configPath = path.join(tmp, 'bucket-config.json');
  await fs.writeFile(configPath, JSON.stringify({
    buckets: {
      datasets: ['csv', 'tsv'],
    },
    fallbackBucket: 'misc',
  }));

  const bucketConfig = await loadBucketConfig(configPath);

  assert.equal(bucketConfig.configPath, path.resolve(configPath));
  assert.equal(bucketFor('values.tsv', bucketConfig), 'datasets');
  assert.equal(bucketFor('mystery.bin', bucketConfig), 'misc');
});

test('loadBucketConfig rejects invalid extendDefaults values and normalized bucket collisions', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-config-invalid-'));
  const invalidExtendDefaultsPath = path.join(tmp, 'invalid-extend-defaults.json');
  await fs.writeFile(invalidExtendDefaultsPath, JSON.stringify({
    buckets: {
      datasets: ['csv'],
    },
    extendDefaults: 'yes please',
  }));

  await assert.rejects(
    loadBucketConfig(invalidExtendDefaultsPath),
    /Field "extendDefaults" must be true or false when provided\./,
  );

  const duplicateBucketNamesPath = path.join(tmp, 'duplicate-bucket-names.json');
  await fs.writeFile(duplicateBucketNamesPath, JSON.stringify({
    buckets: {
      datasets: ['csv'],
      ' datasets ': ['tsv'],
    },
  }));

  await assert.rejects(
    loadBucketConfig(duplicateBucketNamesPath),
    /Bucket names normalize to the same directory name/,
  );
});

test('lintBucketConfig reports normalized-extension warnings for shareable configs', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-config-lint-'));
  const configPath = path.join(tmp, 'shared-buckets.json');
  await fs.writeFile(configPath, JSON.stringify({
    buckets: {
      ' datasets ': ['CSV', '.csv'],
      slides: ['pptx'],
    },
    fallbackBucket: ' misc ',
    extraMetadata: 'ignored by organize runs',
  }, null, 2));

  const result = await lintBucketConfig(configPath);

  assert.equal(result.valid, true);
  assert.equal(result.errors.length, 0);
  assert.equal(result.warnings.length, 6);
  assert.match(result.warnings[0], /Unknown top-level key "extraMetadata" will be ignored/);
  assert.match(result.warnings[1], /Fallback bucket " misc " will normalize to "misc"\./);
  assert.match(result.warnings[2], /Bucket name " datasets " will normalize to "datasets"\./);
  assert.match(result.warnings[3], /Bucket datasets extension "CSV" will normalize to "\.csv"\./);
  assert.match(result.warnings[4], /Bucket datasets repeats extension "\.csv"/);
  assert.match(result.warnings[5], /Bucket slides extension "pptx" will normalize to "\.pptx"\./);
  assert.equal(result.normalizedConfig.fallbackBucket, 'misc');
  assert.deepEqual(result.normalizedConfig.buckets.datasets, ['.csv']);
});

test('lintBucketConfig returns CI-friendly invalid results for broken shared configs', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-config-lint-invalid-'));
  const configPath = path.join(tmp, 'broken-buckets.json');
  await fs.writeFile(configPath, JSON.stringify({
    buckets: {
      datasets: ['csv'],
      archives: ['.csv'],
    },
    extendDefaults: 'false',
  }, null, 2));

  const result = await lintBucketConfig(configPath);

  assert.equal(result.valid, false);
  assert.equal(result.normalizedConfig, null);
  assert.match(result.errors[0], /Field "extendDefaults" must be true or false when provided\./);
  assert.match(result.errors[1], /Extension \.csv is assigned to multiple custom buckets/);
});

test('previewNormalizedBucketConfig summarizes normalization rewrites before writing files', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-config-preview-'));
  const configPath = path.join(tmp, 'shared-buckets.json');
  await fs.writeFile(configPath, JSON.stringify({
    buckets: {
      slides: ['pptx', '.pptx'],
      ' datasets ': ['CSV', '.parquet'],
    },
    fallbackBucket: ' misc ',
    owner: 'team-shared',
  }, null, 2));

  const result = await previewNormalizedBucketConfig(configPath);

  assert.equal(result.valid, true);
  assert.equal(result.rewriteNeeded, true);
  assert.equal(result.errors.length, 0);
  assert.equal(result.warnings.length, 6);
  assert.deepEqual(result.normalizedConfig, {
    buckets: {
      datasets: ['.csv', '.parquet'],
      slides: ['.pptx'],
    },
    fallbackBucket: 'misc',
    extendDefaults: true,
  });
  assert.match(result.changes[0], /Remove unknown top-level key "owner"\./);
assert.match(result.changes.join('\n'), /Normalize fallback bucket " misc " -> "misc"\./);
  assert.match(result.changes.join('\n'), /Normalize bucket name " datasets " -> "datasets"\./);
  assert.match(result.changes.join('\n'), /Normalize extension for bucket datasets: "CSV" -> "\.csv"\./);
  assert.match(result.changes.join('\n'), /Remove duplicate extension "\.pptx" from bucket slides\./);
  assert.match(result.changes.join('\n'), /Sort custom bucket names into canonical order\./);
  assert.match(result.changes.join('\n'), /Add default extendDefaults=true\./);
});

test('previewNormalizedBucketConfig reports canonical configs without rewrite noise', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-config-preview-clean-'));
  const configPath = path.join(tmp, 'shared-buckets.json');
  await fs.writeFile(configPath, JSON.stringify({
    buckets: {
      datasets: ['.csv'],
      slides: ['.pptx'],
    },
    fallbackBucket: 'misc',
    extendDefaults: true,
  }, null, 2));

  const result = await previewNormalizedBucketConfig(configPath);

  assert.equal(result.valid, true);
  assert.equal(result.rewriteNeeded, false);
  assert.deepEqual(result.changes, []);
  assert.equal(result.warnings.length, 0);
});

test('writeNormalizedBucketConfig resolves lint warnings into canonical shareable JSON', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-config-normalize-'));
  const sourcePath = path.join(tmp, 'shared-buckets.json');
  const destinationPath = path.join(tmp, 'normalized', 'shared-buckets.normalized.json');
  await fs.writeFile(sourcePath, JSON.stringify({
    buckets: {
      slides: ['pptx', '.pptx'],
      ' datasets ': ['CSV', '.parquet'],
    },
    fallbackBucket: ' misc ',
    owner: 'team-shared',
  }, null, 2));

  const result = await writeNormalizedBucketConfig(sourcePath, destinationPath);
  const payload = JSON.parse(await fs.readFile(destinationPath, 'utf8'));

  assert.equal(result.destination, path.resolve(destinationPath));
  assert.equal(result.inPlace, false);
  assert.equal(result.resolvedWarnings.length, 6);
  assert.deepEqual(payload, {
    buckets: {
      datasets: ['.csv', '.parquet'],
      slides: ['.pptx'],
    },
    fallbackBucket: 'misc',
    extendDefaults: true,
  });
});

test('writeNormalizedBucketConfig supports in-place fixes and rejects invalid or clobbering writes', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-config-fix-'));
  const configPath = path.join(tmp, 'shared-buckets.json');
  await fs.writeFile(configPath, JSON.stringify({
    buckets: {
      ' datasets ': ['CSV', '.csv'],
    },
    fallbackBucket: ' misc ',
  }, null, 2));

  const inPlaceResult = await writeNormalizedBucketConfig(configPath, configPath);
  const payload = JSON.parse(await fs.readFile(configPath, 'utf8'));
  assert.equal(inPlaceResult.inPlace, true);
  assert.deepEqual(payload, {
    buckets: {
      datasets: ['.csv'],
    },
    fallbackBucket: 'misc',
    extendDefaults: true,
  });

  const existingDestination = path.join(tmp, 'already-exists.json');
  await fs.writeFile(existingDestination, '{}\n');
  await assert.rejects(
    writeNormalizedBucketConfig(configPath, existingDestination),
    /Normalized config destination already exists/,
  );

  const invalidPath = path.join(tmp, 'broken-buckets.json');
  await fs.writeFile(invalidPath, JSON.stringify({
    buckets: {
      datasets: ['csv'],
      archives: ['.csv'],
    },
  }, null, 2));
  await assert.rejects(
    writeNormalizedBucketConfig(invalidPath, path.join(tmp, 'broken.normalized.json')),
    /Cannot normalize invalid config/,
  );
});

test('listPresetCatalog exposes named bucket presets', () => {
  const presets = listPresetCatalog();
  const names = presets.map(preset => preset.name);

  assert.deepEqual(names, ['coursework', 'data-science', 'frontend-assets']);
  assert.deepEqual(presets[0].bucketNames, ['datasets', 'notebooks', 'slides', 'diagrams']);
  assert.equal(presets[1].fallbackBucket, 'lab-misc');
});

test('loadPresetBucketConfig builds organize-ready rules from a named preset', () => {
  const bucketConfig = loadPresetBucketConfig('data-science');

  assert.equal(bucketConfig.presetName, 'data-science');
  assert.equal(bucketFor('results.parquet', bucketConfig), 'datasets');
  assert.equal(bucketFor('analysis.ipynb', bucketConfig), 'notebooks');
  assert.equal(bucketFor('plot.png', bucketConfig), 'figures');
});

test('writePresetConfig writes sharable preset JSON and honors force overwrite', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-preset-'));
  const destination = path.join(tmp, 'coursework.json');

  const firstWrite = await writePresetConfig('coursework', destination);
  assert.equal(firstWrite.destination, path.resolve(destination));
  assert.equal(firstWrite.bucketCount, 4);
  const payload = JSON.parse(await fs.readFile(destination, 'utf8'));
  assert.equal(payload.fallbackBucket, 'coursework-misc');
  assert.deepEqual(payload.buckets.slides, ['.ppt', '.pptx', '.key']);

  await assert.rejects(
    writePresetConfig('coursework', destination),
    /Preset destination already exists/,
  );

  const secondWrite = await writePresetConfig('coursework', destination, { force: true });
  assert.equal(secondWrite.presetName, 'coursework');
});

test('exported preset configs round-trip through loadBucketConfig for shared reuse', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-preset-roundtrip-'));
  const destination = path.join(tmp, 'frontend-assets.json');

  await writePresetConfig('frontend-assets', destination);
  const bucketConfig = await loadBucketConfig(destination);

  assert.equal(bucketConfig.configPath, path.resolve(destination));
  assert.equal(bucketFor('mockup.fig', bucketConfig), 'mockups');
  assert.equal(bucketFor('walkthrough.webm', bucketConfig), 'captures');
  assert.equal(bucketFor('notes.docx', bucketConfig), 'handoff');
  assert.equal(bucketFor('readme.md', bucketConfig), 'documents');
});

test('preset helpers reject unknown preset names with the supported preset list', async () => {
  assert.throws(
    () => loadPresetBucketConfig('unknown-preset'),
    /Unknown preset: unknown-preset\. Supported presets: coursework, data-science, frontend-assets/,
  );

  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-preset-unknown-'));
  await assert.rejects(
    writePresetConfig('unknown-preset', path.join(tmp, 'unknown.json')),
    /Unknown preset: unknown-preset\. Supported presets: coursework, data-science, frontend-assets/,
  );
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

test('organize honors config-driven buckets and custom fallback buckets', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-'));
  const bucketConfig = buildBucketConfig({
    buckets: {
      datasets: ['csv'],
      slides: ['pptx'],
    },
    fallbackBucket: 'misc',
  });
  await fs.writeFile(path.join(tmp, 'grades.csv'), 'scores');
  await fs.writeFile(path.join(tmp, 'week1.pptx'), 'slides');
  await fs.writeFile(path.join(tmp, 'unknown.bin'), 'blob');

  const result = await organize(tmp, { bucketConfig });

  assert.equal(result.summary.total, 3);
  assert.equal(await fs.readFile(path.join(tmp, 'datasets', 'grades.csv'), 'utf8'), 'scores');
  assert.equal(await fs.readFile(path.join(tmp, 'slides', 'week1.pptx'), 'utf8'), 'slides');
  assert.equal(await fs.readFile(path.join(tmp, 'misc', 'unknown.bin'), 'utf8'), 'blob');
  assert.equal(result.bucketConfig.fallbackBucket, 'misc');
});

test('organize can use a named preset directly without a config file on disk', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-'));
  const bucketConfig = loadPresetBucketConfig('frontend-assets');
  await fs.writeFile(path.join(tmp, 'hero.fig'), 'figma');
  await fs.writeFile(path.join(tmp, 'walkthrough.mov'), 'video');
  await fs.writeFile(path.join(tmp, 'notes.txt'), 'handoff');

  const result = await organize(tmp, { bucketConfig });

  assert.equal(result.summary.total, 3);
  assert.equal(result.bucketConfig.presetName, 'frontend-assets');
  assert.equal(await fs.readFile(path.join(tmp, 'mockups', 'hero.fig'), 'utf8'), 'figma');
  assert.equal(await fs.readFile(path.join(tmp, 'captures', 'walkthrough.mov'), 'utf8'), 'video');
  assert.equal(await fs.readFile(path.join(tmp, 'documents', 'notes.txt'), 'utf8'), 'handoff');
});

test('organize skips the config file itself when it lives inside the target directory', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-'));
  const configPath = path.join(tmp, 'buckets.json');
  await fs.writeFile(path.join(tmp, 'grades.csv'), 'scores');
  await fs.writeFile(configPath, JSON.stringify({
    buckets: {
      datasets: ['csv'],
    },
  }));

  const bucketConfig = await loadBucketConfig(configPath);
  const result = await organize(tmp, { bucketConfig, recursive: true });

  assert.equal(result.summary.total, 1);
  assert.equal(await fs.readFile(path.join(tmp, 'datasets', 'grades.csv'), 'utf8'), 'scores');
  assert.equal(await fs.readFile(configPath, 'utf8').then(JSON.parse).then(config => config.buckets.datasets[0]), 'csv');
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

test('organize recursively handles nested folders but skips configured bucket folders', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-'));
  const bucketConfig = buildBucketConfig({
    buckets: {
      datasets: ['csv'],
    },
  });
  await fs.mkdir(path.join(tmp, 'semester1'), { recursive: true });
  await fs.mkdir(path.join(tmp, 'datasets'), { recursive: true });
  await fs.writeFile(path.join(tmp, 'semester1', 'table.csv'), 'csv');
  await fs.writeFile(path.join(tmp, 'datasets', 'kept.csv'), 'keep');

  const result = await organize(tmp, { recursive: true, bucketConfig });

  assert.equal(result.summary.total, 1);
  const nestedMoved = await fs.readFile(path.join(tmp, 'semester1', 'datasets', 'table.csv'), 'utf8');
  const bucketPreserved = await fs.readFile(path.join(tmp, 'datasets', 'kept.csv'), 'utf8');
  assert.equal(nestedMoved, 'csv');
  assert.equal(bucketPreserved, 'keep');
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

test('parseArgs supports config, preset, lint, normalized-config, preset-export, and undo flags', () => {
  const organizeArgs = parseArgs(['~/Downloads', '--dry-run', '--recursive', '--json', '--config', 'buckets.json', '--manifest-out', 'runs/latest.json']);
  assert.equal(organizeArgs.targetDir, '~/Downloads');
  assert.deepEqual(organizeArgs.options, {
    dryRun: true,
    recursive: true,
    json: true,
    manifestOut: 'runs/latest.json',
    undoManifest: null,
    configPath: 'buckets.json',
    lintConfigPath: null,
    previewConfigPath: null,
    fixConfigPath: null,
    writeNormalizedConfigSource: null,
    writeNormalizedConfigDestination: null,
    presetName: null,
    listPresets: false,
    writePresetName: null,
    writePresetDestination: null,
    force: false,
  });

  const presetArgs = parseArgs(['~/Downloads', '--preset', 'coursework', '--manifest-out', 'runs/latest.json']);
  assert.deepEqual(presetArgs.options, {
    dryRun: false,
    recursive: false,
    json: false,
    manifestOut: 'runs/latest.json',
    undoManifest: null,
    configPath: null,
    lintConfigPath: null,
    previewConfigPath: null,
    fixConfigPath: null,
    writeNormalizedConfigSource: null,
    writeNormalizedConfigDestination: null,
    presetName: 'coursework',
    listPresets: false,
    writePresetName: null,
    writePresetDestination: null,
    force: false,
  });

  const undoArgs = parseArgs(['--undo', 'runs/latest.json', '--dry-run', '--json']);
  assert.equal(undoArgs.targetDir, '.');
  assert.deepEqual(undoArgs.options, {
    dryRun: true,
    recursive: false,
    json: true,
    manifestOut: null,
    undoManifest: 'runs/latest.json',
    configPath: null,
    lintConfigPath: null,
    previewConfigPath: null,
    fixConfigPath: null,
    writeNormalizedConfigSource: null,
    writeNormalizedConfigDestination: null,
    presetName: null,
    listPresets: false,
    writePresetName: null,
    writePresetDestination: null,
    force: false,
  });

  const listArgs = parseArgs(['--list-presets', '--json']);
  assert.equal(listArgs.options.listPresets, true);
  assert.equal(listArgs.options.json, true);

  const writePresetArgs = parseArgs(['--write-preset', 'data-science', 'presets/data-science.json', '--force', '--json']);
  assert.deepEqual(writePresetArgs.options, {
    dryRun: false,
    recursive: false,
    json: true,
    manifestOut: null,
    undoManifest: null,
    configPath: null,
    lintConfigPath: null,
    previewConfigPath: null,
    fixConfigPath: null,
    writeNormalizedConfigSource: null,
    writeNormalizedConfigDestination: null,
    presetName: null,
    listPresets: false,
    writePresetName: 'data-science',
    writePresetDestination: 'presets/data-science.json',
    force: true,
  });

  const lintArgs = parseArgs(['--lint-config', 'shared/buckets.json', '--json']);
  assert.deepEqual(lintArgs.options, {
    dryRun: false,
    recursive: false,
    json: true,
    manifestOut: null,
    undoManifest: null,
    configPath: null,
    lintConfigPath: 'shared/buckets.json',
    previewConfigPath: null,
    fixConfigPath: null,
    writeNormalizedConfigSource: null,
    writeNormalizedConfigDestination: null,
    presetName: null,
    listPresets: false,
    writePresetName: null,
    writePresetDestination: null,
    force: false,
  });

  const previewArgs = parseArgs(['--preview-normalized-config', 'shared/buckets.json', '--json']);
  assert.deepEqual(previewArgs.options, {
    dryRun: false,
    recursive: false,
    json: true,
    manifestOut: null,
    undoManifest: null,
    configPath: null,
    lintConfigPath: null,
    previewConfigPath: 'shared/buckets.json',
    fixConfigPath: null,
    writeNormalizedConfigSource: null,
    writeNormalizedConfigDestination: null,
    presetName: null,
    listPresets: false,
    writePresetName: null,
    writePresetDestination: null,
    force: false,
  });

  const fixConfigArgs = parseArgs(['--fix-config', 'shared/buckets.json', '--json']);
  assert.deepEqual(fixConfigArgs.options, {
    dryRun: false,
    recursive: false,
    json: true,
    manifestOut: null,
    undoManifest: null,
    configPath: null,
    lintConfigPath: null,
    previewConfigPath: null,
    fixConfigPath: 'shared/buckets.json',
    writeNormalizedConfigSource: null,
    writeNormalizedConfigDestination: null,
    presetName: null,
    listPresets: false,
    writePresetName: null,
    writePresetDestination: null,
    force: false,
  });

  const writeNormalizedArgs = parseArgs(['--write-normalized-config', 'shared/raw.json', 'shared/clean.json', '--force', '--json']);
  assert.deepEqual(writeNormalizedArgs.options, {
    dryRun: false,
    recursive: false,
    json: true,
    manifestOut: null,
    undoManifest: null,
    configPath: null,
    lintConfigPath: null,
    previewConfigPath: null,
    fixConfigPath: null,
    writeNormalizedConfigSource: 'shared/raw.json',
    writeNormalizedConfigDestination: 'shared/clean.json',
    presetName: null,
    listPresets: false,
    writePresetName: null,
    writePresetDestination: null,
    force: true,
  });

  assert.throws(
    () => parseArgs(['--undo', 'runs/latest.json', '--manifest-out', 'other.json']),
    /--manifest-out cannot be used with --undo/,
  );

  assert.throws(
    () => parseArgs(['--undo', 'runs/latest.json', '--config', 'buckets.json']),
    /--config cannot be used with --undo/,
  );

  assert.throws(
    () => parseArgs(['~/Downloads', '--config', 'buckets.json', '--preset', 'coursework']),
    /--config cannot be combined with --preset/,
  );

  assert.throws(
    () => parseArgs(['--list-presets', '~/Downloads']),
    /Target directory cannot be combined with --list-presets/,
  );

  assert.throws(
    () => parseArgs(['--list-presets', '--dry-run']),
    /--list-presets only supports optional --json output/,
  );

  assert.throws(
    () => parseArgs(['--lint-config', 'shared/buckets.json', '--config', 'other.json']),
    /--lint-config cannot be combined with organize, undo, preset, or normalized-config-write flags/,
  );

  assert.throws(
    () => parseArgs(['--preview-normalized-config', 'shared/buckets.json', '--force']),
    /--preview-normalized-config cannot be combined with organize, undo, lint, preset, or normalized-config-write flags/,
  );

  assert.throws(
    () => parseArgs(['--fix-config', 'shared/buckets.json', '--force']),
    /--fix-config cannot be combined with organize, undo, lint, preset, or normalized-config-export flags/,
  );

  assert.throws(
    () => parseArgs(['--write-normalized-config', 'shared/raw.json', 'shared/clean.json', '--preset', 'coursework']),
    /--write-normalized-config cannot be combined with organize, undo, lint, or preset flags/,
  );

  assert.throws(
    () => parseArgs(['--write-preset', 'coursework', 'preset.json', '--dry-run']),
    /--write-preset cannot be combined with organize, lint, normalized-config, or undo flags/,
  );

  assert.throws(
    () => parseArgs(['--force']),
    /--force can only be used with --write-preset or --write-normalized-config/,
  );
});

test('formatTextReport includes config, preset, manifest, lint, and normalized-config details for supported actions', () => {
  const organizeReport = formatTextReport({
    action: 'organize',
    rootDir: '/tmp/demo',
    dryRun: true,
    recursive: false,
    bucketConfig: {
      configPath: '/tmp/demo/buckets.json',
      presetName: 'coursework',
      extendDefaults: true,
      fallbackBucket: 'other',
      bucketNames: ['datasets', 'documents', 'other'],
      customBuckets: { datasets: ['.csv'] },
    },
    manifestPath: '/tmp/demo/manifests/latest.json',
    summary: { total: 1, renamed: 1, byBucket: { datasets: 1 } },
    moves: [{ from: '/tmp/demo/a.csv', to: '/tmp/demo/datasets/a (1).csv', renamed: true }],
  });

  const undoReport = formatTextReport({
    action: 'undo',
    rootDir: '/tmp/demo',
    dryRun: false,
    manifestPath: '/tmp/demo/manifests/latest.json',
    summary: { total: 1, restored: 1, missing: 0, restoreRenamed: 1, removedDirectories: 1, byBucket: { documents: 1 } },
    moves: [{ from: '/tmp/demo/documents/a.txt', to: '/tmp/demo/a (1).txt', requestedRestore: '/tmp/demo/a.txt', restoreRenamed: true, status: 'restored', bucket: 'documents' }],
  });

  const listPresetsReport = formatTextReport({
    action: 'list-presets',
    presets: [{ name: 'coursework', description: 'demo', bucketNames: ['datasets', 'slides'], fallbackBucket: 'misc', extendDefaults: true }],
  });

  const writePresetReport = formatTextReport({
    action: 'write-preset',
    presetName: 'coursework',
    destination: '/tmp/demo/coursework.json',
    fallbackBucket: 'misc',
    extendDefaults: true,
    bucketNames: ['datasets', 'slides'],
  });

  const lintConfigReport = formatTextReport({
    action: 'lint-config',
    configPath: '/tmp/demo/shared-buckets.json',
    valid: true,
    warnings: ['Bucket datasets extension "CSV" will normalize to ".csv".'],
    errors: [],
    normalizedConfig: {
      buckets: { datasets: ['.csv'] },
      fallbackBucket: 'misc',
      extendDefaults: true,
    },
  });

  const previewConfigReport = formatTextReport({
    action: 'preview-normalized-config',
    configPath: '/tmp/demo/shared-buckets.json',
    valid: true,
    rewriteNeeded: true,
    changes: ['Normalize fallback bucket " misc " -> "misc".'],
    warnings: ['Bucket datasets extension "CSV" will normalize to ".csv".'],
    errors: [],
    normalizedConfig: {
      buckets: { datasets: ['.csv'] },
      fallbackBucket: 'misc',
      extendDefaults: true,
    },
  });

  const writeNormalizedConfigReport = formatTextReport({
    action: 'write-normalized-config',
    configPath: '/tmp/demo/shared-buckets.json',
    destination: '/tmp/demo/shared-buckets.normalized.json',
    inPlace: false,
    resolvedWarnings: ['Bucket datasets extension "CSV" will normalize to ".csv".'],
    normalizedConfig: {
      buckets: { datasets: ['.csv'] },
      fallbackBucket: 'misc',
      extendDefaults: true,
    },
  });

  assert.match(organizeReport, /preset: coursework/);
  assert.match(organizeReport, /config: \/tmp\/demo\/buckets\.json/);
  assert.match(organizeReport, /manifest: \/tmp\/demo\/manifests\/latest\.json/);
  assert.match(organizeReport, /renamed to avoid collisions: 1/);
  assert.match(undoReport, /action: undo/);
  assert.match(undoReport, /renamed to avoid restore collisions: 1/);
  assert.match(undoReport, /restore-renamed from \/tmp\/demo\/a\.txt/);
  assert.match(listPresetsReport, /action: list-presets/);
  assert.match(listPresetsReport, /extends defaults: yes/);
  assert.match(writePresetReport, /destination: \/tmp\/demo\/coursework\.json/);
  assert.match(writePresetReport, /extends defaults: yes/);
  assert.match(lintConfigReport, /action: lint-config/);
  assert.match(lintConfigReport, /status: valid/);
  assert.match(lintConfigReport, /warning 1: Bucket datasets extension "CSV" will normalize to "\.csv"\./);
  assert.match(lintConfigReport, /No errors found\./);
  assert.match(previewConfigReport, /action: preview-normalized-config/);
  assert.match(previewConfigReport, /rewrite needed: yes/);
  assert.match(previewConfigReport, /change 1: Normalize fallback bucket " misc " -> "misc"\./);
  assert.match(previewConfigReport, /Preview only\. Use --fix-config or --write-normalized-config to apply these changes\./);
  assert.match(writeNormalizedConfigReport, /action: write-normalized-config/);
  assert.match(writeNormalizedConfigReport, /destination: \/tmp\/demo\/shared-buckets\.normalized\.json/);
  assert.match(writeNormalizedConfigReport, /mode: copy/);
  assert.match(writeNormalizedConfigReport, /resolved warning 1: Bucket datasets extension "CSV" will normalize to "\.csv"\./);
  assert.match(writeNormalizedConfigReport, /Normalized config written\./);
});
