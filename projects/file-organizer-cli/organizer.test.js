const test = require('node:test');
const assert = require('node:assert/strict');
const crypto = require('crypto');
const { execFile: execFileCallback } = require('node:child_process');
const fs = require('fs/promises');
const os = require('os');
const path = require('path');
const { promisify } = require('node:util');
const execFile = promisify(execFileCallback);
const {
  buildBucketConfig,
  bucketFor,
  detectMimeTypeFromBuffer,
  detectMimeTypeFromText,
  detectMimeType,
  classifyFile,
  organize,
  collectProtectedPathsForOrganize,
  writeManifest,
  manifestChecksumFor,
  verifyManifestIntegrity,
  manifestSignatureChecksumFor,
  publicKeyFingerprint,
  normalizeSignerFingerprint,
  loadSignerPolicy,
  writeDetachedManifestSignature,
  verifyDetachedManifestSignature,
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

async function writeEd25519KeyPair(tmpDir, prefix = 'team-organizer-signer') {
  const { privateKey, publicKey } = crypto.generateKeyPairSync('ed25519');
  const keyDir = path.join(tmpDir, 'keys');
  await fs.mkdir(keyDir, { recursive: true });
  const privateKeyPath = path.join(keyDir, `${prefix}.pem`);
  const publicKeyPath = path.join(keyDir, `${prefix}.pub.pem`);
  await fs.writeFile(privateKeyPath, privateKey.export({ format: 'pem', type: 'pkcs8' }));
  await fs.writeFile(publicKeyPath, publicKey.export({ format: 'pem', type: 'spki' }));
  return { privateKeyPath, publicKeyPath };
}

async function writeSignerPolicy(tmpDir, publicKeyPath, overrides = {}) {
  const policyPath = path.join(tmpDir, overrides.filename || 'trusted-signers.json');
  const publicKey = crypto.createPublicKey(await fs.readFile(publicKeyPath, 'utf8'));
  const fingerprint = publicKeyFingerprint(publicKey);
  const policy = {
    name: overrides.name || 'Course staff signing policy',
    description: overrides.description || 'Trusted signing keys for organizer undo approvals.',
    trustedSigners: overrides.trustedSigners || [{
      fingerprint,
      label: overrides.label || 'TA laptop key',
      roles: overrides.roles || ['organize-approver', 'undo-approver'],
      notes: overrides.notes || 'Portfolio demo key',
    }],
  };
  if (overrides.approvalQuorum) {
    policy.approvalQuorum = overrides.approvalQuorum;
  }
  await fs.writeFile(policyPath, `${JSON.stringify(policy, null, 2)}
`);
  return { policyPath, fingerprint, policy };
}

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
  assert.deepEqual(bucketConfig.customBuckets.datasets, {
    extensions: ['.csv', '.json'],
    basenamePatterns: [],
    mimeTypes: [],
    mimePrefixes: [],
  });
});

test('buildBucketConfig supports basename pattern rules before extension fallback buckets', () => {
  const bucketConfig = buildBucketConfig({
    buckets: {
      screenshots: {
        basenamePatterns: ['Screenshot *', ' screen shot * '],
      },
      assignments: {
        basenamePatterns: ['assignment-*'],
      },
    },
  });

  assert.equal(bucketFor('Screenshot 2026-04-18.png', bucketConfig), 'screenshots');
  assert.equal(bucketFor('screen shot 12.PNG', bucketConfig), 'screenshots');
  assert.equal(bucketFor('assignment-2.txt', bucketConfig), 'assignments');
  assert.equal(bucketFor('diagram.png', bucketConfig), 'images');
  assert.deepEqual(bucketConfig.customBuckets.screenshots, {
    extensions: [],
    basenamePatterns: ['screenshot *', 'screen shot *'],
    mimeTypes: [],
    mimePrefixes: [],
  });
});

test('bucketFor supports single-character basename wildcards alongside extension rules', () => {
  const bucketConfig = buildBucketConfig({
    buckets: {
      quizzes: {
        extensions: ['.txt'],
        basenamePatterns: ['quiz-2026-04-1?'],
      },
    },
  });

  assert.equal(bucketFor('quiz-2026-04-18.txt', bucketConfig), 'quizzes');
  assert.equal(bucketFor('quiz-2026-04-19.md', bucketConfig), 'quizzes');
  assert.equal(bucketFor('quiz-2026-04-180.md', bucketConfig), 'documents');
  assert.equal(bucketFor('notes.md', bucketConfig), 'documents');
});



test('buildBucketConfig supports MIME-aware custom bucket rules', () => {
  const bucketConfig = buildBucketConfig({
    buckets: {
      data: {
        mimeTypes: [' Application/JSON '],
      },
      visuals: {
        mimePrefixes: [' image/* '],
      },
    },
  });

  assert.equal(bucketConfig.requiresMimeDetection, true);
  assert.deepEqual(bucketConfig.customBuckets.data, {
    extensions: [],
    basenamePatterns: [],
    mimeTypes: ['application/json'],
    mimePrefixes: [],
  });
  assert.deepEqual(bucketConfig.customBuckets.visuals, {
    extensions: [],
    basenamePatterns: [],
    mimeTypes: [],
    mimePrefixes: ['image/'],
  });
});

test('buildBucketConfig rejects overlapping MIME rules across buckets', () => {
  assert.throws(
    () => buildBucketConfig({
      buckets: {
        data: {
          mimeTypes: ['application/json'],
        },
        textish: {
          mimePrefixes: ['application/*'],
        },
      },
    }),
    /overlaps MIME/,
  );
});

test('detectMimeType helpers classify common text and binary payloads', async () => {
  assert.equal(detectMimeTypeFromText('{\n  "ok": true\n}'), 'application/json');
  assert.equal(detectMimeTypeFromText('<svg viewBox="0 0 10 10"></svg>'), 'image/svg+xml');
  assert.equal(detectMimeTypeFromText('<html><body>hi</body></html>'), 'text/html');
  assert.equal(detectMimeTypeFromText('plain notes go here'), 'text/plain');

  assert.equal(detectMimeTypeFromBuffer(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a])), 'image/png');
  assert.equal(detectMimeTypeFromBuffer(Buffer.from('%PDF-1.7')), 'application/pdf');
  assert.equal(detectMimeTypeFromBuffer(Buffer.from('{"demo":true}\n')), 'application/json');

  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-mime-'));
  const jsonNotesPath = path.join(tmp, 'report.txt');
  await fs.writeFile(jsonNotesPath, '{"records": 3}\n');
  assert.equal(await detectMimeType(jsonNotesPath), 'application/json');
});

