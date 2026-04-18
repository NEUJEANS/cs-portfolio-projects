const crypto = require('crypto');
const fs = require('fs/promises');
const os = require('os');
const path = require('path');
const {
  formatTextReport,
  organize,
  previewNormalizedBucketConfig,
  writeManifest,
  writeDetachedManifestSignature,
  verifyDetachedManifestSignature,
  writeNormalizedBucketConfig,
  undoFromManifest,
  loadBucketConfig,
} = require('./organizer');

const REPO_ROOT = path.resolve(__dirname, '../..');
const ARTIFACT_DIR = path.join(REPO_ROOT, 'docs', 'artifacts', 'file-organizer-cli');
const DEMO_PLACEHOLDER_ROOT = '/demo/file-organizer-cli';

function replaceAll(text, searchValue, replaceValue) {
  return text.split(searchValue).join(replaceValue);
}

function sanitizeString(value, tempRoot) {
  if (typeof value !== 'string') {
    return value;
  }

  const normalizedTempRoot = tempRoot.split(path.sep).join('/');
  const normalizedValue = value.split(path.sep).join('/');
  const sanitized = replaceAll(normalizedValue, normalizedTempRoot, DEMO_PLACEHOLDER_ROOT);
  return sanitized;
}

function sanitizeForArtifact(value, tempRoot) {
  if (Array.isArray(value)) {
    return value.map(item => sanitizeForArtifact(item, tempRoot));
  }

  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value).map(([key, nestedValue]) => [key, sanitizeForArtifact(nestedValue, tempRoot)]),
    );
  }

  return sanitizeString(value, tempRoot);
}

async function buildTreeLines(rootDir, currentDir = rootDir, prefix = '') {
  const entries = await fs.readdir(currentDir, { withFileTypes: true });
  entries.sort((left, right) => left.name.localeCompare(right.name));

  const lines = [];
  for (let index = 0; index < entries.length; index += 1) {
    const entry = entries[index];
    const isLast = index === entries.length - 1;
    const branch = isLast ? '└── ' : '├── ';
    const nextPrefix = `${prefix}${isLast ? '    ' : '│   '}`;
    const fullPath = path.join(currentDir, entry.name);

    lines.push(`${prefix}${branch}${entry.name}${entry.isDirectory() ? '/' : ''}`);
    if (entry.isDirectory()) {
      const nestedLines = await buildTreeLines(rootDir, fullPath, nextPrefix);
      lines.push(...nestedLines);
    }
  }

  return lines;
}

async function buildTreeSnapshot(rootDir, label) {
  const lines = [label, ...(await buildTreeLines(rootDir))];
  return `${lines.join('\n')}\n`;
}

async function ensureCleanArtifactDir() {
  await fs.mkdir(ARTIFACT_DIR, { recursive: true });
}

async function writeArtifact(filename, content) {
  await fs.writeFile(path.join(ARTIFACT_DIR, filename), content);
}

async function createSigningKeyPair(rootDir) {
  const { privateKey, publicKey } = crypto.generateKeyPairSync('ed25519');
  const privateKeyPath = path.join(rootDir, 'demo-manifest-signer.pem');
  const publicKeyPath = path.join(rootDir, 'demo-manifest-signer.pub.pem');
  await fs.writeFile(privateKeyPath, privateKey.export({ format: 'pem', type: 'pkcs8' }));
  await fs.writeFile(publicKeyPath, publicKey.export({ format: 'pem', type: 'spki' }));
  return {
    privateKeyPath,
    publicKeyPath,
  };
}

