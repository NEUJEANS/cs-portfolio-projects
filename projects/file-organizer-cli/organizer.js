const fs = require('fs/promises');
const path = require('path');

const DEFAULT_BUCKET_RULES = Object.freeze({
  images: ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'],
  documents: ['.pdf', '.doc', '.docx', '.txt', '.md', '.rtf'],
  audio: ['.mp3', '.wav', '.flac', '.m4a'],
  code: ['.js', '.py', '.ts', '.java', '.cpp', '.c', '.cs', '.go', '.rs'],
  archives: ['.zip', '.tar', '.gz', '.tgz'],
});
const DEFAULT_FALLBACK_BUCKET = 'other';
const PRESET_LIBRARY = Object.freeze({
  coursework: Object.freeze({
    description: 'separate datasets, notebooks, slides, and diagram assets for class deliverables',
    config: Object.freeze({
      buckets: Object.freeze({
        datasets: Object.freeze(['.csv', '.tsv', '.json']),
        notebooks: Object.freeze(['.ipynb']),
        slides: Object.freeze(['.ppt', '.pptx', '.key']),
        diagrams: Object.freeze(['.drawio', '.vsdx']),
      }),
      fallbackBucket: 'coursework-misc',
      extendDefaults: true,
    }),
  }),
  'data-science': Object.freeze({
    description: 'highlight datasets, notebooks, figures, and experiment manifests for analysis-heavy folders',
    config: Object.freeze({
      buckets: Object.freeze({
        datasets: Object.freeze(['.csv', '.tsv', '.json', '.parquet']),
        notebooks: Object.freeze(['.ipynb']),
        figures: Object.freeze(['.png', '.jpg', '.jpeg', '.svg']),
        experiments: Object.freeze(['.yaml', '.yml', '.toml']),
      }),
      fallbackBucket: 'lab-misc',
      extendDefaults: true,
    }),
  }),
  'frontend-assets': Object.freeze({
    description: 'group mockups, vector design files, screen recordings, and handoff notes for UI portfolios',
    config: Object.freeze({
      buckets: Object.freeze({
        mockups: Object.freeze(['.fig', '.sketch', '.xd']),
        vectors: Object.freeze(['.ai', '.eps']),
        captures: Object.freeze(['.mp4', '.mov', '.webm']),
        handoff: Object.freeze(['.pdf', '.docx']),
      }),
      fallbackBucket: 'frontend-misc',
      extendDefaults: true,
    }),
  }),
});
const CONFIG_ALLOWED_KEYS = Object.freeze(['buckets', 'fallbackBucket', 'extendDefaults']);

function normalizeBucketName(name, label = 'bucket name') {
  if (typeof name !== 'string') {
    throw new Error(`Expected ${label} to be a string.`);
  }

  const trimmed = name.trim();
  if (!trimmed) {
    throw new Error(`Expected ${label} to be a non-empty string.`);
  }

  if (trimmed === '.' || trimmed === '..' || trimmed.includes('/') || trimmed.includes('\\')) {
    throw new Error(`Bucket names must be simple directory names: ${trimmed}`);
  }

  return trimmed;
}

function normalizeExtension(extension, bucketName) {
  if (typeof extension !== 'string') {
    throw new Error(`Expected every extension in bucket ${bucketName} to be a string.`);
  }

  const trimmed = extension.trim().toLowerCase();
  if (!trimmed || trimmed === '.') {
    throw new Error(`Extensions in bucket ${bucketName} must be non-empty.`);
  }

  return trimmed.startsWith('.') ? trimmed : `.${trimmed}`;
}

function normalizeExtendDefaults(value) {
  if (value == null) {
    return true;
  }

  if (typeof value !== 'boolean') {
    throw new Error('Field "extendDefaults" must be true or false when provided.');
  }

  return value;
}