test('classifyFile prefers MIME rules before extension fallback when organizing', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-classify-'));
  const bucketConfig = buildBucketConfig({
    buckets: {
      datasets: {
        mimeTypes: ['application/json'],
      },
      visuals: {
        mimePrefixes: ['image/'],
      },
    },
  });

  const misleadingJsonPath = path.join(tmp, 'report.txt');
  const svgPath = path.join(tmp, 'diagram.txt');
  const plainNotesPath = path.join(tmp, 'notes.txt');
  await fs.writeFile(misleadingJsonPath, '{"scores": [1, 2, 3]}\n');
  await fs.writeFile(svgPath, '<svg viewBox="0 0 10 10"></svg>\n');
  await fs.writeFile(plainNotesPath, 'ordinary note\n');

  assert.deepEqual(await classifyFile(misleadingJsonPath, bucketConfig), {
    bucket: 'datasets',
    matchedBy: 'mimeType',
    matchedValue: 'application/json',
    detectedMimeType: 'application/json',
  });
  assert.deepEqual(await classifyFile(svgPath, bucketConfig), {
    bucket: 'visuals',
    matchedBy: 'mimePrefix',
    matchedValue: 'image/',
    detectedMimeType: 'image/svg+xml',
  });
  assert.deepEqual(await classifyFile(plainNotesPath, bucketConfig), {
    bucket: 'documents',
    matchedBy: 'extension',
    matchedValue: '.txt',
    detectedMimeType: 'text/plain',
  });
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

test('buildBucketConfig rejects duplicate basename patterns across buckets', () => {
  assert.throws(
    () => buildBucketConfig({
      buckets: {
        screenshots: {
          basenamePatterns: ['screenshot*'],
        },
        captures: {
          basenamePatterns: [' Screenshot* '],
        },
      },
    }),
    /Basename pattern screenshot\* is assigned to multiple custom buckets/,
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



test('lintBucketConfig normalizes MIME-aware bucket rules and reports duplicates', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-config-mime-lint-'));
  const configPath = path.join(tmp, 'mime-buckets.json');
  await fs.writeFile(configPath, JSON.stringify({
    buckets: {
      datasets: {
        mimeTypes: [' Application/JSON ', 'application/json'],
      },
      visuals: {
        mimePrefixes: [' image/* ', 'image/*'],
      },
    },
  }, null, 2));

  const result = await lintBucketConfig(configPath);

  assert.equal(result.valid, true);
  assert.equal(result.errors.length, 0);
  assert.match(result.warnings.join('\n'), /Bucket datasets MIME type " Application\/JSON " will normalize to "application\/json"\./);
  assert.match(result.warnings.join('\n'), /Bucket datasets repeats MIME type "application\/json"/);
  assert.match(result.warnings.join('\n'), /Bucket visuals MIME prefix " image\/\* " will normalize to "image\/"\./);
  assert.match(result.warnings.join('\n'), /Bucket visuals repeats MIME prefix "image\/"/);
  assert.deepEqual(result.normalizedConfig.buckets, {
    datasets: {
      mimeTypes: ['application/json'],
    },
    visuals: {
      mimePrefixes: ['image/'],
    },
  });
});

test('lintBucketConfig normalizes basename-pattern rule objects and ignored bucket fields', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-config-pattern-lint-'));
  const configPath = path.join(tmp, 'pattern-buckets.json');
  await fs.writeFile(configPath, JSON.stringify({
    buckets: {
      screenshots: {
        extensions: ['PNG'],
        basenamePatterns: [' Screenshot * ', 'screenshot *'],
        matcherNote: 'ignored',
      },
    },
  }, null, 2));

  const result = await lintBucketConfig(configPath);

  assert.equal(result.valid, true);
  assert.equal(result.errors.length, 0);
  assert.match(result.warnings.join('\n'), /Bucket screenshots field "matcherNote" will be ignored by the organizer\./);
  assert.match(result.warnings.join('\n'), /Bucket screenshots extension "PNG" will normalize to "\.png"\./);
  assert.match(result.warnings.join('\n'), /Bucket screenshots basename pattern " Screenshot \* " will normalize to "screenshot \*"\./);
  assert.match(result.warnings.join('\n'), /Bucket screenshots repeats basename pattern "screenshot \*"/);
  assert.deepEqual(result.normalizedConfig.buckets.screenshots, {
    extensions: ['.png'],
    basenamePatterns: ['screenshot *'],
  });
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

test('organize prefers basename pattern matches over extension buckets during real moves', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-'));
  const bucketConfig = buildBucketConfig({
    buckets: {
      screenshots: {
        basenamePatterns: ['Screenshot *'],
      },
      quizzes: {
        basenamePatterns: ['quiz-2026-04-1?'],
        extensions: ['.txt'],
      },
    },
  });
  await fs.writeFile(path.join(tmp, 'Screenshot 2026-04-18.png'), 'capture');
  await fs.writeFile(path.join(tmp, 'quiz-2026-04-18.md'), 'quiz');
  await fs.writeFile(path.join(tmp, 'notes.txt'), 'notes');

  const result = await organize(tmp, { bucketConfig });

  assert.equal(result.summary.total, 3);
  assert.equal(await fs.readFile(path.join(tmp, 'screenshots', 'Screenshot 2026-04-18.png'), 'utf8'), 'capture');
  assert.equal(await fs.readFile(path.join(tmp, 'quizzes', 'quiz-2026-04-18.md'), 'utf8'), 'quiz');
  assert.equal(await fs.readFile(path.join(tmp, 'quizzes', 'notes.txt'), 'utf8'), 'notes');
});



test('organize records MIME-aware matches for misleading extensions during real moves', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-'));
  const bucketConfig = buildBucketConfig({
    buckets: {
      datasets: {
        mimeTypes: ['application/json'],
      },
      visuals: {
        mimePrefixes: ['image/'],
      },
    },
  });
  const jsonNotesPath = path.join(tmp, 'report.txt');
  const svgNotesPath = path.join(tmp, 'diagram.txt');
  const plainNotesPath = path.join(tmp, 'notes.txt');
  await fs.writeFile(jsonNotesPath, '{"records": 2}\n');
  await fs.writeFile(svgNotesPath, '<svg viewBox="0 0 10 10"></svg>\n');
  await fs.writeFile(plainNotesPath, 'plain note\n');

  const result = await organize(tmp, { bucketConfig });

  assert.equal(result.summary.byBucket.datasets, 1);
  assert.equal(result.summary.byBucket.visuals, 1);
  assert.equal(result.summary.byBucket.documents, 1);
  assert.deepEqual(result.moves.map(move => ({ bucket: move.bucket, matchedBy: move.matchedBy, detectedMimeType: move.detectedMimeType })).sort((left, right) => left.bucket.localeCompare(right.bucket)), [
    { bucket: 'datasets', matchedBy: 'mimeType', detectedMimeType: 'application/json' },
    { bucket: 'documents', matchedBy: 'extension', detectedMimeType: 'text/plain' },
    { bucket: 'visuals', matchedBy: 'mimePrefix', detectedMimeType: 'image/svg+xml' },
  ]);
  assert.equal(await fs.readFile(path.join(tmp, 'datasets', 'report.txt'), 'utf8'), '{"records": 2}\n');
  assert.equal(await fs.readFile(path.join(tmp, 'visuals', 'diagram.txt'), 'utf8'), '<svg viewBox="0 0 10 10"></svg>\n');
  assert.equal(await fs.readFile(path.join(tmp, 'documents', 'notes.txt'), 'utf8'), 'plain note\n');
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

  assert.deepEqual(verifyManifestIntegrity(manifest), {
    present: false,
    valid: true,
    algorithm: null,
    checksum: null,
    expectedChecksum: null,
    reason: null,
  });
  assert.equal(manifest.manifestPath, path.resolve(manifestPath));
  const restored = await fs.readFile(path.join(tmp, 'notes.txt'), 'utf8');
  assert.equal(restored, 'draft');
  assert.equal(await fs.readFile(path.join(manifestPath), 'utf8').then(Boolean), true);
  await assert.rejects(fs.access(path.join(tmp, 'documents')));
  assert.equal(undoResult.summary.restored, 1);
  assert.equal(undoResult.summary.removedDirectories, 1);
});

test('writeManifest can embed checksum metadata and undo verifies it before restoring files', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-'));
  const manifestPath = path.join(tmp, 'artifacts', 'organize-manifest.json');
  await fs.writeFile(path.join(tmp, 'notes.txt'), 'draft');

  const organizeResult = await organize(tmp);
  const manifest = await writeManifest(organizeResult, manifestPath, { includeChecksum: true });
  const verification = verifyManifestIntegrity(manifest);
  const undoResult = await undoFromManifest(manifestPath);

  assert.equal(typeof manifest.integrity.checksum, 'string');
  assert.equal(manifest.integrity.algorithm, 'sha256');
  assert.equal(manifest.integrity.checksum, manifestChecksumFor(manifest));
  assert.deepEqual(verification, {
    present: true,
    valid: true,
    algorithm: 'sha256',
    checksum: manifest.integrity.checksum,
    expectedChecksum: manifest.integrity.checksum,
    reason: null,
  });
  assert.equal(undoResult.integrity.present, true);
  assert.equal(undoResult.integrity.valid, true);
  assert.equal(await fs.readFile(path.join(tmp, 'notes.txt'), 'utf8'), 'draft');
});

test('writeDetachedManifestSignature requires checksum-backed manifest metadata', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-signature-precondition-'));
  const manifestPath = path.join(tmp, 'artifacts', 'organize-manifest.json');
  const { privateKeyPath } = await writeEd25519KeyPair(tmp);
  await fs.writeFile(path.join(tmp, 'notes.txt'), 'draft');

  const organizeResult = await organize(tmp);
  await writeManifest(organizeResult, manifestPath);

  await assert.rejects(
    writeDetachedManifestSignature(manifestPath, privateKeyPath),
    /checksum-backed integrity metadata/,
  );
});