async function createDemoInput(rootDir) {
  const downloadsDir = path.join(rootDir, 'downloads');
  await fs.mkdir(downloadsDir, { recursive: true });

  const rawConfig = {
    buckets: {
      ' screenshots ': {
        basenamePatterns: [' Screenshot * '],
      },
      datasets: {
        extensions: ['CSV'],
        mimeTypes: [' Application/JSON '],
      },
      assignments: {
        extensions: ['TXT'],
        basenamePatterns: [' assignment-* '],
      },
      visuals: {
        mimePrefixes: [' image/* '],
      },
    },
    fallbackBucket: ' coursework-misc ',
    owner: 'portfolio-demo',
  };

  const rawConfigPath = path.join(rootDir, 'coursework-demo.raw.json');
  await fs.writeFile(rawConfigPath, `${JSON.stringify(rawConfig, null, 2)}\n`);

  await fs.writeFile(path.join(downloadsDir, 'Screenshot 2026-04-18.png'), Buffer.from('fake screenshot bytes\n'));
  await fs.writeFile(path.join(downloadsDir, 'assignment-2.txt'), 'Prepare the streaming systems write-up.\n');
  await fs.writeFile(path.join(downloadsDir, 'course-data.csv'), 'student,score\nAda,98\nGrace,96\n');
  await fs.writeFile(path.join(downloadsDir, 'notes.md'), '# sprint notes\n- tighten README screenshots\n');
  await fs.writeFile(path.join(downloadsDir, 'report.txt'), '{"kind":"benchmark-summary","passed":true}\n');
  await fs.writeFile(path.join(downloadsDir, 'diagram.txt'), '<svg viewBox="0 0 10 10"><rect width="10" height="10"/></svg>\n');

  return {
    downloadsDir,
    rawConfigPath,
  };
}