function normalizeCustomBuckets(buckets) {
  if (buckets == null) {
    return {};
  }

  if (Array.isArray(buckets) || typeof buckets !== 'object') {
    throw new Error('Bucket config field "buckets" must be a JSON object that maps bucket names to extension arrays.');
  }

  const normalized = {};
  const extensionOwners = new Map();
  const bucketNameOwners = new Map();

  for (const [rawBucketName, rawExtensions] of Object.entries(buckets)) {
    const bucketName = normalizeBucketName(rawBucketName, 'bucket name');
    const normalizedOwner = bucketNameOwners.get(bucketName);
    if (normalizedOwner && normalizedOwner !== rawBucketName) {
      throw new Error(`Bucket names normalize to the same directory name (${normalizedOwner}, ${rawBucketName} -> ${bucketName}).`);
    }
    bucketNameOwners.set(bucketName, rawBucketName);

    if (!Array.isArray(rawExtensions) || rawExtensions.length === 0) {
      throw new Error(`Bucket ${bucketName} must list at least one extension.`);
    }

    const extensions = [];
    for (const rawExtension of rawExtensions) {
      const extension = normalizeExtension(rawExtension, bucketName);
      const owner = extensionOwners.get(extension);
      if (owner && owner !== bucketName) {
        throw new Error(`Extension ${extension} is assigned to multiple custom buckets (${owner}, ${bucketName}).`);
      }
      extensionOwners.set(extension, bucketName);
      if (!extensions.includes(extension)) {
        extensions.push(extension);
      }
    }

    normalized[bucketName] = extensions;
  }

  return normalized;
}

function buildBucketConfig(config = {}) {
  if (config == null || Array.isArray(config) || typeof config !== 'object') {
    throw new Error('Bucket config must be a JSON object.');
  }

  const extendDefaults = normalizeExtendDefaults(config.extendDefaults);
  const fallbackBucket = normalizeBucketName(
    config.fallbackBucket || DEFAULT_FALLBACK_BUCKET,
    'fallback bucket',
  );
  const customBuckets = normalizeCustomBuckets(config.buckets);
  const extensionToBucket = new Map();
  const bucketNames = [];

  const registerBucketRules = (rules) => {
    for (const [bucketName, extensions] of Object.entries(rules)) {
      if (!bucketNames.includes(bucketName)) {
        bucketNames.push(bucketName);
      }

      for (const extension of extensions) {
        if (!extensionToBucket.has(extension)) {
          extensionToBucket.set(extension, bucketName);
        }
      }
    }
  };

  registerBucketRules(customBuckets);
  if (extendDefaults) {
    registerBucketRules(DEFAULT_BUCKET_RULES);
  }
  if (!bucketNames.includes(fallbackBucket)) {
    bucketNames.push(fallbackBucket);
  }

  return {
    configPath: null,
    extendDefaults,
    fallbackBucket,
    customBuckets,
    bucketNames,
    extensionToBucket,
  };
}

const DEFAULT_BUCKET_CONFIG = buildBucketConfig();
const RESERVED_BUCKETS = Object.freeze([...DEFAULT_BUCKET_CONFIG.bucketNames]);

function cloneBucketTemplate(config = {}) {
  return {
    buckets: Object.fromEntries(
      Object.entries(config.buckets || {}).map(([bucketName, extensions]) => [bucketName, [...extensions]]),
    ),
    fallbackBucket: config.fallbackBucket || DEFAULT_FALLBACK_BUCKET,
    extendDefaults: normalizeExtendDefaults(config.extendDefaults),
  };
}

function presetNames() {
  return Object.keys(PRESET_LIBRARY).sort();
}

function getPresetDefinition(presetName) {
  const preset = PRESET_LIBRARY[presetName];
  if (!preset) {
    throw new Error(`Unknown preset: ${presetName}. Supported presets: ${presetNames().join(', ')}`);
  }
  return preset;
}

function listPresetCatalog() {
  return presetNames().map((name) => {
    const preset = PRESET_LIBRARY[name];
    const config = cloneBucketTemplate(preset.config);
    return {
      name,
      description: preset.description,
      bucketNames: Object.keys(config.buckets),
      bucketCount: Object.keys(config.buckets).length,
      fallbackBucket: config.fallbackBucket,
      extendDefaults: config.extendDefaults,
      config,
    };
  });
}

function loadPresetBucketConfig(presetName) {
  const preset = getPresetDefinition(presetName);
  return {
    ...buildBucketConfig(cloneBucketTemplate(preset.config)),
    presetName,
    presetDescription: preset.description,
  };
}