test('writeDetachedManifestSignature signs checksum-backed manifests with a detached sidecar', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-signature-'));
  const manifestPath = path.join(tmp, 'artifacts', 'organize-manifest.json');
  const signaturePath = path.join(tmp, 'artifacts', 'organize-manifest.sig.json');
  const { privateKeyPath, publicKeyPath } = await writeEd25519KeyPair(tmp);
  await fs.writeFile(path.join(tmp, 'notes.txt'), 'draft');

  const organizeResult = await organize(tmp);
  const manifest = await writeManifest(organizeResult, manifestPath, { includeChecksum: true });
  const signatureRecord = await writeDetachedManifestSignature(manifestPath, privateKeyPath, { signaturePath });
  const verification = await verifyDetachedManifestSignature(manifestPath, publicKeyPath, { signaturePath });

  assert.equal(signatureRecord.manifestPath, path.resolve(manifestPath));
  assert.equal(signatureRecord.signaturePath, path.resolve(signaturePath));
  assert.equal(signatureRecord.signer.keyType, 'ed25519');
  assert.equal(signatureRecord.signedPayload.checksum, manifestSignatureChecksumFor(manifest));
  assert.equal(Array.isArray(signatureRecord.approvals), true);
  assert.equal(signatureRecord.approvals.length, 1);
  assert.match(signatureRecord.approvals[0].signer.publicKeyPem, /BEGIN PUBLIC KEY/);
  assert.equal(verification.valid, true);
  assert.equal(verification.signaturePath, path.resolve(signaturePath));
  assert.equal(verification.signedPayload.checksum, manifestSignatureChecksumFor(manifest));
  assert.equal(verification.approvalCount, 1);
});

