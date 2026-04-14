const fs = require('fs/promises');
const path = require('path');

const IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'];
const DOCUMENT_EXTENSIONS = ['.pdf', '.doc', '.docx', '.txt', '.md', '.rtf'];
const AUDIO_EXTENSIONS = ['.mp3', '.wav', '.flac', '.m4a'];
const CODE_EXTENSIONS = ['.js', '.py', '.ts', '.java', '.cpp', '.c', '.cs', '.go', '.rs'];
const ARCHIVE_EXTENSIONS = ['.zip', '.tar', '.gz', '.tgz'];

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

async function organize(dir, options = {}) {
  const settings = {
    dryRun: false,
    recursive: false,
    ...options,
  };

  const reservedBuckets = new Set(['images', 'documents', 'audio', 'code', 'archives', 'other']);
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
    rootDir: path.resolve(dir),
    dryRun: settings.dryRun,
    recursive: settings.recursive,
    moves,
    summary: summarizeMoves(moves),
  };
}

function parseArgs(argv) {
  const args = [...argv];
  const options = { dryRun: false, recursive: false, json: false };
  let targetDir = '.';

  for (const arg of args) {
    if (arg === '--dry-run') {
      options.dryRun = true;
    } else if (arg === '--recursive') {
      options.recursive = true;
    } else if (arg === '--json') {
      options.json = true;
    } else if (arg === '--help' || arg === '-h') {
      options.help = true;
    } else if (!arg.startsWith('-')) {
      targetDir = arg;
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  return { targetDir, options };
}

function formatTextReport(result) {
  const header = [
    `root: ${result.rootDir}`,
    `mode: ${result.dryRun ? 'dry-run' : 'apply'}`,
    `recursive: ${result.recursive ? 'yes' : 'no'}`,
    `total moves: ${result.summary.total}`,
    `renamed to avoid collisions: ${result.summary.renamed}`,
  ];

  const bucketLines = Object.entries(result.summary.byBucket)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([bucket, count]) => `bucket ${bucket}: ${count}`);

  const moveLines = result.moves.map(move => {
    const suffix = move.renamed ? ' [renamed]' : '';
    return `${move.from} -> ${move.to}${suffix}`;
  });

  return [...header, ...bucketLines, ...moveLines].join('\n');
}

async function main(argv = process.argv.slice(2)) {
  const { targetDir, options } = parseArgs(argv);

  if (options.help) {
    console.log('Usage: node organizer.js [directory] [--dry-run] [--recursive] [--json]');
    return;
  }

  const result = await organize(targetDir, options);
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
  bucketFor,
  pathExists,
  uniqueDestination,
  moveFile,
  organize,
  parseArgs,
  formatTextReport,
};