async function writePresetConfig(presetName, destinationPath, options = {}) {
  const settings = {
    force: false,
    ...options,
  };
  const preset = getPresetDefinition(presetName);
  const resolvedPath = path.resolve(destinationPath);

  if (!settings.force && await pathExists(resolvedPath)) {
    throw new Error(`Preset destination already exists: ${resolvedPath}`);
  }

  const config = cloneBucketTemplate(preset.config);
  await fs.mkdir(path.dirname(resolvedPath), { recursive: true });
  await fs.writeFile(resolvedPath, `${JSON.stringify(config, null, 2)}\n`);

  return {
    action: 'write-preset',
    presetName,
    description: preset.description,
    destination: resolvedPath,
    bucketNames: Object.keys(config.buckets),
    bucketCount: Object.keys(config.buckets).length,
    fallbackBucket: config.fallbackBucket,
    extendDefaults: config.extendDefaults,
  };
}

async function loadBucketConfig(configPath) {
  const resolvedPath = path.resolve(configPath);
  let raw;

  try {
    raw = await fs.readFile(resolvedPath, 'utf8');
  } catch (error) {
    if (error && error.code === 'ENOENT') {
      throw new Error(`Bucket config file not found: ${resolvedPath}`);
    }
    throw error;
  }

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (error) {
    throw new Error(`Bucket config file must contain valid JSON: ${resolvedPath}`);
  }

  return {
    ...buildBucketConfig(parsed),
    configPath: resolvedPath,
  };
}

async function lintBucketConfig(configPath) {
  const resolvedPath = path.resolve(configPath);
  let raw;

  try {
    raw = await fs.readFile(resolvedPath, 'utf8');
  } catch (error) {
    if (error && error.code === 'ENOENT') {
      return {
        action: 'lint-config',
        configPath: resolvedPath,
        valid: false,
        errors: [`Bucket config file not found: ${resolvedPath}`],
        warnings: [],
        normalizedConfig: null,
      };
    }
    throw error;
  }

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (error) {
    return {
      action: 'lint-config',
      configPath: resolvedPath,
      valid: false,
      errors: [`Bucket config file must contain valid JSON: ${resolvedPath}`],
      warnings: [],
      normalizedConfig: null,
    };
  }

  const errors = [];
  const warnings = [];

  if (parsed == null || Array.isArray(parsed) || typeof parsed !== 'object') {
    errors.push('Bucket config must be a JSON object.');
  } else {
    for (const key of Object.keys(parsed)) {
      if (!CONFIG_ALLOWED_KEYS.includes(key)) {
        warnings.push(`Unknown top-level key "${key}" will be ignored by the organizer.`);
      }
    }

    if (parsed.extendDefaults != null && typeof parsed.extendDefaults !== 'boolean') {
      errors.push('Field "extendDefaults" must be true or false when provided.');
    }

    if (parsed.fallbackBucket != null) {
      try {
        const normalizedFallbackBucket = normalizeBucketName(parsed.fallbackBucket, 'fallback bucket');
        if (parsed.fallbackBucket !== normalizedFallbackBucket) {
          warnings.push(`Fallback bucket "${parsed.fallbackBucket}" will normalize to "${normalizedFallbackBucket}".`);
        }
      } catch (error) {
        errors.push(error.message);
      }
    }

    if (parsed.buckets != null) {
      if (Array.isArray(parsed.buckets) || typeof parsed.buckets !== 'object') {
        errors.push('Bucket config field "buckets" must be a JSON object that maps bucket names to extension arrays.');
      } else {
        const extensionOwners = new Map();
        const normalizedBucketNames = new Map();

        for (const [rawBucketName, rawExtensions] of Object.entries(parsed.buckets)) {
          let bucketName;
          try {
            bucketName = normalizeBucketName(rawBucketName, 'bucket name');
            if (rawBucketName !== bucketName) {
              warnings.push(`Bucket name "${rawBucketName}" will normalize to "${bucketName}".`);
            }
          } catch (error) {
            errors.push(error.message);
            continue;
          }

          const normalizedOwner = normalizedBucketNames.get(bucketName);
          if (normalizedOwner && normalizedOwner !== rawBucketName) {
            errors.push(`Bucket names normalize to the same directory name (${normalizedOwner}, ${rawBucketName} -> ${bucketName}).`);
          } else {
            normalizedBucketNames.set(bucketName, rawBucketName);
          }

          if (!Array.isArray(rawExtensions) || rawExtensions.length === 0) {
            errors.push(`Bucket ${bucketName} must list at least one extension.`);
            continue;
          }

          const bucketExtensions = new Set();
          for (const rawExtension of rawExtensions) {
            let normalizedExtension;
            try {
              normalizedExtension = normalizeExtension(rawExtension, bucketName);
              if (typeof rawExtension === 'string' && rawExtension !== normalizedExtension) {
                warnings.push(`Bucket ${bucketName} extension "${rawExtension}" will normalize to "${normalizedExtension}".`);
              }
            } catch (error) {
              errors.push(error.message);
              continue;
            }

            if (bucketExtensions.has(normalizedExtension)) {
              warnings.push(`Bucket ${bucketName} repeats extension "${normalizedExtension}"; duplicate entries are ignored.`);
              continue;
            }
            bucketExtensions.add(normalizedExtension);

            const owner = extensionOwners.get(normalizedExtension);
            if (owner && owner !== bucketName) {
              errors.push(`Extension ${normalizedExtension} is assigned to multiple custom buckets (${owner}, ${bucketName}).`);
            } else {
              extensionOwners.set(normalizedExtension, bucketName);
            }
          }
        }
      }
    }
  }

  let normalizedConfig = null;
  if (errors.length === 0) {
    const builtConfig = buildBucketConfig(parsed);
    normalizedConfig = {
      buckets: builtConfig.customBuckets,
      fallbackBucket: builtConfig.fallbackBucket,
      extendDefaults: builtConfig.extendDefaults,
      bucketNames: builtConfig.bucketNames,
    };
  }

  return {
    action: 'lint-config',
    configPath: resolvedPath,
    valid: errors.length === 0,
    errors,
    warnings,
    normalizedConfig,
  };
}