test('loadSignerPolicy normalizes trusted signer fingerprints, metadata, and quorum rules', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-signer-policy-'));
  const { publicKeyPath } = await writeEd25519KeyPair(tmp);
  const { fingerprint } = await writeSignerPolicy(tmp, publicKeyPath);

  const bareFingerprint = fingerprint.slice('sha256:'.length);
  const policyPath = path.join(tmp, 'bare-trusted-signers.json');
  await fs.writeFile(policyPath, `${JSON.stringify({
    name: 'Bare fingerprint policy',
    trustedSigners: [{
      fingerprint: bareFingerprint.toUpperCase(),
      label: ' Review laptop ',
      roles: ['organize-approver', 'organize-approver', ' undo-approver '],
    }],
    approvalQuorum: {
      minimumSigners: 1,
      requiredRoles: [' undo-approver ', 'undo-approver'],
    },
  }, null, 2)}
`);

  const signerPolicy = await loadSignerPolicy(policyPath);
  assert.equal(signerPolicy.name, 'Bare fingerprint policy');
  assert.deepEqual(signerPolicy.trustedSigners, [{
    fingerprint,
    label: 'Review laptop',
    roles: ['organize-approver', 'undo-approver'],
    notes: null,
  }]);
  assert.deepEqual(signerPolicy.approvalQuorum, {
    minimumSigners: 1,
    requiredRoles: ['undo-approver'],
  });
  assert.equal(normalizeSignerFingerprint(bareFingerprint), fingerprint);
});

test('verifyDetachedManifestSignature can enforce multi-signer quorum rules with signer-policy-only undo', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-signature-quorum-'));
  const manifestPath = path.join(tmp, 'artifacts', 'organize-manifest.json');
  const signaturePath = path.join(tmp, 'artifacts', 'organize-manifest.sig.json');
  const organizerKeyPair = await writeEd25519KeyPair(tmp, 'organize-approver');
  const undoKeyPair = await writeEd25519KeyPair(tmp, 'undo-approver');

  const organizerFingerprint = publicKeyFingerprint(crypto.createPublicKey(await fs.readFile(organizerKeyPair.publicKeyPath, 'utf8')));
  const undoFingerprint = publicKeyFingerprint(crypto.createPublicKey(await fs.readFile(undoKeyPair.publicKeyPath, 'utf8')));
  const { policyPath } = await writeSignerPolicy(tmp, organizerKeyPair.publicKeyPath, {
    trustedSigners: [
      {
        fingerprint: organizerFingerprint,
        label: 'Organizer reviewer',
        roles: ['organize-approver'],
        notes: 'Approves organize passes.',
      },
      {
        fingerprint: undoFingerprint,
        label: 'Undo reviewer',
        roles: ['undo-approver'],
        notes: 'Approves restore operations.',
      },
    ],
    approvalQuorum: {
      minimumSigners: 2,
      requiredRoles: ['organize-approver', 'undo-approver'],
    },
  });
  await fs.writeFile(path.join(tmp, 'notes.txt'), 'draft');

  const protectedPaths = [
    manifestPath,
    signaturePath,
    policyPath,
    organizerKeyPair.privateKeyPath,
    organizerKeyPair.publicKeyPath,
    undoKeyPair.privateKeyPath,
    undoKeyPair.publicKeyPath,
  ];
  const organizeResult = await organize(tmp, { skipPaths: protectedPaths });
  await writeManifest(organizeResult, manifestPath, { includeChecksum: true });

  const firstSignature = await writeDetachedManifestSignature(manifestPath, organizerKeyPair.privateKeyPath, {
    signaturePath,
    signerPolicyPath: policyPath,
  });
  assert.equal(firstSignature.approvals.length, 1);
  assert.equal(firstSignature.signerPolicy.approvalQuorum.satisfied, false);
  assert.deepEqual(firstSignature.signerPolicy.approvalQuorum.missingRoles, ['undo-approver']);

  const quorumFailure = await verifyDetachedManifestSignature(manifestPath, null, {
    signaturePath,
    signerPolicyPath: policyPath,
  });
  assert.equal(quorumFailure.valid, false);
  assert.match(quorumFailure.reason, /Signer policy quorum not met/);
  assert.equal(quorumFailure.approvalCount, 1);
  assert.equal(quorumFailure.verifiedApprovalCount, 1);
  assert.equal(quorumFailure.approvalQuorum.satisfied, false);
  assert.equal(quorumFailure.approvalQuorum.missingSigners, 1);
  assert.deepEqual(quorumFailure.approvalQuorum.missingRoles, ['undo-approver']);

  const secondSignature = await writeDetachedManifestSignature(manifestPath, undoKeyPair.privateKeyPath, {
    signaturePath,
    signerPolicyPath: policyPath,
  });
  assert.equal(secondSignature.approvals.length, 2);
  assert.equal(secondSignature.signerPolicy.approvalQuorum.satisfied, true);
  assert.equal(secondSignature.signerPolicy.approvalQuorum.approvalsPresent, 2);
  assert.deepEqual(secondSignature.signerPolicy.approvalQuorum.missingRoles, []);

  const quorumSuccess = await verifyDetachedManifestSignature(manifestPath, null, {
    signaturePath,
    signerPolicyPath: policyPath,
  });
  assert.equal(quorumSuccess.valid, true);
  assert.equal(quorumSuccess.approvalCount, 2);
  assert.equal(quorumSuccess.verifiedApprovalCount, 2);
  assert.equal(quorumSuccess.approvalQuorum.satisfied, true);
  assert.equal(quorumSuccess.approvalQuorum.minimumSigners, 2);
  assert.deepEqual(quorumSuccess.approvalQuorum.requiredRoles, ['organize-approver', 'undo-approver']);
  assert.deepEqual(quorumSuccess.approvalQuorum.missingRoles, []);
  assert.equal(quorumSuccess.publicKeyFingerprint, null);

  const keyedVerification = await verifyDetachedManifestSignature(manifestPath, undoKeyPair.publicKeyPath, {
    signaturePath,
    signerPolicyPath: policyPath,
  });
  assert.equal(keyedVerification.valid, true);
  assert.equal(keyedVerification.publicKeyFingerprint, undoFingerprint);
  assert.equal(keyedVerification.signerLabel, 'Undo reviewer');
  assert.deepEqual(keyedVerification.signerRoles, ['undo-approver']);

  const undoResult = await undoFromManifest(manifestPath, {
    signaturePath,
    signerPolicyPath: policyPath,
  });
  assert.equal(undoResult.signatureVerification.valid, true);
  assert.equal(undoResult.signatureVerification.approvalQuorum.satisfied, true);
  assert.equal(await fs.readFile(path.join(tmp, 'notes.txt'), 'utf8'), 'draft');
});

