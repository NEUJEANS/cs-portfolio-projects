const fs = require('fs/promises');
const path = require('path');

const IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'];
const DOCUMENT_EXTENSIONS = ['.pdf', '.doc', '.docx', '.txt', '.md', '.rtf'];
const AUDIO_EXTENSIONS = ['.mp3', '.wav', '.flac', '.m4a'];
const CODE_EXTENSIONS = ['.js', '.py', '.ts', '.java', '.cpp', '.c', '.cs', '.go', '.rs'];
const ARCHIVE_EXTENSIONS = ['.zip', '.tar', '.gz', '.tgz'];
const RESERVED_BUCKETS = ['images', 'documents', 'audio', 'code', 'archives', 'other'];

function bucketFor(filename) {
  const ext = path.extname(filename).toLowerCase();
  if (IMAGE_EXTENSIONS.includes(ext)) return 'images';
  if (DOCUMENT_EXTENSIONS.includes(ext)) return 'documents';
  if (AUDIO_EXTENSIONS.includes(ext)) return 'audio';
  if (CODE_EXTENSIONS.includes(ext)) return 'code';
  if (ARCHIVE_EXTENSIONS.includes(ext)) return 'archives';
  return 'other';
}

async function pathExists(targetPath) {
  try {
    await fs.access(targetPath);
    return true;
  } catch {
    return false;
  }
}

async function uniqueDestination(targetPath) {
  if (!(await pathExists(targetPath))) {
    return targetPath;
  }

  const directory = path.dirname(targetPath);
  const extension = path.extname(targetPath);
  const baseName = path.basename(targetPath, extension);

  let counter = 1;
  while (true) {
    const candidate = path.join(directory, `${baseName} (${counter})${extension}`);
    if (!(await pathExists(candidate))) {
      return candidate;
    }
    counter += 1;
  }
}

async function moveFile(from, to) {
  try {
    await fs.rename(from, to);
  } catch (error) {
    if (error && error.code === 'EXDEV') {
      await fs.copyFile(from, to);
      await fs.unlink(from);
      return;
    }
    throw error;
  }
}

async function collectFiles(dir, { recursive, reservedBuckets }) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const files = [];

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isFile()) {
      files.push(fullPath);
      continue;
    }

    if (!recursive || !entry.isDirectory() || reservedBuckets.has(entry.name)) {
      continue;
    }

    const nestedFiles = await collectFiles(fullPath, { recursive, reservedBuckets });
    files.push(...nestedFiles);
  }

  return files;
}

function summarizeMoves(moves) {
  return moves.reduce((summary, move) => {
    summary.total += 1;
    summary.byBucket[move.bucket] = (summary.byBucket[move.bucket] || 0) + 1;
    if (move.renamed) {
      summary.renamed += 1;
    }
    return summary;
  }, { total: 0, renamed: 0, byBucket: {} });
}

function summarizeUndo(moves, removedDirectoryCount) {
  return moves.reduce((summary, move) => {
    summary.total += 1;
    if (move.status === 'missing') {
      summary.missing += 1;
      return summary;
    }

    summary.restored += 1;
    summary.byBucket[move.bucket] = (summary.byBucket[move.bucket] || 0) + 1;
    if (move.restoreRenamed) {
      summary.restoreRenamed += 1;
    }
    return summary;
  }, {
    total: 0,
    restored: 0,
    missing: 0,
    restoreRenamed: 0,
    removedDirectories: removedDirectoryCount,
    byBucket: {},
  });
}

async function organize(dir, options = {}) {
  const settings = {
    dryRun: false,
    recursive: false,
    ...options,
  };

  const reservedBuckets = new Set(RESERVED_BUCKETS);
  const files = await collectFiles(dir, { recursive: settings.recursive, reservedBuckets });
  const moves = [];

  for (const sourcePath of files) {
    const filename = path.basename(sourcePath);
    const sourceDirectory = path.dirname(sourcePath);
    const bucket = bucketFor(filename);
    const targetDir = path.join(sourceDirectory, bucket);
    const requestedDestination = path.join(targetDir, filename);
    const destinationPath = await uniqueDestination(requestedDestination);
    const renamed = destinationPath !== requestedDestination;

    if (!settings.dryRun) {
      await fs.mkdir(targetDir, { recursive: true });
      await moveFile(sourcePath, destinationPath);
    }

    moves.push({
      from: sourcePath,
      to: destinationPath,
      bucket,
      renamed,
      dryRun: settings.dryRun,
    });
  }

  return {
    action: 'organize',
    createdAt: new Date().toISOString(),
    rootDir: path.resolve(dir),
    dryRun: settings.dryRun,
    recursive: settings.recursive,
    moves,
    summary: summarizeMoves(moves),
  };
}