async function generateArtifacts() {
  await ensureCleanArtifactDir();

  const tempRoot = await fs.mkdtemp(path.join(os.tmpdir(), 'file-organizer-demo-'));
  try {
    const { downloadsDir, rawConfigPath } = await createDemoInput(tempRoot);
    const { privateKeyPath, publicKeyPath } = await createSigningKeyPair(tempRoot);
    const normalizedConfigPath = path.join(tempRoot, 'coursework-demo.normalized.json');
    const manifestPath = path.join(tempRoot, 'demo-manifest.json');
    const signaturePath = path.join(tempRoot, 'demo-manifest.sig.json');

    const previewResult = await previewNormalizedBucketConfig(rawConfigPath);
    const normalizedWriteResult = await writeNormalizedBucketConfig(rawConfigPath, normalizedConfigPath, { force: true });
    const bucketConfig = await loadBucketConfig(normalizedConfigPath);

    const beforeTree = await buildTreeSnapshot(downloadsDir, 'downloads/');
    const dryRunResult = await organize(downloadsDir, {
      dryRun: true,
      recursive: false,
      bucketConfig,
    });
    const organizeResult = await organize(downloadsDir, {
      dryRun: false,
      recursive: false,
      bucketConfig,
    });
    const manifestResult = await writeManifest(organizeResult, manifestPath, { includeChecksum: true });
    const signatureResult = await writeDetachedManifestSignature(manifestPath, privateKeyPath, { signaturePath });
    manifestResult.detachedSignature = signatureResult;
    const signatureVerification = await verifyDetachedManifestSignature(manifestPath, publicKeyPath, { signaturePath });
    const afterTree = await buildTreeSnapshot(downloadsDir, 'downloads/');
    const undoResult = await undoFromManifest(manifestPath, {
      verifySignatureKeyPath: publicKeyPath,
      signaturePath,
    });
    const restoredTree = await buildTreeSnapshot(downloadsDir, 'downloads/');

    const sanitizedPreview = sanitizeForArtifact(previewResult, tempRoot);
    const sanitizedNormalizedWrite = sanitizeForArtifact(normalizedWriteResult, tempRoot);
    const sanitizedDryRun = sanitizeForArtifact(dryRunResult, tempRoot);
    const sanitizedApply = sanitizeForArtifact(manifestResult, tempRoot);
    const sanitizedSignature = sanitizeForArtifact(signatureResult, tempRoot);
    const sanitizedSignatureVerification = sanitizeForArtifact(signatureVerification, tempRoot);
    const sanitizedUndo = sanitizeForArtifact(undoResult, tempRoot);
    const sanitizedRawConfig = sanitizeForArtifact(JSON.parse(await fs.readFile(rawConfigPath, 'utf8')), tempRoot);
    const sanitizedNormalizedConfig = sanitizeForArtifact(JSON.parse(await fs.readFile(normalizedConfigPath, 'utf8')), tempRoot);
    const sanitizedPublicKey = sanitizeForArtifact(await fs.readFile(publicKeyPath, 'utf8'), tempRoot);

    await writeArtifact('demo-source-tree.txt', beforeTree);
    await writeArtifact('demo-after-tree.txt', afterTree);
    await writeArtifact('demo-restored-tree.txt', restoredTree);
    await writeArtifact('demo-config.raw.json', `${JSON.stringify(sanitizedRawConfig, null, 2)}\n`);
    await writeArtifact('demo-config.preview.txt', `${formatTextReport(sanitizedPreview)}\n`);
    await writeArtifact('demo-config.normalized.json', `${JSON.stringify(sanitizedNormalizedConfig, null, 2)}\n`);
    await writeArtifact('demo-normalized-write.txt', `${formatTextReport(sanitizedNormalizedWrite)}\n`);
    await writeArtifact('demo-dry-run-report.txt', `${formatTextReport(sanitizedDryRun)}\n`);
    await writeArtifact('demo-apply-report.txt', `${formatTextReport(sanitizedApply)}\n`);
    await writeArtifact('demo-manifest.json', `${JSON.stringify(sanitizedApply, null, 2)}\n`);
    await writeArtifact('demo-manifest.sig.json', `${JSON.stringify(sanitizedSignature, null, 2)}\n`);
    await writeArtifact('demo-signature-verify.txt', `${JSON.stringify(sanitizedSignatureVerification, null, 2)}\n`);
    await writeArtifact('demo-manifest-signer.pub.pem', sanitizedPublicKey);
    await writeArtifact('demo-undo-report.txt', `${formatTextReport(sanitizedUndo)}\n`);

    const summary = [
      '# File organizer demo artifact bundle',
      '',
      'This bundle is generated by `npm run demo:artifacts --prefix projects/file-organizer-cli` and gives the README/portfolio a concrete before/after walkthrough.',
      '',
      '## Included artifacts',
      '- [`demo-source-tree.txt`](./demo-source-tree.txt) — loose input folder before organizing',
      '- [`demo-config.raw.json`](./demo-config.raw.json) — warning-heavy shared config before cleanup',
      '- [`demo-config.preview.txt`](./demo-config.preview.txt) — normalization-preview output for the raw config',
      '- [`demo-config.normalized.json`](./demo-config.normalized.json) — canonical config used for the run',
      '- [`demo-normalized-write.txt`](./demo-normalized-write.txt) — normalization-write report for the canonical config export',
      '- [`demo-dry-run-report.txt`](./demo-dry-run-report.txt) — preview of the planned moves',
      '- [`demo-apply-report.txt`](./demo-apply-report.txt) — real organize run with checksum-backed manifest recording',
      '- [`demo-manifest.json`](./demo-manifest.json) — sanitized manifest/report payload captured from the real run',
      '- [`demo-manifest.sig.json`](./demo-manifest.sig.json) — detached signature sidecar for the manifest',
      '- [`demo-manifest-signer.pub.pem`](./demo-manifest-signer.pub.pem) — public verification key published with the bundle',
      '- [`demo-signature-verify.txt`](./demo-signature-verify.txt) — detached-signature verification proof before undo',
      '- [`demo-after-tree.txt`](./demo-after-tree.txt) — folder tree after the organize pass',
      '- [`demo-undo-report.txt`](./demo-undo-report.txt) — manifest-driven rollback proof',
      '- [`demo-restored-tree.txt`](./demo-restored-tree.txt) — folder tree after undo restores the original layout',
      '',
      '## Before tree',
      '```text',
      beforeTree.trimEnd(),
      '```',
      '',
      '## Config preview excerpt',
      '```text',
      formatTextReport(sanitizedPreview).trimEnd(),
      '```',
      '',
      '## After tree',
      '```text',
      afterTree.trimEnd(),
      '```',
      '',
      '## What the bundle demonstrates',
      '- basename-pattern routing for screenshots and assignments',
      '- MIME-aware routing for misleading `.txt` files that actually contain JSON or SVG',
      '- normalization-preview + canonical shared-config writing before a real organize run',
      '- checksum-backed manifest capture plus detached-signature sidecar generation',
      '- detached-signature verification with a published public key before undo',
      '- dry-run preview and successful rollback back to the original loose tree',
      '',
      '## Notes',
      '- committed reports replace the temporary smoke-run root with the stable placeholder `/demo/file-organizer-cli` so the artifacts stay readable in Git',
      '- the bundle publishes only the generated public verification key; the temporary private signing key never leaves the isolated smoke-test folder',
      '- the real smoke test still runs against an isolated temporary folder before these sanitized artifacts are written',
      '',
    ].join('\n');

    await writeArtifact('demo-summary.md', summary);
  } finally {
    await fs.rm(tempRoot, { recursive: true, force: true });
  }
}

generateArtifacts().catch(error => {
  console.error(error && error.stack ? error.stack : error);
  process.exit(1);
});