test('CLI can append approvals to an existing manifest with --sign-manifest manifest.json', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-cli-sign-manifest-'));
  const manifestPath = path.join(tmp, 'artifacts', 'organize-manifest.json');
  const signaturePath = path.join(tmp, 'artifacts', 'organize-manifest.sig.json');
  const organizerKeyPair = await writeEd25519KeyPair(tmp, 'cli-organize-approver');
  const undoKeyPair = await writeEd25519KeyPair(tmp, 'cli-undo-approver');

  const organizerFingerprint = publicKeyFingerprint(crypto.createPublicKey(await fs.readFile(organizerKeyPair.publicKeyPath, 'utf8')));
  const undoFingerprint = publicKeyFingerprint(crypto.createPublicKey(await fs.readFile(undoKeyPair.publicKeyPath, 'utf8')));
  const { policyPath } = await writeSignerPolicy(tmp, organizerKeyPair.publicKeyPath, {
    trustedSigners: [
      {
        fingerprint: organizerFingerprint,
        label: 'Organizer reviewer',
        roles: ['organize-approver'],
        notes: 'Approves organize passes.',
      },
      {
        fingerprint: undoFingerprint,
        label: 'Undo reviewer',
        roles: ['undo-approver'],
        notes: 'Approves restore operations.',
      },
    ],
    approvalQuorum: {
      minimumSigners: 2,
      requiredRoles: ['organize-approver', 'undo-approver'],
    },
  });
  await fs.writeFile(path.join(tmp, 'notes.txt'), 'draft');

  const protectedPaths = [
    manifestPath,
    signaturePath,
    policyPath,
    organizerKeyPair.privateKeyPath,
    organizerKeyPair.publicKeyPath,
    undoKeyPair.privateKeyPath,
    undoKeyPair.publicKeyPath,
  ];
  const organizeResult = await organize(tmp, { skipPaths: protectedPaths });
  await writeManifest(organizeResult, manifestPath, { includeChecksum: true });

  const organizerCli = path.join(__dirname, 'organizer.js');
  const firstRun = JSON.parse((await execFile(process.execPath, [
    organizerCli,
    manifestPath,
    '--sign-manifest',
    organizerKeyPair.privateKeyPath,
    '--signature-path',
    signaturePath,
    '--signer-policy',
    policyPath,
    '--json',
  ])).stdout);
  assert.equal(firstRun.action, 'manifest-signature');
  assert.equal(firstRun.approvals.length, 1);
  assert.equal(firstRun.signerPolicy.approvalQuorum.satisfied, false);

  const secondRun = JSON.parse((await execFile(process.execPath, [
    organizerCli,
    manifestPath,
    '--sign-manifest',
    undoKeyPair.privateKeyPath,
    '--signature-path',
    signaturePath,
    '--signer-policy',
    policyPath,
    '--json',
  ])).stdout);
  assert.equal(secondRun.action, 'manifest-signature');
  assert.equal(secondRun.approvals.length, 2);
  assert.equal(secondRun.signerPolicy.approvalQuorum.satisfied, true);

  const verification = await verifyDetachedManifestSignature(manifestPath, null, {
    signaturePath,
    signerPolicyPath: policyPath,
  });
  assert.equal(verification.valid, true);
  assert.equal(verification.approvalCount, 2);
  assert.equal(verification.approvalQuorum.satisfied, true);
});

test('writeDetachedManifestSignature can enforce a trusted signer policy and store signer metadata', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-signature-policy-'));
  const manifestPath = path.join(tmp, 'artifacts', 'organize-manifest.json');
  const signaturePath = path.join(tmp, 'artifacts', 'organize-manifest.sig.json');
  const { privateKeyPath, publicKeyPath } = await writeEd25519KeyPair(tmp);
  const { policyPath, fingerprint } = await writeSignerPolicy(tmp, publicKeyPath);
  await fs.writeFile(path.join(tmp, 'notes.txt'), 'draft');

  const protectedPaths = [
    ...collectProtectedPathsForOrganize({
      manifestOut: manifestPath,
      signaturePath,
      signManifestKeyPath: privateKeyPath,
      signerPolicyPath: policyPath,
    }),
    publicKeyPath,
  ];
  const organizeResult = await organize(tmp, { skipPaths: protectedPaths });
  await writeManifest(organizeResult, manifestPath, { includeChecksum: true });
  const signatureRecord = await writeDetachedManifestSignature(manifestPath, privateKeyPath, {
    signaturePath,
    signerPolicyPath: policyPath,
  });
  const verification = await verifyDetachedManifestSignature(manifestPath, publicKeyPath, {
    signaturePath,
    signerPolicyPath: policyPath,
  });

  assert.equal(signatureRecord.signer.publicKeyFingerprint, fingerprint);
  assert.equal(signatureRecord.signer.label, 'TA laptop key');
  assert.deepEqual(signatureRecord.signer.roles, ['organize-approver', 'undo-approver']);
  assert.equal(signatureRecord.signerPolicy.name, 'Course staff signing policy');
  assert.equal(verification.valid, true);
  assert.equal(verification.signerLabel, 'TA laptop key');
  assert.deepEqual(verification.signerRoles, ['organize-approver', 'undo-approver']);
  assert.equal(verification.signerPolicy.name, 'Course staff signing policy');
  assert.equal(await fs.readFile(policyPath, 'utf8') !== '', true);
  assert.equal(await fs.readFile(privateKeyPath, 'utf8') !== '', true);
});