async function writeManifest(result, manifestPath) {
  const resolvedPath = path.resolve(manifestPath);
  const manifest = {
    ...result,
    manifestPath: resolvedPath,
  };

  await fs.mkdir(path.dirname(resolvedPath), { recursive: true });
  await fs.writeFile(resolvedPath, `${JSON.stringify(manifest, null, 2)}\n`);
  return manifest;
}

function isInsideRoot(rootDir, candidateDir) {
  const relative = path.relative(rootDir, candidateDir);
  return relative !== '' && !relative.startsWith('..') && !path.isAbsolute(relative);
}

async function removeEmptyDirectories(startDir, stopDir) {
  const removed = [];
  let currentDir = path.resolve(startDir);
  const boundaryDir = path.resolve(stopDir);

  while (isInsideRoot(boundaryDir, currentDir)) {
    const entries = await fs.readdir(currentDir);
    if (entries.length > 0) {
      break;
    }
    await fs.rmdir(currentDir);
    removed.push(currentDir);
    currentDir = path.dirname(currentDir);
  }

  return removed;
}

async function undoFromManifest(manifestPath, options = {}) {
  const settings = {
    dryRun: false,
    ...options,
  };

  const resolvedManifestPath = path.resolve(manifestPath);
  const manifest = JSON.parse(await fs.readFile(resolvedManifestPath, 'utf8'));

  if (manifest.action !== 'organize' || !Array.isArray(manifest.moves)) {
    throw new Error('Undo manifest must be a JSON file produced by an organize run.');
  }

  if (manifest.dryRun) {
    throw new Error('Cannot undo a dry-run manifest because no files were moved.');
  }

  const rootDir = path.resolve(manifest.rootDir || path.dirname(resolvedManifestPath));
  const moves = [];
  const removedDirectories = new Set();

  for (const move of [...manifest.moves].reverse()) {
    const requestedRestore = move.from;
    const currentPath = move.to;

    if (!(await pathExists(currentPath))) {
      moves.push({
        from: currentPath,
        to: requestedRestore,
        requestedRestore,
        bucket: move.bucket,
        renamed: move.renamed,
        restoreRenamed: false,
        status: 'missing',
      });
      continue;
    }

    const restorePath = await uniqueDestination(requestedRestore);
    const restoreRenamed = restorePath !== requestedRestore;

    if (!settings.dryRun) {
      await fs.mkdir(path.dirname(restorePath), { recursive: true });
      await moveFile(currentPath, restorePath);
      const emptiedDirectories = await removeEmptyDirectories(path.dirname(currentPath), rootDir);
      emptiedDirectories.forEach(directory => removedDirectories.add(directory));
    }

    moves.push({
      from: currentPath,
      to: restorePath,
      requestedRestore,
      bucket: move.bucket,
      renamed: move.renamed,
      restoreRenamed,
      status: 'restored',
    });
  }

  return {
    action: 'undo',
    createdAt: new Date().toISOString(),
    rootDir,
    dryRun: settings.dryRun,
    manifestPath: resolvedManifestPath,
    removedDirectories: [...removedDirectories].sort(),
    moves,
    summary: summarizeUndo(moves, removedDirectories.size),
  };
}