function describeBucketConfig(bucketConfig) {
  return {
    configPath: bucketConfig.configPath,
    presetName: bucketConfig.presetName || null,
    presetDescription: bucketConfig.presetDescription || null,
    extendDefaults: bucketConfig.extendDefaults,
    fallbackBucket: bucketConfig.fallbackBucket,
    bucketNames: [...bucketConfig.bucketNames],
    customBuckets: bucketConfig.customBuckets,
  };
}

function bucketFor(filename, bucketConfig = DEFAULT_BUCKET_CONFIG) {
  const ext = path.extname(filename).toLowerCase();
  return bucketConfig.extensionToBucket.get(ext) || bucketConfig.fallbackBucket;
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

async function collectFiles(dir, { recursive, reservedBuckets, skipPaths }) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const files = [];

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    const resolvedFullPath = path.resolve(fullPath);

    if (skipPaths.has(resolvedFullPath)) {
      continue;
    }

    if (entry.isFile()) {
      files.push(fullPath);
      continue;
    }

    if (!recursive || !entry.isDirectory() || reservedBuckets.has(entry.name)) {
      continue;
    }

    const nestedFiles = await collectFiles(fullPath, { recursive, reservedBuckets, skipPaths });
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
    bucketConfig: DEFAULT_BUCKET_CONFIG,
    skipPaths: [],
    ...options,
  };

  const reservedBuckets = new Set(settings.bucketConfig.bucketNames);
  const skipPaths = new Set(settings.skipPaths.map(candidate => path.resolve(candidate)));
  if (settings.bucketConfig.configPath) {
    skipPaths.add(path.resolve(settings.bucketConfig.configPath));
  }
  const files = await collectFiles(dir, { recursive: settings.recursive, reservedBuckets, skipPaths });
  const moves = [];

  for (const sourcePath of files) {
    const filename = path.basename(sourcePath);
    const sourceDirectory = path.dirname(sourcePath);
    const bucket = bucketFor(filename, settings.bucketConfig);
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
    bucketConfig: describeBucketConfig(settings.bucketConfig),
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
    configPath: null,
    lintConfigPath: null,
    presetName: null,
    listPresets: false,
    writePresetName: null,
    writePresetDestination: null,
    force: false,
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
    } else if (arg === '--config') {
      const nextArg = args[index + 1];
      if (!nextArg || nextArg.startsWith('-')) {
        throw new Error('Expected a path after --config');
      }
      options.configPath = nextArg;
      index += 1;
    } else if (arg === '--lint-config') {
      const nextArg = args[index + 1];
      if (!nextArg || nextArg.startsWith('-')) {
        throw new Error('Expected a path after --lint-config');
      }
      options.lintConfigPath = nextArg;
      index += 1;
    } else if (arg === '--preset') {
      const nextArg = args[index + 1];
      if (!nextArg || nextArg.startsWith('-')) {
        throw new Error('Expected a preset name after --preset');
      }
      options.presetName = nextArg;
      index += 1;
    } else if (arg === '--list-presets') {
      options.listPresets = true;
    } else if (arg === '--write-preset') {
      const presetName = args[index + 1];
      const destination = args[index + 2];
      if (!presetName || presetName.startsWith('-')) {
        throw new Error('Expected a preset name after --write-preset');
      }
      if (!destination || destination.startsWith('-')) {
        throw new Error('Expected a destination path after --write-preset <preset>');
      }
      options.writePresetName = presetName;
      options.writePresetDestination = destination;
      index += 2;
    } else if (arg === '--force') {
      options.force = true;
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

  if (options.undoManifest && options.configPath) {
    throw new Error('--config cannot be used with --undo');
  }

  if (options.undoManifest && options.presetName) {
    throw new Error('--preset cannot be used with --undo');
  }

  if (options.configPath && options.presetName) {
    throw new Error('--config cannot be combined with --preset');
  }

  if (options.lintConfigPath && targetDirExplicit) {
    throw new Error('Target directory cannot be combined with --lint-config');
  }

  if (options.lintConfigPath && (options.dryRun || options.undoManifest || options.manifestOut || options.recursive || options.configPath || options.presetName || options.listPresets || options.writePresetName || options.force)) {
    throw new Error('--lint-config cannot be combined with organize, undo, or preset-export flags');
  }

  if (options.listPresets && targetDirExplicit) {
    throw new Error('Target directory cannot be combined with --list-presets');
  }

  if (options.listPresets && (options.dryRun || options.undoManifest || options.manifestOut || options.recursive || options.configPath || options.presetName || options.writePresetName || options.force)) {
    throw new Error('--list-presets only supports optional --json output');
  }

  if (options.writePresetName && targetDirExplicit) {
    throw new Error('Target directory cannot be combined with --write-preset');
  }

  if (options.writePresetName && (options.dryRun || options.undoManifest || options.manifestOut || options.recursive || options.configPath || options.presetName || options.listPresets)) {
    throw new Error('--write-preset cannot be combined with organize or undo flags');
  }

  if (options.force && !options.writePresetName) {
    throw new Error('--force can only be used with --write-preset');
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

  if (result.bucketConfig && result.bucketConfig.presetName) {
    header.push(`preset: ${result.bucketConfig.presetName}`);
  }

  if (result.bucketConfig && result.bucketConfig.configPath) {
    header.push(`config: ${result.bucketConfig.configPath}`);
  }

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

function formatPresetListTextReport(result) {
  const lines = ['action: list-presets', `available presets: ${result.presets.length}`];
  for (const preset of result.presets) {
    lines.push(`- ${preset.name}: ${preset.description}`);
    lines.push(`  buckets: ${preset.bucketNames.join(', ')}`);
    lines.push(`  fallback bucket: ${preset.fallbackBucket}`);
    lines.push(`  extends defaults: ${preset.extendDefaults ? 'yes' : 'no'}`);
  }
  return lines.join('\n');
}

function formatWritePresetTextReport(result) {
  return [
    'action: write-preset',
    `preset: ${result.presetName}`,
    `destination: ${result.destination}`,
    `fallback bucket: ${result.fallbackBucket}`,
    `extends defaults: ${result.extendDefaults ? 'yes' : 'no'}`,
    `custom buckets: ${result.bucketNames.join(', ')}`,
  ].join('\n');
}

function formatLintConfigTextReport(result) {
  const lines = [
    'action: lint-config',
    `config: ${result.configPath}`,
    `status: ${result.valid ? 'valid' : 'invalid'}`,
    `warnings: ${result.warnings.length}`,
    `errors: ${result.errors.length}`,
  ];

  if (result.normalizedConfig) {
    lines.push(`normalized fallback bucket: ${result.normalizedConfig.fallbackBucket}`);
    lines.push(`extends defaults: ${result.normalizedConfig.extendDefaults ? 'yes' : 'no'}`);
    lines.push(`custom buckets: ${Object.keys(result.normalizedConfig.buckets).join(', ') || '(none)'}`);
  }

  result.warnings.forEach((warning, index) => {
    lines.push(`warning ${index + 1}: ${warning}`);
  });
  result.errors.forEach((error, index) => {
    lines.push(`error ${index + 1}: ${error}`);
  });

  if (result.valid) {
    lines.push('No errors found.');
  }

  return lines.join('\n');
}

function formatTextReport(result) {
  if (result.action === 'undo') {
    return formatUndoTextReport(result);
  }
  if (result.action === 'list-presets') {
    return formatPresetListTextReport(result);
  }
  if (result.action === 'write-preset') {
    return formatWritePresetTextReport(result);
  }
  if (result.action === 'lint-config') {
    return formatLintConfigTextReport(result);
  }
  return formatOrganizeTextReport(result);
}

async function main(argv = process.argv.slice(2)) {
  const { targetDir, options } = parseArgs(argv);

  if (options.help) {
    console.log('Usage: node organizer.js [directory] [--dry-run] [--recursive] [--json] [--config buckets.json] [--preset preset-name] [--manifest-out manifest.json]');
    console.log('       node organizer.js --undo manifest.json [--dry-run] [--json]');
    console.log('       node organizer.js --list-presets [--json]');
    console.log('       node organizer.js --write-preset preset-name destination.json [--force] [--json]');
    console.log('       node organizer.js --lint-config buckets.json [--json]');
    return;
  }

  let result;
  if (options.listPresets) {
    result = {
      action: 'list-presets',
      presets: listPresetCatalog(),
    };
  } else if (options.writePresetName) {
    result = await writePresetConfig(options.writePresetName, options.writePresetDestination, {
      force: options.force,
    });
  } else if (options.lintConfigPath) {
    result = await lintBucketConfig(options.lintConfigPath);
  } else if (options.undoManifest) {
    result = await undoFromManifest(options.undoManifest, { dryRun: options.dryRun });
  } else {
    const bucketConfig = options.configPath
      ? await loadBucketConfig(options.configPath)
      : options.presetName
        ? loadPresetBucketConfig(options.presetName)
        : DEFAULT_BUCKET_CONFIG;
    result = await organize(targetDir, {
      dryRun: options.dryRun,
      recursive: options.recursive,
      bucketConfig,
    });
    if (options.manifestOut) {
      result = await writeManifest(result, options.manifestOut);
    }
  }

  if (options.json) {
    console.log(JSON.stringify(result, null, 2));
  } else {
    console.log(formatTextReport(result));
  }

  if (result.action === 'lint-config' && !result.valid) {
    process.exitCode = 1;
  }
}

if (require.main === module) {
  main().catch(error => {
    console.error(error.message || error);
    process.exit(1);
  });
}

module.exports = {
  DEFAULT_BUCKET_RULES,
  DEFAULT_FALLBACK_BUCKET,
  DEFAULT_BUCKET_CONFIG,
  PRESET_LIBRARY,
  RESERVED_BUCKETS,
  normalizeBucketName,
  normalizeExtension,
  normalizeExtendDefaults,
  normalizeCustomBuckets,
  buildBucketConfig,
  cloneBucketTemplate,
  presetNames,
  getPresetDefinition,
  listPresetCatalog,
  loadPresetBucketConfig,
  writePresetConfig,
  loadBucketConfig,
  lintBucketConfig,
  describeBucketConfig,
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