test('writeDetachedManifestSignature rejects signer policies that do not trust the signing key', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-signature-untrusted-policy-'));
  const manifestPath = path.join(tmp, 'artifacts', 'organize-manifest.json');
  const { privateKeyPath, publicKeyPath } = await writeEd25519KeyPair(tmp, 'primary');
  const { publicKeyPath: otherPublicKeyPath } = await writeEd25519KeyPair(tmp, 'secondary');
  const { policyPath } = await writeSignerPolicy(tmp, otherPublicKeyPath);
  await fs.writeFile(path.join(tmp, 'notes.txt'), 'draft');

  const protectedPaths = [
    ...collectProtectedPathsForOrganize({
      manifestOut: manifestPath,
      signManifestKeyPath: privateKeyPath,
      signerPolicyPath: policyPath,
    }),
    publicKeyPath,
    otherPublicKeyPath,
  ];
  const organizeResult = await organize(tmp, { skipPaths: protectedPaths });
  await writeManifest(organizeResult, manifestPath, { includeChecksum: true });

  await assert.rejects(
    writeDetachedManifestSignature(manifestPath, privateKeyPath, { signerPolicyPath: policyPath }),
    /is not trusted by signer policy/,
  );

  await writeDetachedManifestSignature(manifestPath, privateKeyPath);
  await assert.rejects(
    undoFromManifest(manifestPath, {
      verifySignatureKeyPath: publicKeyPath,
      signerPolicyPath: policyPath,
    }),
    /is not trusted by signer policy/,
  );
});

test('verifyDetachedManifestSignature fails for tampered manifests or mismatched public keys', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-signature-invalid-'));
  const manifestPath = path.join(tmp, 'artifacts', 'organize-manifest.json');
  const { privateKeyPath, publicKeyPath } = await writeEd25519KeyPair(tmp, 'primary');
  const { publicKeyPath: wrongPublicKeyPath } = await writeEd25519KeyPair(tmp, 'secondary');
  await fs.writeFile(path.join(tmp, 'notes.txt'), 'draft');

  const organizeResult = await organize(tmp);
  await writeManifest(organizeResult, manifestPath, { includeChecksum: true });
  await writeDetachedManifestSignature(manifestPath, privateKeyPath);

  const wrongKeyResult = await verifyDetachedManifestSignature(manifestPath, wrongPublicKeyPath);
  assert.equal(wrongKeyResult.valid, false);
  assert.match(wrongKeyResult.reason, /Public key fingerprint mismatch/);

  const tamperedManifest = JSON.parse(await fs.readFile(manifestPath, 'utf8'));
  tamperedManifest.summary.total = 999;
  await fs.writeFile(manifestPath, `${JSON.stringify(tamperedManifest, null, 2)}\n`);

  const tamperedResult = await verifyDetachedManifestSignature(manifestPath, publicKeyPath);
  assert.equal(tamperedResult.valid, false);
  assert.match(tamperedResult.reason, /Manifest payload checksum mismatch/);
});

test('undo can require detached signature verification before restoring files', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-signature-undo-'));
  const manifestPath = path.join(tmp, 'artifacts', 'organize-manifest.json');
  const { privateKeyPath, publicKeyPath } = await writeEd25519KeyPair(tmp);
  await fs.writeFile(path.join(tmp, 'notes.txt'), 'draft');

  const organizeResult = await organize(tmp);
  await writeManifest(organizeResult, manifestPath, { includeChecksum: true });
  await writeDetachedManifestSignature(manifestPath, privateKeyPath);

  const undoResult = await undoFromManifest(manifestPath, {
    verifySignatureKeyPath: publicKeyPath,
  });
  assert.equal(undoResult.signatureVerification.valid, true);
  assert.equal(await fs.readFile(path.join(tmp, 'notes.txt'), 'utf8'), 'draft');

  await fs.writeFile(path.join(tmp, 'notes.txt'), 'draft');
  const reorganizeResult = await organize(tmp);
  await writeManifest(reorganizeResult, manifestPath, { includeChecksum: true });
  await writeDetachedManifestSignature(manifestPath, privateKeyPath);
  const { publicKeyPath: wrongPublicKeyPath } = await writeEd25519KeyPair(tmp, 'wrong-team');
  await assert.rejects(
    undoFromManifest(manifestPath, { verifySignatureKeyPath: wrongPublicKeyPath }),
    /failed signature verification: Public key fingerprint mismatch/,
  );
});

test('writeDetachedManifestSignature resets stale approval bundles when the manifest payload changes', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-signature-refresh-'));
  const manifestPath = path.join(tmp, 'artifacts', 'organize-manifest.json');
  const signaturePath = path.join(tmp, 'artifacts', 'organize-manifest.sig.json');
  const { privateKeyPath, publicKeyPath } = await writeEd25519KeyPair(tmp);
  await fs.writeFile(path.join(tmp, 'notes.txt'), 'draft');

  const initialOrganizeResult = await organize(tmp);
  const initialManifest = await writeManifest(initialOrganizeResult, manifestPath, { includeChecksum: true });
  const initialSignature = await writeDetachedManifestSignature(manifestPath, privateKeyPath, { signaturePath });
  assert.equal(initialSignature.approvals.length, 1);

  await fs.writeFile(path.join(tmp, 'notes.txt'), 'draft');
  const refreshedOrganizeResult = await organize(tmp);
  const refreshedManifest = await writeManifest(refreshedOrganizeResult, manifestPath, { includeChecksum: true });
  const refreshedSignature = await writeDetachedManifestSignature(manifestPath, privateKeyPath, { signaturePath });
  const refreshedVerification = await verifyDetachedManifestSignature(manifestPath, publicKeyPath, { signaturePath });

  assert.notEqual(manifestSignatureChecksumFor(initialManifest), manifestSignatureChecksumFor(refreshedManifest));
  assert.equal(refreshedSignature.approvals.length, 1);
  assert.equal(refreshedSignature.approvals[0].signedPayload.checksum, manifestSignatureChecksumFor(refreshedManifest));
  assert.equal(refreshedVerification.valid, true);
  assert.equal(refreshedVerification.approvalCount, 1);
  assert.equal(refreshedVerification.signedPayload.checksum, manifestSignatureChecksumFor(refreshedManifest));
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

test('undo rejects tampered checksum manifests unless verification is skipped', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-'));
  const manifestPath = path.join(tmp, 'undo-manifest.json');
  await fs.writeFile(path.join(tmp, 'notes.txt'), 'draft');

  const organizeResult = await organize(tmp);
  const manifest = await writeManifest(organizeResult, manifestPath, { includeChecksum: true });
  const tampered = JSON.parse(await fs.readFile(manifestPath, 'utf8'));
  tampered.summary.total = 999;
  await fs.writeFile(manifestPath, `${JSON.stringify(tampered, null, 2)}\n`);

  await assert.rejects(
    undoFromManifest(manifestPath),
    /failed integrity verification: Manifest checksum mismatch/,
  );

  const undoResult = await undoFromManifest(manifestPath, { verifyIntegrity: false });
  assert.equal(undoResult.integrity.present, true);
  assert.equal(undoResult.integrity.valid, false);
  assert.equal(undoResult.integrity.checksum, manifest.integrity.checksum);
  assert.equal(await fs.readFile(path.join(tmp, 'notes.txt'), 'utf8'), 'draft');
});