function parseArgs(argv) {
  const args = [...argv];
  const options = {
    dryRun: false,
    recursive: false,
    json: false,
    manifestOut: null,
    undoManifest: null,
  };
  let targetDir = '.';
  let targetDirExplicit = false;

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];

    if (arg === '--dry-run') {
      options.dryRun = true;
    } else if (arg === '--recursive') {
      options.recursive = true;
    } else if (arg === '--json') {
      options.json = true;
    } else if (arg === '--manifest-out') {
      const nextArg = args[index + 1];
      if (!nextArg || nextArg.startsWith('-')) {
        throw new Error('Expected a path after --manifest-out');
      }
      options.manifestOut = nextArg;
      index += 1;
    } else if (arg === '--undo') {
      const nextArg = args[index + 1];
      if (!nextArg || nextArg.startsWith('-')) {
        throw new Error('Expected a path after --undo');
      }
      options.undoManifest = nextArg;
      index += 1;
    } else if (arg === '--help' || arg === '-h') {
      options.help = true;
    } else if (!arg.startsWith('-')) {
      if (targetDirExplicit) {
        throw new Error(`Unexpected extra argument: ${arg}`);
      }
      targetDir = arg;
      targetDirExplicit = true;
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  if (options.undoManifest && targetDirExplicit) {
    throw new Error('Target directory cannot be combined with --undo');
  }

  if (options.undoManifest && options.recursive) {
    throw new Error('--recursive cannot be used with --undo');
  }

  if (options.undoManifest && options.manifestOut) {
    throw new Error('--manifest-out cannot be used with --undo');
  }

  return { targetDir, options };
}

function formatOrganizeTextReport(result) {
  const header = [
    `root: ${result.rootDir}`,
    'action: organize',
    `mode: ${result.dryRun ? 'dry-run' : 'apply'}`,
    `recursive: ${result.recursive ? 'yes' : 'no'}`,
    `total moves: ${result.summary.total}`,
    `renamed to avoid collisions: ${result.summary.renamed}`,
  ];

  if (result.manifestPath) {
    header.push(`manifest: ${result.manifestPath}`);
  }

  const bucketLines = Object.entries(result.summary.byBucket)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([bucket, count]) => `bucket ${bucket}: ${count}`);

  const moveLines = result.moves.map(move => {
    const suffix = move.renamed ? ' [renamed]' : '';
    return `${move.from} -> ${move.to}${suffix}`;
  });

  return [...header, ...bucketLines, ...moveLines].join('\n');
}

function formatUndoTextReport(result) {
  const header = [
    `root: ${result.rootDir}`,
    'action: undo',
    `mode: ${result.dryRun ? 'dry-run' : 'apply'}`,
    `manifest: ${result.manifestPath}`,
    `total manifest entries: ${result.summary.total}`,
    `restored files: ${result.summary.restored}`,
    `missing current files: ${result.summary.missing}`,
    `renamed to avoid restore collisions: ${result.summary.restoreRenamed}`,
    `removed empty directories: ${result.summary.removedDirectories}`,
  ];

  const bucketLines = Object.entries(result.summary.byBucket)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([bucket, count]) => `bucket ${bucket}: ${count}`);

  const moveLines = result.moves.map(move => {
    if (move.status === 'missing') {
      return `${move.from} -> ${move.requestedRestore} [missing]`;
    }

    const suffix = move.restoreRenamed
      ? ` [restore-renamed from ${move.requestedRestore}]`
      : '';
    return `${move.from} -> ${move.to}${suffix}`;
  });

  return [...header, ...bucketLines, ...moveLines].join('\n');
}

function formatTextReport(result) {
  if (result.action === 'undo') {
    return formatUndoTextReport(result);
  }
  return formatOrganizeTextReport(result);
}

async function main(argv = process.argv.slice(2)) {
  const { targetDir, options } = parseArgs(argv);

  if (options.help) {
    console.log('Usage: node organizer.js [directory] [--dry-run] [--recursive] [--json] [--manifest-out manifest.json]');
    console.log('       node organizer.js --undo manifest.json [--dry-run] [--json]');
    return;
  }

  let result;
  if (options.undoManifest) {
    result = await undoFromManifest(options.undoManifest, { dryRun: options.dryRun });
  } else {
    result = await organize(targetDir, options);
    if (options.manifestOut) {
      result = await writeManifest(result, options.manifestOut);
    }
  }

  if (options.json) {
    console.log(JSON.stringify(result, null, 2));
  } else {
    console.log(formatTextReport(result));
  }
}

if (require.main === module) {
  main().catch(error => {
    console.error(error.message || error);
    process.exit(1);
  });
}

module.exports = {
  RESERVED_BUCKETS,
  bucketFor,
  pathExists,
  uniqueDestination,
  moveFile,
  organize,
  writeManifest,
  undoFromManifest,
  parseArgs,
  formatTextReport,
  removeEmptyDirectories,
};