test('parseArgs supports config, preset, lint, normalized-config, preset-export, and undo flags', () => {
  const organizeArgs = parseArgs(['~/Downloads', '--dry-run', '--recursive', '--json', '--config', 'buckets.json', '--manifest-out', 'runs/latest.json', '--manifest-checksum']);
  assert.equal(organizeArgs.targetDir, '~/Downloads');
  assert.deepEqual(organizeArgs.options, {
    dryRun: true,
    recursive: true,
    json: true,
    manifestOut: 'runs/latest.json',
    manifestChecksum: true,
    signManifestKeyPath: null,
    signExistingManifestPath: null,
    verifyManifestSignatureKeyPath: null,
    signaturePath: null,
    signerPolicyPath: null,
    undoManifest: null,
    skipManifestVerification: false,
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
    manifestChecksum: false,
    signManifestKeyPath: null,
    signExistingManifestPath: null,
    verifyManifestSignatureKeyPath: null,
    signaturePath: null,
    signerPolicyPath: null,
    undoManifest: null,
    skipManifestVerification: false,
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

  const undoArgs = parseArgs(['--undo', 'runs/latest.json', '--dry-run', '--json', '--skip-manifest-verification']);
  assert.equal(undoArgs.targetDir, '.');
  assert.deepEqual(undoArgs.options, {
    dryRun: true,
    recursive: false,
    json: true,
    manifestOut: null,
    manifestChecksum: false,
    signManifestKeyPath: null,
    signExistingManifestPath: null,
    verifyManifestSignatureKeyPath: null,
    signaturePath: null,
    signerPolicyPath: null,
    undoManifest: 'runs/latest.json',
    skipManifestVerification: true,
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

  const signedOrganizeArgs = parseArgs(['~/Downloads', '--manifest-out', 'runs/latest.json', '--manifest-checksum', '--sign-manifest', 'keys/team.pem', '--signature-path', 'runs/latest.sig.json', '--signer-policy', 'keys/trusted-signers.json']);
  assert.deepEqual(signedOrganizeArgs.options, {
    dryRun: false,
    recursive: false,
    json: false,
    manifestOut: 'runs/latest.json',
    manifestChecksum: true,
    signManifestKeyPath: 'keys/team.pem',
    signExistingManifestPath: null,
    verifyManifestSignatureKeyPath: null,
    signaturePath: 'runs/latest.sig.json',
    signerPolicyPath: 'keys/trusted-signers.json',
    undoManifest: null,
    skipManifestVerification: false,
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

  const signExistingManifestArgs = parseArgs(['runs/latest.json', '--sign-manifest', 'keys/reviewer.pem', '--signature-path', 'runs/latest.sig.json', '--signer-policy', 'keys/trusted-signers.json']);
  assert.equal(signExistingManifestArgs.targetDir, '.');
  assert.deepEqual(signExistingManifestArgs.options, {
    dryRun: false,
    recursive: false,
    json: false,
    manifestOut: null,
    manifestChecksum: false,
    signManifestKeyPath: 'keys/reviewer.pem',
    signExistingManifestPath: 'runs/latest.json',
    verifyManifestSignatureKeyPath: null,
    signaturePath: 'runs/latest.sig.json',
    signerPolicyPath: 'keys/trusted-signers.json',
    undoManifest: null,
    skipManifestVerification: false,
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

  const signedUndoArgs = parseArgs(['--undo', 'runs/latest.json', '--verify-manifest-signature', 'keys/team.pub.pem', '--signature-path', 'runs/latest.sig.json', '--signer-policy', 'keys/trusted-signers.json']);
  assert.deepEqual(signedUndoArgs.options, {
    dryRun: false,
    recursive: false,
    json: false,
    manifestOut: null,
    manifestChecksum: false,
    signManifestKeyPath: null,
    signExistingManifestPath: null,
    verifyManifestSignatureKeyPath: 'keys/team.pub.pem',
    signaturePath: 'runs/latest.sig.json',
    signerPolicyPath: 'keys/trusted-signers.json',
    undoManifest: 'runs/latest.json',
    skipManifestVerification: false,
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

  const policyOnlyUndoArgs = parseArgs(['--undo', 'runs/latest.json', '--signer-policy', 'keys/trusted-signers.json']);
  assert.deepEqual(policyOnlyUndoArgs.options, {
    dryRun: false,
    recursive: false,
    json: false,
    manifestOut: null,
    manifestChecksum: false,
    signManifestKeyPath: null,
    signExistingManifestPath: null,
    verifyManifestSignatureKeyPath: null,
    signaturePath: null,
    signerPolicyPath: 'keys/trusted-signers.json',
    undoManifest: 'runs/latest.json',
    skipManifestVerification: false,
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
    manifestChecksum: false,
    signManifestKeyPath: null,
    signExistingManifestPath: null,
    verifyManifestSignatureKeyPath: null,
    signaturePath: null,
    signerPolicyPath: null,
    undoManifest: null,
    skipManifestVerification: false,
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
    manifestChecksum: false,
    signManifestKeyPath: null,
    signExistingManifestPath: null,
    verifyManifestSignatureKeyPath: null,
    signaturePath: null,
    signerPolicyPath: null,
    undoManifest: null,
    skipManifestVerification: false,
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
    manifestChecksum: false,
    signManifestKeyPath: null,
    signExistingManifestPath: null,
    verifyManifestSignatureKeyPath: null,
    signaturePath: null,
    signerPolicyPath: null,
    undoManifest: null,
    skipManifestVerification: false,
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
    manifestChecksum: false,
    signManifestKeyPath: null,
    signExistingManifestPath: null,
    verifyManifestSignatureKeyPath: null,
    signaturePath: null,
    signerPolicyPath: null,
    undoManifest: null,
    skipManifestVerification: false,
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
    manifestChecksum: false,
    signManifestKeyPath: null,
    signExistingManifestPath: null,
    verifyManifestSignatureKeyPath: null,
    signaturePath: null,
    signerPolicyPath: null,
    undoManifest: null,
    skipManifestVerification: false,
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
    () => parseArgs(['--undo', 'runs/latest.json', '--manifest-checksum']),
    /--manifest-checksum cannot be used with --undo/,
  );

  assert.throws(
    () => parseArgs(['~/Downloads', '--config', 'buckets.json', '--preset', 'coursework']),
    /--config cannot be combined with --preset/,
  );

  assert.throws(
    () => parseArgs(['~/Downloads', '--manifest-checksum']),
    /--manifest-checksum requires --manifest-out/,
  );

  assert.throws(
    () => parseArgs(['~/Downloads', '--manifest-out', 'runs/latest.json', '--sign-manifest', 'keys/team.pem']),
    /--sign-manifest requires --manifest-checksum/,
  );

  assert.throws(
    () => parseArgs(['--sign-manifest', 'keys/team.pem']),
    /--sign-manifest requires --manifest-out or a manifest path argument/,
  );

  assert.throws(
    () => parseArgs(['--verify-manifest-signature', 'keys/team.pub.pem']),
    /--verify-manifest-signature can only be used with --undo/,
  );

  assert.throws(
    () => parseArgs(['--signature-path', 'runs/latest.sig.json']),
    /--signature-path requires --sign-manifest or --undo/,
  );

  assert.throws(
    () => parseArgs(['--signer-policy', 'keys/trusted-signers.json']),
    /--signer-policy requires --sign-manifest or --undo/,
  );

  assert.throws(
    () => parseArgs(['--skip-manifest-verification']),
    /--skip-manifest-verification can only be used with --undo/,
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

test('formatTextReport includes config, preset, manifest, signature, lint, and normalized-config details for supported actions', () => {
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
    integrity: { algorithm: 'sha256', checksum: 'abc123' },
    detachedSignature: {
      signaturePath: '/tmp/demo/manifests/latest.sig.json',
      signer: {
        publicKeyFingerprint: 'sha256:def456',
        label: 'TA laptop key',
        roles: ['organize-approver', 'undo-approver'],
      },
      signerPolicy: {
        name: 'Course staff signing policy',
        policyPath: '/tmp/demo/trusted-signers.json',
      },
    },
    summary: { total: 1, renamed: 1, byBucket: { datasets: 1 } },
    moves: [{
      from: '/tmp/demo/a.csv',
      to: '/tmp/demo/datasets/a (1).csv',
      renamed: true,
      matchedBy: 'mimeType',
      matchedValue: 'application/json',
      detectedMimeType: 'application/json',
    }],
  });

  const signatureReport = formatTextReport({
    action: 'manifest-signature',
    manifestPath: '/tmp/demo/manifests/latest.json',
    signaturePath: '/tmp/demo/manifests/latest.sig.json',
    signer: {
      publicKeyFingerprint: 'sha256:def456',
      label: 'Undo reviewer',
      roles: ['undo-approver'],
    },
    approvals: [{}, {}],
    signerPolicy: {
      name: 'Course staff signing policy',
      policyPath: '/tmp/demo/trusted-signers.json',
      approvalQuorum: {
        minimumSigners: 2,
        approvalsPresent: 2,
        missingSigners: 0,
        missingRoles: [],
        satisfied: true,
      },
    },
  });

  const undoReport = formatTextReport({
    action: 'undo',
    rootDir: '/tmp/demo',
    dryRun: false,
    manifestPath: '/tmp/demo/manifests/latest.json',
    integrity: { present: true, valid: true, algorithm: 'sha256', checksum: 'abc123' },
    signatureVerification: {
      valid: true,
      signaturePath: '/tmp/demo/manifests/latest.sig.json',
      publicKeyFingerprint: 'sha256:def456',
      signerLabel: 'TA laptop key',
      signerRoles: ['organize-approver', 'undo-approver'],
      signerPolicy: {
        name: 'Course staff signing policy',
        policyPath: '/tmp/demo/trusted-signers.json',
      },
    },
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
  assert.match(organizeReport, /manifest checksum: sha256:abc123/);
  assert.match(organizeReport, /manifest: \/tmp\/demo\/manifests\/latest\.json/);
  assert.match(organizeReport, /manifest signature: \/tmp\/demo\/manifests\/latest\.sig\.json/);
  assert.match(organizeReport, /manifest signer fingerprint: sha256:def456/);
  assert.match(organizeReport, /manifest signer label: TA laptop key/);
  assert.match(organizeReport, /manifest signer roles: organize-approver, undo-approver/);
  assert.match(organizeReport, /signer policy: Course staff signing policy/);
  assert.match(organizeReport, /renamed to avoid collisions: 1/);
  assert.match(signatureReport, /action: manifest-signature/);
  assert.match(signatureReport, /manifest: \/tmp\/demo\/manifests\/latest\.json/);
  assert.match(signatureReport, /signature path: \/tmp\/demo\/manifests\/latest\.sig\.json/);
  assert.match(signatureReport, /manifest signer label: Undo reviewer/);
  assert.match(signatureReport, /manifest approvals: 2/);
  assert.match(signatureReport, /signer quorum: 2\/2 trusted approval\(s\); satisfied/);
  assert.match(organizeReport, /\[renamed; MIME type application\/json; detected application\/json\]/);
  assert.match(undoReport, /action: undo/);
  assert.match(undoReport, /manifest checksum verified: yes/);
  assert.match(undoReport, /manifest checksum: sha256:abc123/);
  assert.match(undoReport, /manifest signature verified: yes/);
  assert.match(undoReport, /manifest signature file: \/tmp\/demo\/manifests\/latest\.sig\.json/);
  assert.match(undoReport, /manifest signer fingerprint: sha256:def456/);
  assert.match(undoReport, /manifest signer label: TA laptop key/);
  assert.match(undoReport, /manifest signer roles: organize-approver, undo-approver/);
  assert.match(undoReport, /signer policy: Course staff signing policy/);
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
