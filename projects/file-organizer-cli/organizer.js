const crypto = require('crypto');
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
const BUCKET_RULE_ALLOWED_KEYS = Object.freeze(['extensions', 'basenamePatterns', 'mimeTypes', 'mimePrefixes']);
const MIME_SNIFF_BYTE_LIMIT = 4096;
const MANIFEST_CHECKSUM_ALGORITHM = 'sha256';
const MANIFEST_SIGNATURE_PAYLOAD_ALGORITHM = 'sha256';
const MANIFEST_SIGNATURE_DEFAULT_SUFFIX = '.sig.json';
const MANIFEST_SIGNATURE_ENCODING = 'base64';
const SIGNER_POLICY_ALLOWED_KEYS = Object.freeze(['name', 'description', 'trustedSigners']);

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

function normalizeBasenamePattern(pattern, bucketName) {
  if (typeof pattern !== 'string') {
    throw new Error(`Expected every basename pattern in bucket ${bucketName} to be a string.`);
  }

  const trimmed = pattern.trim().toLowerCase();
  if (!trimmed) {
    throw new Error(`Basename patterns in bucket ${bucketName} must be non-empty.`);
  }

  if (trimmed.includes('/') || trimmed.includes('\\')) {
    throw new Error(`Basename patterns in bucket ${bucketName} must not include path separators.`);
  }

  return trimmed;
}

function normalizeExtensionList(rawExtensions, bucketName, { allowEmpty = false } = {}) {
  if (!Array.isArray(rawExtensions)) {
    throw new Error(`Bucket ${bucketName} field "extensions" must be an array when provided.`);
  }

  if (!allowEmpty && rawExtensions.length === 0) {
    throw new Error(`Bucket ${bucketName} must list at least one extension.`);
  }

  const extensions = [];
  for (const rawExtension of rawExtensions) {
    const extension = normalizeExtension(rawExtension, bucketName);
    if (!extensions.includes(extension)) {
      extensions.push(extension);
    }
  }

  return extensions;
}

function normalizeBasenamePatternList(rawPatterns, bucketName, { allowEmpty = false } = {}) {
  if (!Array.isArray(rawPatterns)) {
    throw new Error(`Bucket ${bucketName} field "basenamePatterns" must be an array when provided.`);
  }

  if (!allowEmpty && rawPatterns.length === 0) {
    throw new Error(`Bucket ${bucketName} must list at least one basename pattern.`);
  }

  const patterns = [];
  for (const rawPattern of rawPatterns) {
    const pattern = normalizeBasenamePattern(rawPattern, bucketName);
    if (!patterns.includes(pattern)) {
      patterns.push(pattern);
    }
  }

  return patterns;
}

function normalizeMimeType(mimeType, bucketName) {
  if (typeof mimeType !== 'string') {
    throw new Error(`Expected every MIME type in bucket ${bucketName} to be a string.`);
  }

  const trimmed = mimeType.trim().toLowerCase();
  if (!trimmed) {
    throw new Error(`MIME types in bucket ${bucketName} must be non-empty.`);
  }

  if (!/^[a-z0-9.+-]+\/[a-z0-9.+-]+$/.test(trimmed)) {
    throw new Error(`MIME types in bucket ${bucketName} must look like "type/subtype".`);
  }

  return trimmed;
}

function normalizeMimePrefix(mimePrefix, bucketName) {
  if (typeof mimePrefix !== 'string') {
    throw new Error(`Expected every MIME prefix in bucket ${bucketName} to be a string.`);
  }

  let normalized = mimePrefix.trim().toLowerCase();
  if (!normalized) {
    throw new Error(`MIME prefixes in bucket ${bucketName} must be non-empty.`);
  }

  if (normalized.endsWith('*')) {
    normalized = normalized.slice(0, -1);
  }

  if (!normalized.endsWith('/')) {
    throw new Error(`MIME prefixes in bucket ${bucketName} must end with "/" or "/*".`);
  }

  if (!/^[a-z0-9.+-]+\/$/.test(normalized)) {
    throw new Error(`MIME prefixes in bucket ${bucketName} must look like "type/" or "type/*".`);
  }

  return normalized;
}

function normalizeMimeTypeList(rawMimeTypes, bucketName, { allowEmpty = false } = {}) {
  if (!Array.isArray(rawMimeTypes)) {
    throw new Error(`Bucket ${bucketName} field "mimeTypes" must be an array when provided.`);
  }

  if (!allowEmpty && rawMimeTypes.length === 0) {
    throw new Error(`Bucket ${bucketName} must list at least one MIME type.`);
  }

  const mimeTypes = [];
  for (const rawMimeType of rawMimeTypes) {
    const mimeType = normalizeMimeType(rawMimeType, bucketName);
    if (!mimeTypes.includes(mimeType)) {
      mimeTypes.push(mimeType);
    }
  }

  return mimeTypes;
}

function normalizeMimePrefixList(rawMimePrefixes, bucketName, { allowEmpty = false } = {}) {
  if (!Array.isArray(rawMimePrefixes)) {
    throw new Error(`Bucket ${bucketName} field "mimePrefixes" must be an array when provided.`);
  }

  if (!allowEmpty && rawMimePrefixes.length === 0) {
    throw new Error(`Bucket ${bucketName} must list at least one MIME prefix.`);
  }

  const mimePrefixes = [];
  for (const rawMimePrefix of rawMimePrefixes) {
    const mimePrefix = normalizeMimePrefix(rawMimePrefix, bucketName);
    if (!mimePrefixes.includes(mimePrefix)) {
      mimePrefixes.push(mimePrefix);
    }
  }

  return mimePrefixes;
}

function normalizeCustomBucketRule(rawRuleDefinition, bucketName) {
  if (Array.isArray(rawRuleDefinition)) {
    return {
      extensions: normalizeExtensionList(rawRuleDefinition, bucketName),
      basenamePatterns: [],
      mimeTypes: [],
      mimePrefixes: [],
    };
  }

  if (rawRuleDefinition == null || typeof rawRuleDefinition !== 'object') {
    throw new Error(`Bucket ${bucketName} must be an extension array or an object with "extensions", "basenamePatterns", "mimeTypes", and/or "mimePrefixes".`);
  }

  const extensions = rawRuleDefinition.extensions == null
    ? []
    : normalizeExtensionList(rawRuleDefinition.extensions, bucketName, { allowEmpty: true });
  const basenamePatterns = rawRuleDefinition.basenamePatterns == null
    ? []
    : normalizeBasenamePatternList(rawRuleDefinition.basenamePatterns, bucketName, { allowEmpty: true });
  const mimeTypes = rawRuleDefinition.mimeTypes == null
    ? []
    : normalizeMimeTypeList(rawRuleDefinition.mimeTypes, bucketName, { allowEmpty: true });
  const mimePrefixes = rawRuleDefinition.mimePrefixes == null
    ? []
    : normalizeMimePrefixList(rawRuleDefinition.mimePrefixes, bucketName, { allowEmpty: true });

  if (extensions.length === 0 && basenamePatterns.length === 0 && mimeTypes.length === 0 && mimePrefixes.length === 0) {
    throw new Error(`Bucket ${bucketName} must define at least one extension, basename pattern, MIME type, or MIME prefix.`);
  }

  return {
    extensions,
    basenamePatterns,
    mimeTypes,
    mimePrefixes,
  };
}

function serializeCustomBucketRule(ruleDefinition) {
  const extensions = [...ruleDefinition.extensions];
  const basenamePatterns = [...ruleDefinition.basenamePatterns];
  const mimeTypes = [...(ruleDefinition.mimeTypes || [])];
  const mimePrefixes = [...(ruleDefinition.mimePrefixes || [])];

  if (basenamePatterns.length === 0 && mimeTypes.length === 0 && mimePrefixes.length === 0) {
    return extensions;
  }

  const serializedRule = {};
  if (extensions.length > 0) {
    serializedRule.extensions = extensions;
  }
  if (basenamePatterns.length > 0) {
    serializedRule.basenamePatterns = basenamePatterns;
  }
  if (mimeTypes.length > 0) {
    serializedRule.mimeTypes = mimeTypes;
  }
  if (mimePrefixes.length > 0) {
    serializedRule.mimePrefixes = mimePrefixes;
  }
  return serializedRule;
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

function escapeRegexCharacters(value) {
  return value.replace(/[|\\{}()[\]^$+.,]/g, '\\$&');
}

function basenamePatternToRegex(pattern) {
  return new RegExp(`^${escapeRegexCharacters(pattern).replace(/\*/g, '.*').replace(/\?/g, '.')}$`);
}

function normalizeCustomBuckets(buckets) {
  if (buckets == null) {
    return {};
  }

  if (Array.isArray(buckets) || typeof buckets !== 'object') {
    throw new Error('Bucket config field "buckets" must be a JSON object that maps bucket names to extension arrays or richer rule objects.');
  }

  const normalized = {};
  const extensionOwners = new Map();
  const basenamePatternOwners = new Map();
  const mimeTypeOwners = new Map();
  const mimePrefixOwners = new Map();
  const bucketNameOwners = new Map();

  const registerMimeType = (mimeType, bucketName) => {
    const owner = mimeTypeOwners.get(mimeType);
    if (owner && owner !== bucketName) {
      throw new Error(`MIME type ${mimeType} is assigned to multiple custom buckets (${owner}, ${bucketName}).`);
    }

    for (const [prefix, prefixOwner] of mimePrefixOwners.entries()) {
      if (prefixOwner !== bucketName && mimeType.startsWith(prefix)) {
        throw new Error(`MIME type ${mimeType} overlaps MIME prefix ${prefix} from another custom bucket (${prefixOwner}, ${bucketName}).`);
      }
    }

    mimeTypeOwners.set(mimeType, bucketName);
  };

  const registerMimePrefix = (mimePrefix, bucketName) => {
    const owner = mimePrefixOwners.get(mimePrefix);
    if (owner && owner !== bucketName) {
      throw new Error(`MIME prefix ${mimePrefix} is assigned to multiple custom buckets (${owner}, ${bucketName}).`);
    }

    for (const [existingMimeType, typeOwner] of mimeTypeOwners.entries()) {
      if (typeOwner !== bucketName && existingMimeType.startsWith(mimePrefix)) {
        throw new Error(`MIME prefix ${mimePrefix} overlaps MIME type ${existingMimeType} from another custom bucket (${typeOwner}, ${bucketName}).`);
      }
    }

    for (const [existingPrefix, prefixOwner] of mimePrefixOwners.entries()) {
      if (prefixOwner !== bucketName && (existingPrefix.startsWith(mimePrefix) || mimePrefix.startsWith(existingPrefix))) {
        throw new Error(`MIME prefix ${mimePrefix} overlaps MIME prefix ${existingPrefix} from another custom bucket (${prefixOwner}, ${bucketName}).`);
      }
    }

    mimePrefixOwners.set(mimePrefix, bucketName);
  };

  for (const [rawBucketName, rawRuleDefinition] of Object.entries(buckets)) {
    const bucketName = normalizeBucketName(rawBucketName, 'bucket name');
    const normalizedOwner = bucketNameOwners.get(bucketName);
    if (normalizedOwner && normalizedOwner !== rawBucketName) {
      throw new Error(`Bucket names normalize to the same directory name (${normalizedOwner}, ${rawBucketName} -> ${bucketName}).`);
    }
    bucketNameOwners.set(bucketName, rawBucketName);

    const ruleDefinition = normalizeCustomBucketRule(rawRuleDefinition, bucketName);

    for (const extension of ruleDefinition.extensions) {
      const owner = extensionOwners.get(extension);
      if (owner && owner !== bucketName) {
        throw new Error(`Extension ${extension} is assigned to multiple custom buckets (${owner}, ${bucketName}).`);
      }
      extensionOwners.set(extension, bucketName);
    }

    for (const pattern of ruleDefinition.basenamePatterns) {
      const owner = basenamePatternOwners.get(pattern);
      if (owner && owner !== bucketName) {
        throw new Error(`Basename pattern ${pattern} is assigned to multiple custom buckets (${owner}, ${bucketName}).`);
      }
      basenamePatternOwners.set(pattern, bucketName);
    }

    for (const mimeType of ruleDefinition.mimeTypes) {
      registerMimeType(mimeType, bucketName);
    }

    for (const mimePrefix of ruleDefinition.mimePrefixes) {
      registerMimePrefix(mimePrefix, bucketName);
    }

    normalized[bucketName] = ruleDefinition;
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
  const basenamePatternRules = [];
  const mimeTypeToBucket = new Map();
  const mimePrefixRules = [];
  const bucketNames = [];

  const registerBucketRules = (rules, { includeBasenamePatterns = false, includeMimeRules = false } = {}) => {
    for (const [bucketName, ruleDefinition] of Object.entries(rules)) {
      if (!bucketNames.includes(bucketName)) {
        bucketNames.push(bucketName);
      }

      const extensions = Array.isArray(ruleDefinition)
        ? ruleDefinition
        : ruleDefinition.extensions;
      for (const extension of extensions) {
        if (!extensionToBucket.has(extension)) {
          extensionToBucket.set(extension, bucketName);
        }
      }

      if (!Array.isArray(ruleDefinition)) {
        if (includeBasenamePatterns) {
          for (const pattern of ruleDefinition.basenamePatterns) {
            basenamePatternRules.push({
              bucketName,
              pattern,
              regex: basenamePatternToRegex(pattern),
            });
          }
        }

        if (includeMimeRules) {
          for (const mimeType of ruleDefinition.mimeTypes) {
            if (!mimeTypeToBucket.has(mimeType)) {
              mimeTypeToBucket.set(mimeType, bucketName);
            }
          }

          for (const mimePrefix of ruleDefinition.mimePrefixes) {
            mimePrefixRules.push({
              bucketName,
              prefix: mimePrefix,
            });
          }
        }
      }
    }
  };

  registerBucketRules(customBuckets, { includeBasenamePatterns: true, includeMimeRules: true });
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
    basenamePatternRules,
    mimeTypeToBucket,
    mimePrefixRules,
    requiresMimeDetection: mimeTypeToBucket.size > 0 || mimePrefixRules.length > 0,
  };
}

const DEFAULT_BUCKET_CONFIG = buildBucketConfig();
const RESERVED_BUCKETS = Object.freeze([...DEFAULT_BUCKET_CONFIG.bucketNames]);

function cloneBucketRuleDefinition(ruleDefinition) {
  if (Array.isArray(ruleDefinition)) {
    return [...ruleDefinition];
  }

  if (ruleDefinition == null || typeof ruleDefinition !== 'object') {
    return ruleDefinition;
  }

  const clone = {};
  if (ruleDefinition.extensions != null) {
    clone.extensions = [...ruleDefinition.extensions];
  }
  if (ruleDefinition.basenamePatterns != null) {
    clone.basenamePatterns = [...ruleDefinition.basenamePatterns];
  }
  if (ruleDefinition.mimeTypes != null) {
    clone.mimeTypes = [...ruleDefinition.mimeTypes];
  }
  if (ruleDefinition.mimePrefixes != null) {
    clone.mimePrefixes = [...ruleDefinition.mimePrefixes];
  }
  return clone;
}

function cloneBucketTemplate(config = {}) {
  return {
    buckets: Object.fromEntries(
      Object.entries(config.buckets || {}).map(([bucketName, ruleDefinition]) => [bucketName, cloneBucketRuleDefinition(ruleDefinition)]),
    ),
    fallbackBucket: config.fallbackBucket || DEFAULT_FALLBACK_BUCKET,
    extendDefaults: normalizeExtendDefaults(config.extendDefaults),
  };
}

function sortValues(values) {
  return [...values].sort((left, right) => left.localeCompare(right));
}

function buildNormalizedConfigPayload(config = {}) {
  const bucketConfig = buildBucketConfig(config);
  const buckets = Object.fromEntries(
    Object.entries(bucketConfig.customBuckets)
      .sort(([leftBucket], [rightBucket]) => leftBucket.localeCompare(rightBucket))
      .map(([bucketName, ruleDefinition]) => {
        const normalizedRule = {
          extensions: sortValues(ruleDefinition.extensions),
          basenamePatterns: sortValues(ruleDefinition.basenamePatterns),
          mimeTypes: sortValues(ruleDefinition.mimeTypes || []),
          mimePrefixes: sortValues(ruleDefinition.mimePrefixes || []),
        };
        return [bucketName, serializeCustomBucketRule(normalizedRule)];
      }),
  );

  return {
    buckets,
    fallbackBucket: bucketConfig.fallbackBucket,
    extendDefaults: bucketConfig.extendDefaults,
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
        errors.push('Bucket config field "buckets" must be a JSON object that maps bucket names to extension arrays or richer rule objects.');
      } else {
        const extensionOwners = new Map();
        const basenamePatternOwners = new Map();
        const mimeTypeOwners = new Map();
        const mimePrefixOwners = new Map();
        const normalizedBucketNames = new Map();

        const registerMimeType = (mimeType, bucketName) => {
          const owner = mimeTypeOwners.get(mimeType);
          if (owner && owner !== bucketName) {
            errors.push(`MIME type ${mimeType} is assigned to multiple custom buckets (${owner}, ${bucketName}).`);
            return;
          }

          for (const [prefix, prefixOwner] of mimePrefixOwners.entries()) {
            if (prefixOwner !== bucketName && mimeType.startsWith(prefix)) {
              errors.push(`MIME type ${mimeType} overlaps MIME prefix ${prefix} from another custom bucket (${prefixOwner}, ${bucketName}).`);
              return;
            }
          }

          mimeTypeOwners.set(mimeType, bucketName);
        };

        const registerMimePrefix = (mimePrefix, bucketName) => {
          const owner = mimePrefixOwners.get(mimePrefix);
          if (owner && owner !== bucketName) {
            errors.push(`MIME prefix ${mimePrefix} is assigned to multiple custom buckets (${owner}, ${bucketName}).`);
            return;
          }

          for (const [existingMimeType, typeOwner] of mimeTypeOwners.entries()) {
            if (typeOwner !== bucketName && existingMimeType.startsWith(mimePrefix)) {
              errors.push(`MIME prefix ${mimePrefix} overlaps MIME type ${existingMimeType} from another custom bucket (${typeOwner}, ${bucketName}).`);
              return;
            }
          }

          for (const [existingPrefix, prefixOwner] of mimePrefixOwners.entries()) {
            if (prefixOwner !== bucketName && (existingPrefix.startsWith(mimePrefix) || mimePrefix.startsWith(existingPrefix))) {
              errors.push(`MIME prefix ${mimePrefix} overlaps MIME prefix ${existingPrefix} from another custom bucket (${prefixOwner}, ${bucketName}).`);
              return;
            }
          }

          mimePrefixOwners.set(mimePrefix, bucketName);
        };

        for (const [rawBucketName, rawRuleDefinition] of Object.entries(parsed.buckets)) {
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

          let rawExtensions = null;
          let rawBasenamePatterns = null;
          let rawMimeTypes = null;
          let rawMimePrefixes = null;

          if (Array.isArray(rawRuleDefinition)) {
            rawExtensions = rawRuleDefinition;
          } else if (rawRuleDefinition == null || typeof rawRuleDefinition !== 'object') {
            errors.push(`Bucket ${bucketName} must be an extension array or an object with "extensions", "basenamePatterns", "mimeTypes", and/or "mimePrefixes".`);
            continue;
          } else {
            for (const key of Object.keys(rawRuleDefinition)) {
              if (!BUCKET_RULE_ALLOWED_KEYS.includes(key)) {
                warnings.push(`Bucket ${bucketName} field "${key}" will be ignored by the organizer.`);
              }
            }
            rawExtensions = rawRuleDefinition.extensions == null ? null : rawRuleDefinition.extensions;
            rawBasenamePatterns = rawRuleDefinition.basenamePatterns == null ? null : rawRuleDefinition.basenamePatterns;
            rawMimeTypes = rawRuleDefinition.mimeTypes == null ? null : rawRuleDefinition.mimeTypes;
            rawMimePrefixes = rawRuleDefinition.mimePrefixes == null ? null : rawRuleDefinition.mimePrefixes;
          }

          let extensionCount = 0;
          let basenamePatternCount = 0;
          let mimeTypeCount = 0;
          let mimePrefixCount = 0;

          if (rawExtensions != null) {
            if (!Array.isArray(rawExtensions)) {
              errors.push(`Bucket ${bucketName} field "extensions" must be an array when provided.`);
            } else {
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
                extensionCount += 1;

                const owner = extensionOwners.get(normalizedExtension);
                if (owner && owner !== bucketName) {
                  errors.push(`Extension ${normalizedExtension} is assigned to multiple custom buckets (${owner}, ${bucketName}).`);
                } else {
                  extensionOwners.set(normalizedExtension, bucketName);
                }
              }
            }
          }

          if (rawBasenamePatterns != null) {
            if (!Array.isArray(rawBasenamePatterns)) {
              errors.push(`Bucket ${bucketName} field "basenamePatterns" must be an array when provided.`);
            } else {
              const bucketPatterns = new Set();
              for (const rawPattern of rawBasenamePatterns) {
                let normalizedPattern;
                try {
                  normalizedPattern = normalizeBasenamePattern(rawPattern, bucketName);
                  if (typeof rawPattern === 'string' && rawPattern !== normalizedPattern) {
                    warnings.push(`Bucket ${bucketName} basename pattern "${rawPattern}" will normalize to "${normalizedPattern}".`);
                  }
                } catch (error) {
                  errors.push(error.message);
                  continue;
                }

                if (bucketPatterns.has(normalizedPattern)) {
                  warnings.push(`Bucket ${bucketName} repeats basename pattern "${normalizedPattern}"; duplicate entries are ignored.`);
                  continue;
                }
                bucketPatterns.add(normalizedPattern);
                basenamePatternCount += 1;

                const owner = basenamePatternOwners.get(normalizedPattern);
                if (owner && owner !== bucketName) {
                  errors.push(`Basename pattern ${normalizedPattern} is assigned to multiple custom buckets (${owner}, ${bucketName}).`);
                } else {
                  basenamePatternOwners.set(normalizedPattern, bucketName);
                }
              }
            }
          }

          if (rawMimeTypes != null) {
            if (!Array.isArray(rawMimeTypes)) {
              errors.push(`Bucket ${bucketName} field "mimeTypes" must be an array when provided.`);
            } else {
              const bucketMimeTypes = new Set();
              for (const rawMimeType of rawMimeTypes) {
                let normalizedMimeType;
                try {
                  normalizedMimeType = normalizeMimeType(rawMimeType, bucketName);
                  if (typeof rawMimeType === 'string' && rawMimeType !== normalizedMimeType) {
                    warnings.push(`Bucket ${bucketName} MIME type "${rawMimeType}" will normalize to "${normalizedMimeType}".`);
                  }
                } catch (error) {
                  errors.push(error.message);
                  continue;
                }

                if (bucketMimeTypes.has(normalizedMimeType)) {
                  warnings.push(`Bucket ${bucketName} repeats MIME type "${normalizedMimeType}"; duplicate entries are ignored.`);
                  continue;
                }
                bucketMimeTypes.add(normalizedMimeType);
                mimeTypeCount += 1;
                registerMimeType(normalizedMimeType, bucketName);
              }
            }
          }

          if (rawMimePrefixes != null) {
            if (!Array.isArray(rawMimePrefixes)) {
              errors.push(`Bucket ${bucketName} field "mimePrefixes" must be an array when provided.`);
            } else {
              const bucketMimePrefixes = new Set();
              for (const rawMimePrefix of rawMimePrefixes) {
                let normalizedMimePrefix;
                try {
                  normalizedMimePrefix = normalizeMimePrefix(rawMimePrefix, bucketName);
                  if (typeof rawMimePrefix === 'string' && rawMimePrefix !== normalizedMimePrefix) {
                    warnings.push(`Bucket ${bucketName} MIME prefix "${rawMimePrefix}" will normalize to "${normalizedMimePrefix}".`);
                  }
                } catch (error) {
                  errors.push(error.message);
                  continue;
                }

                if (bucketMimePrefixes.has(normalizedMimePrefix)) {
                  warnings.push(`Bucket ${bucketName} repeats MIME prefix "${normalizedMimePrefix}"; duplicate entries are ignored.`);
                  continue;
                }
                bucketMimePrefixes.add(normalizedMimePrefix);
                mimePrefixCount += 1;
                registerMimePrefix(normalizedMimePrefix, bucketName);
              }
            }
          }

          if (extensionCount === 0 && basenamePatternCount === 0 && mimeTypeCount === 0 && mimePrefixCount === 0) {
            errors.push(`Bucket ${bucketName} must define at least one extension, basename pattern, MIME type, or MIME prefix.`);
          }
        }
      }
    }
  }

  let normalizedConfig = null;
  if (errors.length === 0) {
    const builtConfig = buildBucketConfig(parsed);
    normalizedConfig = {
      ...buildNormalizedConfigPayload(parsed),
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

function pushUniqueChange(changes, message) {
  if (!changes.includes(message)) {
    changes.push(message);
  }
}

function buildNormalizationPreviewChanges(parsed, normalizedConfig) {
  const changes = [];

  for (const key of Object.keys(parsed)) {
    if (!CONFIG_ALLOWED_KEYS.includes(key)) {
      pushUniqueChange(changes, `Remove unknown top-level key "${key}".`);
    }
  }

  if (parsed.buckets == null) {
    pushUniqueChange(changes, 'Add an explicit empty "buckets" object for the canonical shared-config format.');
  }

  if (parsed.fallbackBucket == null) {
    pushUniqueChange(changes, `Add default fallback bucket "${normalizedConfig.fallbackBucket}".`);
  } else if (parsed.fallbackBucket !== normalizedConfig.fallbackBucket) {
    pushUniqueChange(changes, `Normalize fallback bucket "${parsed.fallbackBucket}" -> "${normalizedConfig.fallbackBucket}".`);
  }

  if (parsed.extendDefaults == null) {
    pushUniqueChange(changes, `Add default extendDefaults=${normalizedConfig.extendDefaults}.`);
  }

  if (parsed.buckets && !Array.isArray(parsed.buckets) && typeof parsed.buckets === 'object') {
    const rawBucketOrder = [];

    for (const [rawBucketName, rawRuleDefinition] of Object.entries(parsed.buckets)) {
      const bucketName = normalizeBucketName(rawBucketName, 'bucket name');
      rawBucketOrder.push(bucketName);
      if (rawBucketName !== bucketName) {
        pushUniqueChange(changes, `Normalize bucket name "${rawBucketName}" -> "${bucketName}".`);
      }

      const canonicalRule = normalizedConfig.buckets[bucketName];
      const canonicalExtensions = Array.isArray(canonicalRule)
        ? canonicalRule
        : (canonicalRule?.extensions || []);
      const canonicalBasenamePatterns = Array.isArray(canonicalRule)
        ? []
        : (canonicalRule?.basenamePatterns || []);
      const canonicalMimeTypes = Array.isArray(canonicalRule)
        ? []
        : (canonicalRule?.mimeTypes || []);
      const canonicalMimePrefixes = Array.isArray(canonicalRule)
        ? []
        : (canonicalRule?.mimePrefixes || []);

      if (Array.isArray(rawRuleDefinition)) {
        const encounteredExtensions = [];
        const seenExtensions = new Set();
        for (const rawExtension of rawRuleDefinition) {
          const normalizedExtension = normalizeExtension(rawExtension, bucketName);
          if (rawExtension !== normalizedExtension) {
            pushUniqueChange(changes, `Normalize extension for bucket ${bucketName}: "${rawExtension}" -> "${normalizedExtension}".`);
          }
          if (seenExtensions.has(normalizedExtension)) {
            pushUniqueChange(changes, `Remove duplicate extension "${normalizedExtension}" from bucket ${bucketName}.`);
            continue;
          }
          seenExtensions.add(normalizedExtension);
          encounteredExtensions.push(normalizedExtension);
        }

        if (JSON.stringify(encounteredExtensions) !== JSON.stringify(canonicalExtensions)) {
          pushUniqueChange(changes, `Sort extensions for bucket ${bucketName} into canonical order.`);
        }
        continue;
      }

      if (rawRuleDefinition == null || typeof rawRuleDefinition !== 'object') {
        continue;
      }

      for (const key of Object.keys(rawRuleDefinition)) {
        if (!BUCKET_RULE_ALLOWED_KEYS.includes(key)) {
          pushUniqueChange(changes, `Remove ignored field "${key}" from bucket ${bucketName}.`);
        }
      }

      const collectNormalized = ({ rawValues, normalizeValue, normalizeMessage, duplicateLabel, canonicalValues, sortMessage }) => {
        const encounteredValues = [];
        if (Array.isArray(rawValues)) {
          const seenValues = new Set();
          for (const rawValue of rawValues) {
            const normalizedValue = normalizeValue(rawValue, bucketName);
            if (rawValue !== normalizedValue) {
              pushUniqueChange(changes, `${normalizeMessage} for bucket ${bucketName}: "${rawValue}" -> "${normalizedValue}".`);
            }
            if (seenValues.has(normalizedValue)) {
              pushUniqueChange(changes, `Remove duplicate ${duplicateLabel} "${normalizedValue}" from bucket ${bucketName}.`);
              continue;
            }
            seenValues.add(normalizedValue);
            encounteredValues.push(normalizedValue);
          }
        }

        if (JSON.stringify(encounteredValues) !== JSON.stringify(canonicalValues)) {
          pushUniqueChange(changes, sortMessage);
        }
      };

      collectNormalized({
        rawValues: rawRuleDefinition.extensions,
        normalizeValue: normalizeExtension,
        normalizeMessage: 'Normalize extension',
        duplicateLabel: 'extension',
        canonicalValues: canonicalExtensions,
        sortMessage: `Sort extensions for bucket ${bucketName} into canonical order.`,
      });
      collectNormalized({
        rawValues: rawRuleDefinition.basenamePatterns,
        normalizeValue: normalizeBasenamePattern,
        normalizeMessage: 'Normalize basename pattern',
        duplicateLabel: 'basename pattern',
        canonicalValues: canonicalBasenamePatterns,
        sortMessage: `Sort basename patterns for bucket ${bucketName} into canonical order.`,
      });
      collectNormalized({
        rawValues: rawRuleDefinition.mimeTypes,
        normalizeValue: normalizeMimeType,
        normalizeMessage: 'Normalize MIME type',
        duplicateLabel: 'MIME type',
        canonicalValues: canonicalMimeTypes,
        sortMessage: `Sort MIME types for bucket ${bucketName} into canonical order.`,
      });
      collectNormalized({
        rawValues: rawRuleDefinition.mimePrefixes,
        normalizeValue: normalizeMimePrefix,
        normalizeMessage: 'Normalize MIME prefix',
        duplicateLabel: 'MIME prefix',
        canonicalValues: canonicalMimePrefixes,
        sortMessage: `Sort MIME prefixes for bucket ${bucketName} into canonical order.`,
      });

      if (Array.isArray(canonicalRule)) {
        pushUniqueChange(changes, `Rewrite bucket ${bucketName} into extension-array shorthand.`);
      }
    }

    if (JSON.stringify(rawBucketOrder) !== JSON.stringify(Object.keys(normalizedConfig.buckets))) {
      pushUniqueChange(changes, 'Sort custom bucket names into canonical order.');
    }
  }

  if (JSON.stringify(parsed) !== JSON.stringify(normalizedConfig) && changes.length === 0) {
    pushUniqueChange(changes, 'Rewrite the config into canonical JSON ordering.');
  }

  return changes;
}

async function previewNormalizedBucketConfig(configPath) {
  const resolvedPath = path.resolve(configPath);
  let raw;

  try {
    raw = await fs.readFile(resolvedPath, 'utf8');
  } catch (error) {
    if (error && error.code === 'ENOENT') {
      return {
        action: 'preview-normalized-config',
        configPath: resolvedPath,
        valid: false,
        errors: [`Bucket config file not found: ${resolvedPath}`],
        warnings: [],
        changes: [],
        rewriteNeeded: false,
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
      action: 'preview-normalized-config',
      configPath: resolvedPath,
      valid: false,
      errors: [`Bucket config file must contain valid JSON: ${resolvedPath}`],
      warnings: [],
      changes: [],
      rewriteNeeded: false,
      normalizedConfig: null,
    };
  }

  const lintResult = await lintBucketConfig(resolvedPath);
  if (!lintResult.valid) {
    return {
      action: 'preview-normalized-config',
      configPath: resolvedPath,
      valid: false,
      errors: lintResult.errors,
      warnings: lintResult.warnings,
      changes: [],
      rewriteNeeded: false,
      normalizedConfig: null,
    };
  }

  const normalizedConfig = buildNormalizedConfigPayload(lintResult.normalizedConfig);
  const changes = buildNormalizationPreviewChanges(parsed, normalizedConfig);

  return {
    action: 'preview-normalized-config',
    configPath: resolvedPath,
    valid: true,
    errors: [],
    warnings: lintResult.warnings,
    changes,
    rewriteNeeded: JSON.stringify(parsed) !== JSON.stringify(normalizedConfig),
    normalizedConfig,
  };
}

async function writeNormalizedBucketConfig(configPath, destinationPath, options = {}) {
  const settings = {
    force: false,
    ...options,
  };
  const lintResult = await lintBucketConfig(configPath);
  if (!lintResult.valid) {
    throw new Error(`Cannot normalize invalid config ${lintResult.configPath}: ${lintResult.errors.join(' ')}`);
  }

  const resolvedDestination = path.resolve(destinationPath);
  const inPlace = resolvedDestination === lintResult.configPath;
  if (!inPlace && !settings.force && await pathExists(resolvedDestination)) {
    throw new Error(`Normalized config destination already exists: ${resolvedDestination}`);
  }

  const normalizedConfig = buildNormalizedConfigPayload(lintResult.normalizedConfig);
  await fs.mkdir(path.dirname(resolvedDestination), { recursive: true });
  await fs.writeFile(resolvedDestination, `${JSON.stringify(normalizedConfig, null, 2)}\n`);

  return {
    action: 'write-normalized-config',
    configPath: lintResult.configPath,
    destination: resolvedDestination,
    inPlace,
    resolvedWarnings: lintResult.warnings,
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
    customBuckets: Object.fromEntries(
      Object.entries(bucketConfig.customBuckets).map(([bucketName, ruleDefinition]) => [bucketName, serializeCustomBucketRule(ruleDefinition)]),
    ),
  };
}

function bucketFor(filename, bucketConfig = DEFAULT_BUCKET_CONFIG) {
  const basename = path.basename(filename, path.extname(filename)).toLowerCase();
  const patternMatch = bucketConfig.basenamePatternRules.find(ruleDefinition => ruleDefinition.regex.test(basename));
  if (patternMatch) {
    return patternMatch.bucketName;
  }

  const ext = path.extname(filename).toLowerCase();
  return bucketConfig.extensionToBucket.get(ext) || bucketConfig.fallbackBucket;
}

function mimeMatchFor(mimeType, bucketConfig = DEFAULT_BUCKET_CONFIG) {
  if (!mimeType) {
    return null;
  }

  const normalizedMimeType = mimeType.trim().toLowerCase();
  const exactBucket = bucketConfig.mimeTypeToBucket.get(normalizedMimeType);
  if (exactBucket) {
    return {
      bucket: exactBucket,
      matchedBy: 'mimeType',
      matchedValue: normalizedMimeType,
    };
  }

  const prefixMatch = bucketConfig.mimePrefixRules.find(ruleDefinition => normalizedMimeType.startsWith(ruleDefinition.prefix));
  if (prefixMatch) {
    return {
      bucket: prefixMatch.bucketName,
      matchedBy: 'mimePrefix',
      matchedValue: prefixMatch.prefix,
    };
  }

  return null;
}

function detectMimeTypeFromText(text) {
  const trimmed = text.trimStart();
  if (!trimmed) {
    return 'text/plain';
  }

  if (/^<!doctype html[\s>]/i.test(trimmed) || /^<html[\s>]/i.test(trimmed)) {
    return 'text/html';
  }

  if (/^<svg[\s>]/i.test(trimmed) || (/^<\?xml[\s\S]*$/i.test(trimmed) && /<svg[\s>]/i.test(trimmed))) {
    return 'image/svg+xml';
  }

  if (/^<\?xml[\s>]/i.test(trimmed) || /^<[a-z_:][\w:.-]*(\s|>)/i.test(trimmed)) {
    return 'application/xml';
  }

  const firstCharacter = trimmed[0];
  if (firstCharacter === '{' || firstCharacter === '[') {
    try {
      JSON.parse(trimmed);
      return 'application/json';
    } catch {
      // fall through to plain text
    }
  }

  return 'text/plain';
}

function detectMimeTypeFromBuffer(buffer, extension = '') {
  if (!buffer || buffer.length === 0) {
    return null;
  }

  if (buffer.length >= 8 && buffer[0] === 0x89 && buffer[1] === 0x50 && buffer[2] === 0x4e && buffer[3] === 0x47 && buffer[4] === 0x0d && buffer[5] === 0x0a && buffer[6] === 0x1a && buffer[7] === 0x0a) {
    return 'image/png';
  }

  if (buffer.length >= 3 && buffer[0] === 0xff && buffer[1] === 0xd8 && buffer[2] === 0xff) {
    return 'image/jpeg';
  }

  if (buffer.length >= 6) {
    const signature6 = buffer.subarray(0, 6).toString('ascii');
    if (signature6 === 'GIF87a' || signature6 === 'GIF89a') {
      return 'image/gif';
    }
  }

  if (buffer.length >= 12 && buffer.subarray(0, 4).toString('ascii') == 'RIFF' && buffer.subarray(8, 12).toString('ascii') === 'WEBP') {
    return 'image/webp';
  }

  if (buffer.length >= 5 && buffer.subarray(0, 5).toString('ascii') === '%PDF-') {
    return 'application/pdf';
  }

  if (buffer.length >= 4 && buffer[0] === 0x50 && buffer[1] === 0x4b && buffer[2] === 0x03 && buffer[3] === 0x04) {
    if (extension === '.docx') {
      return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
    }
    if (extension === '.pptx') {
      return 'application/vnd.openxmlformats-officedocument.presentationml.presentation';
    }
    if (extension === '.xlsx') {
      return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
    }
    return 'application/zip';
  }

  if (buffer.length >= 2 && buffer[0] === 0x1f && buffer[1] === 0x8b) {
    return 'application/gzip';
  }

  if (buffer.length >= 6 && buffer.subarray(0, 6).toString('hex') === '377abcaf271c') {
    return 'application/x-7z-compressed';
  }

  if (buffer.length >= 7 && buffer.subarray(0, 7).toString('ascii') === 'Rar!') {
    return 'application/vnd.rar';
  }

  if (buffer.length >= 4 && buffer.subarray(0, 4).toString('ascii') === 'fLaC') {
    return 'audio/flac';
  }

  if (buffer.length >= 4 && buffer.subarray(0, 4).toString('ascii') === 'OggS') {
    return 'audio/ogg';
  }

  if (buffer.length >= 12 && buffer.subarray(0, 4).toString('ascii') === 'RIFF' && buffer.subarray(8, 12).toString('ascii') === 'WAVE') {
    return 'audio/wav';
  }

  if ((buffer.length >= 3 && buffer.subarray(0, 3).toString('ascii') === 'ID3') || (buffer.length >= 2 && buffer[0] === 0xff && (buffer[1] & 0xe0) === 0xe0)) {
    return 'audio/mpeg';
  }

  if (buffer.length >= 12 && buffer.subarray(4, 8).toString('ascii') === 'ftyp') {
    const brand = buffer.subarray(8, 12).toString('ascii');
    if (brand === 'M4A ' || brand === 'M4B ' || brand === 'isom' || brand === 'mp42' || brand === 'mp41') {
      return 'audio/mp4';
    }
  }

  if (buffer.includes(0x00)) {
    return 'application/octet-stream';
  }

  try {
    const decoded = new TextDecoder('utf-8', { fatal: true }).decode(buffer);
    return detectMimeTypeFromText(decoded);
  } catch {
    return 'application/octet-stream';
  }
}

async function detectMimeType(filePath) {
  const handle = await fs.open(filePath, 'r');
  try {
    const buffer = Buffer.alloc(MIME_SNIFF_BYTE_LIMIT);
    const { bytesRead } = await handle.read(buffer, 0, MIME_SNIFF_BYTE_LIMIT, 0);
    return detectMimeTypeFromBuffer(buffer.subarray(0, bytesRead), path.extname(filePath).toLowerCase());
  } finally {
    await handle.close();
  }
}

async function classifyFile(filePath, bucketConfig = DEFAULT_BUCKET_CONFIG) {
  const filename = path.basename(filePath);
  const basename = path.basename(filename, path.extname(filename)).toLowerCase();
  const patternMatch = bucketConfig.basenamePatternRules.find(ruleDefinition => ruleDefinition.regex.test(basename));
  if (patternMatch) {
    return {
      bucket: patternMatch.bucketName,
      matchedBy: 'basenamePattern',
      matchedValue: patternMatch.pattern,
      detectedMimeType: null,
    };
  }

  let detectedMimeType = null;
  if (bucketConfig.requiresMimeDetection) {
    detectedMimeType = await detectMimeType(filePath);
    const mimeMatch = mimeMatchFor(detectedMimeType, bucketConfig);
    if (mimeMatch) {
      return {
        bucket: mimeMatch.bucket,
        matchedBy: mimeMatch.matchedBy,
        matchedValue: mimeMatch.matchedValue,
        detectedMimeType,
      };
    }
  }

  const ext = path.extname(filename).toLowerCase();
  const extensionBucket = bucketConfig.extensionToBucket.get(ext);
  if (extensionBucket) {
    return {
      bucket: extensionBucket,
      matchedBy: 'extension',
      matchedValue: ext,
      detectedMimeType,
    };
  }

  return {
    bucket: bucketConfig.fallbackBucket,
    matchedBy: 'fallback',
    matchedValue: bucketConfig.fallbackBucket,
    detectedMimeType,
  };
}

async function pathExists(targetPath) {
  try {
    await fs.access(targetPath);
    return true;
  } catch {
    return false;
  }
}

function sortObjectKeysDeep(value) {
  if (Array.isArray(value)) {
    return value.map(item => sortObjectKeysDeep(item));
  }

  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.keys(value)
        .sort((left, right) => left.localeCompare(right))
        .map(key => [key, sortObjectKeysDeep(value[key])]),
    );
  }

  return value;
}

function canonicalizeJsonPayload(value) {
  return JSON.stringify(sortObjectKeysDeep(value));
}

function manifestPayloadForIntegrity(manifest) {
  const { integrity, ...manifestWithoutIntegrity } = manifest;
  return manifestWithoutIntegrity;
}

function manifestChecksumFor(manifest, algorithm = MANIFEST_CHECKSUM_ALGORITHM) {
  const hash = crypto.createHash(algorithm);
  hash.update(canonicalizeJsonPayload(manifestPayloadForIntegrity(manifest)));
  return hash.digest('hex');
}

function buildManifestIntegrity(manifest, algorithm = MANIFEST_CHECKSUM_ALGORITHM) {
  return {
    algorithm,
    checksum: manifestChecksumFor(manifest, algorithm),
  };
}

function verifyManifestIntegrity(manifest) {
  if (!manifest.integrity) {
    return {
      present: false,
      valid: true,
      algorithm: null,
      checksum: null,
      expectedChecksum: null,
      reason: null,
    };
  }

  const { algorithm, checksum } = manifest.integrity;
  if (typeof algorithm !== 'string' || !algorithm) {
    return {
      present: true,
      valid: false,
      algorithm: null,
      checksum: checksum || null,
      expectedChecksum: null,
      reason: 'Manifest integrity metadata is missing an algorithm.',
    };
  }

  if (typeof checksum !== 'string' || !checksum) {
    return {
      present: true,
      valid: false,
      algorithm,
      checksum: checksum || null,
      expectedChecksum: null,
      reason: 'Manifest integrity metadata is missing a checksum.',
    };
  }

  let expectedChecksum;
  try {
    expectedChecksum = manifestChecksumFor(manifest, algorithm);
  } catch (error) {
    return {
      present: true,
      valid: false,
      algorithm,
      checksum,
      expectedChecksum: null,
      reason: error.message || String(error),
    };
  }

  return {
    present: true,
    valid: checksum === expectedChecksum,
    algorithm,
    checksum,
    expectedChecksum,
    reason: checksum === expectedChecksum
      ? null
      : `Manifest checksum mismatch: expected ${expectedChecksum} but found ${checksum}.`,
  };
}

function manifestSignaturePayload(manifest) {
  return Buffer.from(canonicalizeJsonPayload(manifest));
}

function manifestSignatureChecksumFor(manifest, algorithm = MANIFEST_SIGNATURE_PAYLOAD_ALGORITHM) {
  const hash = crypto.createHash(algorithm);
  hash.update(manifestSignaturePayload(manifest));
  return hash.digest('hex');
}

function defaultManifestSignaturePath(manifestPath) {
  return `${path.resolve(manifestPath)}${MANIFEST_SIGNATURE_DEFAULT_SUFFIX}`;
}

async function loadPrivateKey(privateKeyPath) {
  const resolvedPrivateKeyPath = path.resolve(privateKeyPath);
  return {
    keyPath: resolvedPrivateKeyPath,
    keyObject: crypto.createPrivateKey(await fs.readFile(resolvedPrivateKeyPath, 'utf8')),
  };
}

async function loadPublicKey(publicKeyPath) {
  const resolvedPublicKeyPath = path.resolve(publicKeyPath);
  return {
    keyPath: resolvedPublicKeyPath,
    keyObject: crypto.createPublicKey(await fs.readFile(resolvedPublicKeyPath, 'utf8')),
  };
}

function manifestSignatureAlgorithmForKey(keyObject) {
  const keyType = keyObject.asymmetricKeyType;
  if (keyType === 'ed25519' || keyType === 'ed448') {
    return {
      keyType,
      digest: null,
    };
  }

  if (keyType === 'rsa' || keyType === 'ec') {
    return {
      keyType,
      digest: 'sha256',
    };
  }

  throw new Error(`Unsupported manifest signing key type: ${keyType || 'unknown'}. Use an Ed25519, Ed448, RSA, or EC PEM key.`);
}

function publicKeyFingerprint(keyObject, algorithm = 'sha256') {
  const digest = crypto.createHash(algorithm);
  digest.update(keyObject.export({ type: 'spki', format: 'der' }));
  return `${algorithm}:${digest.digest('hex')}`;
}

function normalizeSignerFingerprint(fingerprint, label = 'signer fingerprint') {
  if (typeof fingerprint !== 'string') {
    throw new Error(`Expected ${label} to be a string.`);
  }

  const trimmed = fingerprint.trim().toLowerCase();
  if (!trimmed) {
    throw new Error(`Expected ${label} to be non-empty.`);
  }

  if (/^[a-f0-9]{64}$/.test(trimmed)) {
    return `sha256:${trimmed}`;
  }

  if (/^[a-z0-9.+-]+:[a-f0-9]+$/.test(trimmed)) {
    return trimmed;
  }

  throw new Error(`Expected ${label} to look like "sha256:<hex>".`);
}

function normalizeOptionalSignerMetadata(value, label) {
  if (value == null) {
    return null;
  }

  if (typeof value !== 'string') {
    throw new Error(`Expected ${label} to be a string when provided.`);
  }

  const trimmed = value.trim();
  return trimmed || null;
}

function normalizeOptionalSignerRoles(rawRoles, label) {
  if (rawRoles == null) {
    return [];
  }

  if (!Array.isArray(rawRoles)) {
    throw new Error(`Expected ${label} to be an array when provided.`);
  }

  const roles = [];
  for (const rawRole of rawRoles) {
    const role = normalizeOptionalSignerMetadata(rawRole, `${label} entry`);
    if (role && !roles.includes(role)) {
      roles.push(role);
    }
  }

  return roles;
}

function normalizeTrustedSignerEntry(rawTrustedSigner, index) {
  if (typeof rawTrustedSigner === 'string') {
    return {
      fingerprint: normalizeSignerFingerprint(rawTrustedSigner, `trustedSigners[${index}]`),
      label: null,
      roles: [],
      notes: null,
    };
  }

  if (!rawTrustedSigner || typeof rawTrustedSigner !== 'object' || Array.isArray(rawTrustedSigner)) {
    throw new Error(`trustedSigners[${index}] must be a fingerprint string or an object with a fingerprint field.`);
  }

  return {
    fingerprint: normalizeSignerFingerprint(rawTrustedSigner.fingerprint, `trustedSigners[${index}].fingerprint`),
    label: normalizeOptionalSignerMetadata(rawTrustedSigner.label, `trustedSigners[${index}].label`),
    roles: normalizeOptionalSignerRoles(rawTrustedSigner.roles, `trustedSigners[${index}].roles`),
    notes: normalizeOptionalSignerMetadata(rawTrustedSigner.notes, `trustedSigners[${index}].notes`),
  };
}

async function loadSignerPolicy(policyPath) {
  const resolvedPolicyPath = path.resolve(policyPath);
  const rawPolicy = JSON.parse(await fs.readFile(resolvedPolicyPath, 'utf8'));

  if (!rawPolicy || typeof rawPolicy !== 'object' || Array.isArray(rawPolicy)) {
    throw new Error('Signer policy must be a JSON object.');
  }

  const unknownKeys = Object.keys(rawPolicy).filter(key => !SIGNER_POLICY_ALLOWED_KEYS.includes(key));
  if (unknownKeys.length > 0) {
    throw new Error(`Signer policy contains unsupported top-level keys: ${unknownKeys.join(', ')}.`);
  }

  if (!Array.isArray(rawPolicy.trustedSigners) || rawPolicy.trustedSigners.length === 0) {
    throw new Error('Signer policy must define a non-empty trustedSigners array.');
  }

  const trustedSigners = rawPolicy.trustedSigners.map((entry, index) => normalizeTrustedSignerEntry(entry, index));
  const seenFingerprints = new Set();
  for (const signer of trustedSigners) {
    if (seenFingerprints.has(signer.fingerprint)) {
      throw new Error(`Signer policy lists fingerprint ${signer.fingerprint} more than once.`);
    }
    seenFingerprints.add(signer.fingerprint);
  }

  return {
    policyPath: resolvedPolicyPath,
    name: normalizeOptionalSignerMetadata(rawPolicy.name, 'signer policy name'),
    description: normalizeOptionalSignerMetadata(rawPolicy.description, 'signer policy description'),
    trustedSigners,
  };
}

function trustedSignerEntryFor(policy, fingerprint) {
  if (!policy) {
    return null;
  }

  const normalizedFingerprint = normalizeSignerFingerprint(fingerprint);
  return policy.trustedSigners.find(entry => entry.fingerprint === normalizedFingerprint) || null;
}

function signerPolicySummary(policy, trustedSigner = null) {
  if (!policy) {
    return null;
  }

  const summary = {
    policyPath: policy.policyPath,
    trustedSignerCount: policy.trustedSigners.length,
  };

  if (policy.name) {
    summary.name = policy.name;
  }

  if (policy.description) {
    summary.description = policy.description;
  }

  if (trustedSigner) {
    summary.matchedFingerprint = trustedSigner.fingerprint;
    if (trustedSigner.label) {
      summary.matchedLabel = trustedSigner.label;
    }
    if (trustedSigner.roles.length > 0) {
      summary.matchedRoles = [...trustedSigner.roles];
    }
  }

  return summary;
}

async function writeDetachedManifestSignature(manifestPath, privateKeyPath, options = {}) {
  const settings = {
    signaturePath: null,
    signerPolicyPath: null,
    ...options,
  };
  const resolvedManifestPath = path.resolve(manifestPath);
  const resolvedSignaturePath = path.resolve(settings.signaturePath || defaultManifestSignaturePath(resolvedManifestPath));
  const manifest = JSON.parse(await fs.readFile(resolvedManifestPath, 'utf8'));
  const integrity = verifyManifestIntegrity(manifest);
  if (!integrity.present) {
    throw new Error('Detached manifest signatures require checksum-backed integrity metadata. Write the manifest with includeChecksum or --manifest-checksum first.');
  }
  if (!integrity.valid) {
    throw new Error(`Cannot sign a manifest with invalid integrity metadata: ${integrity.reason}`);
  }
  const { keyObject: privateKey } = await loadPrivateKey(privateKeyPath);
  const publicKey = crypto.createPublicKey(privateKey);
  const signatureAlgorithm = manifestSignatureAlgorithmForKey(privateKey);
  const signerFingerprint = publicKeyFingerprint(publicKey);
  const signerPolicy = settings.signerPolicyPath ? await loadSignerPolicy(settings.signerPolicyPath) : null;
  const trustedSigner = signerPolicy ? trustedSignerEntryFor(signerPolicy, signerFingerprint) : null;
  if (signerPolicy && !trustedSigner) {
    throw new Error(`Signer fingerprint ${signerFingerprint} is not trusted by signer policy ${signerPolicy.policyPath}.`);
  }
  const signature = crypto.sign(
    signatureAlgorithm.digest,
    manifestSignaturePayload(manifest),
    privateKey,
  ).toString(MANIFEST_SIGNATURE_ENCODING);

  const signatureRecord = {
    action: 'manifest-signature',
    createdAt: new Date().toISOString(),
    manifestPath: resolvedManifestPath,
    signaturePath: resolvedSignaturePath,
    signedPayload: {
      kind: 'canonical-manifest-json',
      checksumAlgorithm: MANIFEST_SIGNATURE_PAYLOAD_ALGORITHM,
      checksum: manifestSignatureChecksumFor(manifest),
      includesIntegritySection: Boolean(manifest.integrity),
    },
    signer: {
      keyType: signatureAlgorithm.keyType,
      publicKeyFingerprint: signerFingerprint,
      label: trustedSigner?.label || null,
      roles: trustedSigner ? [...trustedSigner.roles] : [],
      notes: trustedSigner?.notes || null,
    },
    signature: {
      encoding: MANIFEST_SIGNATURE_ENCODING,
      value: signature,
    },
    signerPolicy: signerPolicySummary(signerPolicy, trustedSigner),
  };

  await fs.mkdir(path.dirname(resolvedSignaturePath), { recursive: true });
  await fs.writeFile(resolvedSignaturePath, `${JSON.stringify(signatureRecord, null, 2)}\n`);
  return signatureRecord;
}

async function verifyDetachedManifestSignature(manifestPath, publicKeyPath, options = {}) {
  const settings = {
    signaturePath: null,
    signerPolicyPath: null,
    ...options,
  };
  const resolvedManifestPath = path.resolve(manifestPath);
  const resolvedSignaturePath = path.resolve(settings.signaturePath || defaultManifestSignaturePath(resolvedManifestPath));
  const resolvedPublicKeyPath = path.resolve(publicKeyPath);

  let manifest;
  try {
    manifest = JSON.parse(await fs.readFile(resolvedManifestPath, 'utf8'));
  } catch (error) {
    if (error && error.code === 'ENOENT') {
      return {
        action: 'verify-manifest-signature',
        manifestPath: resolvedManifestPath,
        signaturePath: resolvedSignaturePath,
        publicKeyPath: resolvedPublicKeyPath,
        valid: false,
        keyType: null,
        publicKeyFingerprint: null,
        reason: `Manifest file not found: ${resolvedManifestPath}`,
      };
    }
    throw error;
  }

  let signatureRecord;
  try {
    signatureRecord = JSON.parse(await fs.readFile(resolvedSignaturePath, 'utf8'));
  } catch (error) {
    if (error && error.code === 'ENOENT') {
      return {
        action: 'verify-manifest-signature',
        manifestPath: resolvedManifestPath,
        signaturePath: resolvedSignaturePath,
        publicKeyPath: resolvedPublicKeyPath,
        valid: false,
        keyType: null,
        publicKeyFingerprint: null,
        reason: `Manifest signature file not found: ${resolvedSignaturePath}`,
      };
    }
    throw error;
  }

  const { keyObject: publicKey } = await loadPublicKey(resolvedPublicKeyPath);
  const signatureAlgorithm = manifestSignatureAlgorithmForKey(publicKey);
  const computedFingerprint = publicKeyFingerprint(publicKey);
  const expectedChecksum = manifestSignatureChecksumFor(manifest);
  const signerPolicy = settings.signerPolicyPath ? await loadSignerPolicy(settings.signerPolicyPath) : null;
  const trustedSigner = signerPolicy ? trustedSignerEntryFor(signerPolicy, computedFingerprint) : null;

  if (signatureRecord.manifestPath && path.resolve(signatureRecord.manifestPath) !== resolvedManifestPath) {
    return {
      action: 'verify-manifest-signature',
      manifestPath: resolvedManifestPath,
      signaturePath: resolvedSignaturePath,
      publicKeyPath: resolvedPublicKeyPath,
      valid: false,
      keyType: signatureAlgorithm.keyType,
      publicKeyFingerprint: computedFingerprint,
      reason: `Manifest signature references ${signatureRecord.manifestPath}, expected ${resolvedManifestPath}.`,
    };
  }

  if (!signatureRecord.signature || typeof signatureRecord.signature.value !== 'string' || !signatureRecord.signature.value) {
    return {
      action: 'verify-manifest-signature',
      manifestPath: resolvedManifestPath,
      signaturePath: resolvedSignaturePath,
      publicKeyPath: resolvedPublicKeyPath,
      valid: false,
      keyType: signatureAlgorithm.keyType,
      publicKeyFingerprint: computedFingerprint,
      reason: 'Manifest signature metadata is missing a signature value.',
    };
  }

  if (signatureRecord.signer?.publicKeyFingerprint && signatureRecord.signer.publicKeyFingerprint !== computedFingerprint) {
    return {
      action: 'verify-manifest-signature',
      manifestPath: resolvedManifestPath,
      signaturePath: resolvedSignaturePath,
      publicKeyPath: resolvedPublicKeyPath,
      valid: false,
      keyType: signatureAlgorithm.keyType,
      publicKeyFingerprint: computedFingerprint,
      reason: `Public key fingerprint mismatch: expected ${signatureRecord.signer.publicKeyFingerprint} but found ${computedFingerprint}.`,
    };
  }

  if (signatureRecord.signedPayload?.checksum && signatureRecord.signedPayload.checksum !== expectedChecksum) {
    return {
      action: 'verify-manifest-signature',
      manifestPath: resolvedManifestPath,
      signaturePath: resolvedSignaturePath,
      publicKeyPath: resolvedPublicKeyPath,
      valid: false,
      keyType: signatureAlgorithm.keyType,
      publicKeyFingerprint: computedFingerprint,
      signerPolicy: signerPolicySummary(signerPolicy, trustedSigner),
      reason: `Manifest payload checksum mismatch: expected ${expectedChecksum} but found ${signatureRecord.signedPayload.checksum}.`,
    };
  }

  if (signerPolicy && !trustedSigner) {
    return {
      action: 'verify-manifest-signature',
      manifestPath: resolvedManifestPath,
      signaturePath: resolvedSignaturePath,
      publicKeyPath: resolvedPublicKeyPath,
      valid: false,
      keyType: signatureAlgorithm.keyType,
      publicKeyFingerprint: computedFingerprint,
      signerPolicy: signerPolicySummary(signerPolicy),
      reason: `Signer fingerprint ${computedFingerprint} is not trusted by signer policy ${signerPolicy.policyPath}.`,
    };
  }

  if (signerPolicy && signatureRecord.signerPolicy?.name && signerPolicy.name && signatureRecord.signerPolicy.name !== signerPolicy.name) {
    return {
      action: 'verify-manifest-signature',
      manifestPath: resolvedManifestPath,
      signaturePath: resolvedSignaturePath,
      publicKeyPath: resolvedPublicKeyPath,
      valid: false,
      keyType: signatureAlgorithm.keyType,
      publicKeyFingerprint: computedFingerprint,
      signerPolicy: signerPolicySummary(signerPolicy, trustedSigner),
      reason: `Manifest signature policy mismatch: signature references ${signatureRecord.signerPolicy.name} but signer policy is ${signerPolicy.name}.`,
    };
  }

  let signatureBuffer;
  try {
    signatureBuffer = Buffer.from(signatureRecord.signature.value, signatureRecord.signature.encoding || MANIFEST_SIGNATURE_ENCODING);
  } catch (error) {
    return {
      action: 'verify-manifest-signature',
      manifestPath: resolvedManifestPath,
      signaturePath: resolvedSignaturePath,
      publicKeyPath: resolvedPublicKeyPath,
      valid: false,
      keyType: signatureAlgorithm.keyType,
      publicKeyFingerprint: computedFingerprint,
      signerPolicy: signerPolicySummary(signerPolicy, trustedSigner),
      reason: error.message || String(error),
    };
  }

  const valid = crypto.verify(
    signatureAlgorithm.digest,
    manifestSignaturePayload(manifest),
    publicKey,
    signatureBuffer,
  );

  return {
    action: 'verify-manifest-signature',
    manifestPath: resolvedManifestPath,
    signaturePath: resolvedSignaturePath,
    publicKeyPath: resolvedPublicKeyPath,
    valid,
    keyType: signatureAlgorithm.keyType,
    publicKeyFingerprint: computedFingerprint,
    signerLabel: signatureRecord.signer?.label || null,
    signerRoles: Array.isArray(signatureRecord.signer?.roles) ? [...signatureRecord.signer.roles] : [],
    signedPayload: {
      checksumAlgorithm: MANIFEST_SIGNATURE_PAYLOAD_ALGORITHM,
      checksum: expectedChecksum,
    },
    signerPolicy: signerPolicySummary(signerPolicy, trustedSigner),
    reason: valid ? null : 'Manifest signature verification failed.',
  };
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

function collectProtectedPathsForOrganize(options = {}) {
  return [
    options.configPath,
    options.manifestOut,
    options.signaturePath,
    options.signManifestKeyPath,
    options.signerPolicyPath,
  ].filter(Boolean);
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
    const classification = await classifyFile(sourcePath, settings.bucketConfig);
    const targetDir = path.join(sourceDirectory, classification.bucket);
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
      bucket: classification.bucket,
      renamed,
      dryRun: settings.dryRun,
      matchedBy: classification.matchedBy,
      matchedValue: classification.matchedValue,
      detectedMimeType: classification.detectedMimeType,
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

async function writeManifest(result, manifestPath, options = {}) {
  const settings = {
    includeChecksum: false,
    ...options,
  };
  const resolvedPath = path.resolve(manifestPath);
  const manifest = {
    ...result,
    manifestPath: resolvedPath,
  };

  if (settings.includeChecksum) {
    manifest.integrity = buildManifestIntegrity(manifest);
  }

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
    verifyIntegrity: true,
    verifySignatureKeyPath: null,
    signaturePath: null,
    signerPolicyPath: null,
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

  const integrity = verifyManifestIntegrity(manifest);
  if (settings.verifyIntegrity && integrity.present && !integrity.valid) {
    throw new Error(`Undo manifest failed integrity verification: ${integrity.reason}`);
  }

  let signatureVerification = null;
  if (settings.verifySignatureKeyPath) {
    signatureVerification = await verifyDetachedManifestSignature(resolvedManifestPath, settings.verifySignatureKeyPath, {
      signaturePath: settings.signaturePath,
      signerPolicyPath: settings.signerPolicyPath,
    });
    if (!signatureVerification.valid) {
      throw new Error(`Undo manifest failed signature verification: ${signatureVerification.reason}`);
    }
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
    integrity,
    signatureVerification,
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
    manifestChecksum: false,
    signManifestKeyPath: null,
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
    } else if (arg === '--manifest-checksum') {
      options.manifestChecksum = true;
    } else if (arg === '--sign-manifest') {
      const nextArg = args[index + 1];
      if (!nextArg || nextArg.startsWith('-')) {
        throw new Error('Expected a private-key path after --sign-manifest');
      }
      options.signManifestKeyPath = nextArg;
      index += 1;
    } else if (arg === '--verify-manifest-signature') {
      const nextArg = args[index + 1];
      if (!nextArg || nextArg.startsWith('-')) {
        throw new Error('Expected a public-key path after --verify-manifest-signature');
      }
      options.verifyManifestSignatureKeyPath = nextArg;
      index += 1;
    } else if (arg === '--signature-path') {
      const nextArg = args[index + 1];
      if (!nextArg || nextArg.startsWith('-')) {
        throw new Error('Expected a path after --signature-path');
      }
      options.signaturePath = nextArg;
      index += 1;
    } else if (arg === '--signer-policy') {
      const nextArg = args[index + 1];
      if (!nextArg || nextArg.startsWith('-')) {
        throw new Error('Expected a path after --signer-policy');
      }
      options.signerPolicyPath = nextArg;
      index += 1;
    } else if (arg === '--skip-manifest-verification') {
      options.skipManifestVerification = true;
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
    } else if (arg === '--preview-normalized-config') {
      const nextArg = args[index + 1];
      if (!nextArg || nextArg.startsWith('-')) {
        throw new Error('Expected a path after --preview-normalized-config');
      }
      options.previewConfigPath = nextArg;
      index += 1;
    } else if (arg === '--fix-config') {
      const nextArg = args[index + 1];
      if (!nextArg || nextArg.startsWith('-')) {
        throw new Error('Expected a path after --fix-config');
      }
      options.fixConfigPath = nextArg;
      index += 1;
    } else if (arg === '--write-normalized-config') {
      const sourcePath = args[index + 1];
      const destinationPath = args[index + 2];
      if (!sourcePath || sourcePath.startsWith('-')) {
        throw new Error('Expected a source path after --write-normalized-config');
      }
      if (!destinationPath || destinationPath.startsWith('-')) {
        throw new Error('Expected a destination path after --write-normalized-config <source>');
      }
      options.writeNormalizedConfigSource = sourcePath;
      options.writeNormalizedConfigDestination = destinationPath;
      index += 2;
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

  if (options.undoManifest && options.manifestChecksum) {
    throw new Error('--manifest-checksum cannot be used with --undo');
  }

  if (options.undoManifest && options.signManifestKeyPath) {
    throw new Error('--sign-manifest cannot be used with --undo');
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

  if (options.manifestChecksum && !options.manifestOut) {
    throw new Error('--manifest-checksum requires --manifest-out');
  }

  if (options.signManifestKeyPath && !options.manifestOut) {
    throw new Error('--sign-manifest requires --manifest-out');
  }

  if (options.signManifestKeyPath && !options.manifestChecksum) {
    throw new Error('--sign-manifest requires --manifest-checksum');
  }

  if (options.verifyManifestSignatureKeyPath && !options.undoManifest) {
    throw new Error('--verify-manifest-signature can only be used with --undo');
  }

  if (options.signaturePath && !options.signManifestKeyPath && !options.verifyManifestSignatureKeyPath) {
    throw new Error('--signature-path requires --sign-manifest or --verify-manifest-signature');
  }

  if (options.signerPolicyPath && !options.signManifestKeyPath && !options.verifyManifestSignatureKeyPath) {
    throw new Error('--signer-policy requires --sign-manifest or --verify-manifest-signature');
  }

  if (options.skipManifestVerification && !options.undoManifest) {
    throw new Error('--skip-manifest-verification can only be used with --undo');
  }

  if (options.lintConfigPath && targetDirExplicit) {
    throw new Error('Target directory cannot be combined with --lint-config');
  }

  if (options.lintConfigPath && (options.dryRun || options.undoManifest || options.manifestOut || options.manifestChecksum || options.signManifestKeyPath || options.verifyManifestSignatureKeyPath || options.signaturePath || options.signerPolicyPath || options.skipManifestVerification || options.recursive || options.configPath || options.previewConfigPath || options.fixConfigPath || options.writeNormalizedConfigSource || options.presetName || options.listPresets || options.writePresetName || options.force)) {
    throw new Error('--lint-config cannot be combined with organize, undo, preset, or normalized-config-write flags');
  }

  if (options.previewConfigPath && targetDirExplicit) {
    throw new Error('Target directory cannot be combined with --preview-normalized-config');
  }

  if (options.previewConfigPath && (options.dryRun || options.undoManifest || options.manifestOut || options.manifestChecksum || options.signManifestKeyPath || options.verifyManifestSignatureKeyPath || options.signaturePath || options.signerPolicyPath || options.skipManifestVerification || options.recursive || options.configPath || options.lintConfigPath || options.fixConfigPath || options.writeNormalizedConfigSource || options.presetName || options.listPresets || options.writePresetName || options.force)) {
    throw new Error('--preview-normalized-config cannot be combined with organize, undo, lint, preset, or normalized-config-write flags');
  }

  if (options.fixConfigPath && targetDirExplicit) {
    throw new Error('Target directory cannot be combined with --fix-config');
  }

  if (options.fixConfigPath && (options.dryRun || options.undoManifest || options.manifestOut || options.manifestChecksum || options.signManifestKeyPath || options.verifyManifestSignatureKeyPath || options.signaturePath || options.signerPolicyPath || options.skipManifestVerification || options.recursive || options.configPath || options.lintConfigPath || options.previewConfigPath || options.writeNormalizedConfigSource || options.presetName || options.listPresets || options.writePresetName || options.force)) {
    throw new Error('--fix-config cannot be combined with organize, undo, lint, preset, or normalized-config-export flags');
  }

  if (options.writeNormalizedConfigSource && targetDirExplicit) {
    throw new Error('Target directory cannot be combined with --write-normalized-config');
  }

  if (options.writeNormalizedConfigSource && (options.dryRun || options.undoManifest || options.manifestOut || options.manifestChecksum || options.signManifestKeyPath || options.verifyManifestSignatureKeyPath || options.signaturePath || options.signerPolicyPath || options.skipManifestVerification || options.recursive || options.configPath || options.lintConfigPath || options.previewConfigPath || options.fixConfigPath || options.presetName || options.listPresets || options.writePresetName)) {
    throw new Error('--write-normalized-config cannot be combined with organize, undo, lint, or preset flags');
  }

  if (options.listPresets && targetDirExplicit) {
    throw new Error('Target directory cannot be combined with --list-presets');
  }

  if (options.listPresets && (options.dryRun || options.undoManifest || options.manifestOut || options.manifestChecksum || options.signManifestKeyPath || options.verifyManifestSignatureKeyPath || options.signaturePath || options.signerPolicyPath || options.skipManifestVerification || options.recursive || options.configPath || options.lintConfigPath || options.previewConfigPath || options.fixConfigPath || options.writeNormalizedConfigSource || options.presetName || options.writePresetName || options.force)) {
    throw new Error('--list-presets only supports optional --json output');
  }

  if (options.writePresetName && targetDirExplicit) {
    throw new Error('Target directory cannot be combined with --write-preset');
  }

  if (options.writePresetName && (options.dryRun || options.undoManifest || options.manifestOut || options.manifestChecksum || options.signManifestKeyPath || options.verifyManifestSignatureKeyPath || options.signaturePath || options.signerPolicyPath || options.skipManifestVerification || options.recursive || options.configPath || options.lintConfigPath || options.previewConfigPath || options.fixConfigPath || options.writeNormalizedConfigSource || options.presetName || options.listPresets)) {
    throw new Error('--write-preset cannot be combined with organize, lint, normalized-config, or undo flags');
  }

  if (options.force && !options.writePresetName && !options.writeNormalizedConfigSource) {
    throw new Error('--force can only be used with --write-preset or --write-normalized-config');
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

  if (result.integrity && result.integrity.checksum) {
    header.push(`manifest checksum: ${result.integrity.algorithm}:${result.integrity.checksum}`);
  }

  if (result.bucketConfig && result.bucketConfig.presetName) {
    header.push(`preset: ${result.bucketConfig.presetName}`);
  }

  if (result.bucketConfig && result.bucketConfig.configPath) {
    header.push(`config: ${result.bucketConfig.configPath}`);
  }

  if (result.manifestPath) {
    header.push(`manifest: ${result.manifestPath}`);
  }

  if (result.detachedSignature && result.detachedSignature.signaturePath) {
    header.push(`manifest signature: ${result.detachedSignature.signaturePath}`);
    if (result.detachedSignature.signer?.publicKeyFingerprint) {
      header.push(`manifest signer fingerprint: ${result.detachedSignature.signer.publicKeyFingerprint}`);
    }
    if (result.detachedSignature.signer?.label) {
      header.push(`manifest signer label: ${result.detachedSignature.signer.label}`);
    }
    if (Array.isArray(result.detachedSignature.signer?.roles) && result.detachedSignature.signer.roles.length > 0) {
      header.push(`manifest signer roles: ${result.detachedSignature.signer.roles.join(', ')}`);
    }
    if (result.detachedSignature.signerPolicy) {
      header.push(`signer policy: ${result.detachedSignature.signerPolicy.name || result.detachedSignature.signerPolicy.policyPath}`);
    }
  }

  const bucketLines = Object.entries(result.summary.byBucket)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([bucket, count]) => `bucket ${bucket}: ${count}`);

  const moveLines = result.moves.map(move => {
    const annotations = [];
    if (move.renamed) {
      annotations.push('renamed');
    }
    if (move.matchedBy === 'basenamePattern') {
      annotations.push(`basename pattern ${move.matchedValue}`);
    }
    if (move.matchedBy === 'mimeType') {
      annotations.push(`MIME type ${move.matchedValue}`);
    }
    if (move.matchedBy === 'mimePrefix') {
      annotations.push(`MIME prefix ${move.matchedValue}`);
    }
    if ((move.matchedBy === 'mimeType' || move.matchedBy === 'mimePrefix') && move.detectedMimeType) {
      annotations.push(`detected ${move.detectedMimeType}`);
    }
    const suffix = annotations.length > 0 ? ` [${annotations.join('; ')}]` : '';
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

  if (result.integrity && result.integrity.present) {
    header.push(`manifest checksum verified: ${result.integrity.valid ? 'yes' : 'no'}`);
    if (result.integrity.algorithm && result.integrity.checksum) {
      header.push(`manifest checksum: ${result.integrity.algorithm}:${result.integrity.checksum}`);
    }
  }

  if (result.signatureVerification) {
    header.push(`manifest signature verified: ${result.signatureVerification.valid ? 'yes' : 'no'}`);
    header.push(`manifest signature file: ${result.signatureVerification.signaturePath}`);
    if (result.signatureVerification.publicKeyFingerprint) {
      header.push(`manifest signer fingerprint: ${result.signatureVerification.publicKeyFingerprint}`);
    }
    if (result.signatureVerification.signerLabel) {
      header.push(`manifest signer label: ${result.signatureVerification.signerLabel}`);
    }
    if (Array.isArray(result.signatureVerification.signerRoles) && result.signatureVerification.signerRoles.length > 0) {
      header.push(`manifest signer roles: ${result.signatureVerification.signerRoles.join(', ')}`);
    }
    if (result.signatureVerification.signerPolicy) {
      header.push(`signer policy: ${result.signatureVerification.signerPolicy.name || result.signatureVerification.signerPolicy.policyPath}`);
    }
  }

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

function formatPreviewNormalizedConfigTextReport(result) {
  const lines = [
    'action: preview-normalized-config',
    `config: ${result.configPath}`,
    `status: ${result.valid ? 'valid' : 'invalid'}`,
    `rewrite needed: ${result.rewriteNeeded ? 'yes' : 'no'}`,
    `changes: ${result.changes.length}`,
    `warnings: ${result.warnings.length}`,
    `errors: ${result.errors.length}`,
  ];

  if (result.normalizedConfig) {
    lines.push(`normalized fallback bucket: ${result.normalizedConfig.fallbackBucket}`);
    lines.push(`extends defaults: ${result.normalizedConfig.extendDefaults ? 'yes' : 'no'}`);
    lines.push(`custom buckets: ${Object.keys(result.normalizedConfig.buckets).join(', ') || '(none)'}`);
  }

  result.changes.forEach((change, index) => {
    lines.push(`change ${index + 1}: ${change}`);
  });
  result.warnings.forEach((warning, index) => {
    lines.push(`warning ${index + 1}: ${warning}`);
  });
  result.errors.forEach((error, index) => {
    lines.push(`error ${index + 1}: ${error}`);
  });

  if (result.valid) {
    lines.push(result.rewriteNeeded
      ? 'Preview only. Use --fix-config or --write-normalized-config to apply these changes.'
      : 'Config is already canonical.');
  }

  return lines.join('\n');
}

function formatWriteNormalizedConfigTextReport(result) {
  const lines = [
    'action: write-normalized-config',
    `config: ${result.configPath}`,
    `destination: ${result.destination}`,
    `mode: ${result.inPlace ? 'in-place' : 'copy'}`,
    `resolved warnings: ${result.resolvedWarnings.length}`,
    `fallback bucket: ${result.normalizedConfig.fallbackBucket}`,
    `extends defaults: ${result.normalizedConfig.extendDefaults ? 'yes' : 'no'}`,
    `custom buckets: ${Object.keys(result.normalizedConfig.buckets).join(', ') || '(none)'}`,
  ];

  result.resolvedWarnings.forEach((warning, index) => {
    lines.push(`resolved warning ${index + 1}: ${warning}`);
  });
  lines.push('Normalized config written.');
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
  if (result.action === 'preview-normalized-config') {
    return formatPreviewNormalizedConfigTextReport(result);
  }
  if (result.action === 'write-normalized-config') {
    return formatWriteNormalizedConfigTextReport(result);
  }
  return formatOrganizeTextReport(result);
}

async function main(argv = process.argv.slice(2)) {
  const { targetDir, options } = parseArgs(argv);

  if (options.help) {
    console.log('Usage: node organizer.js [directory] [--dry-run] [--recursive] [--json] [--config buckets.json] [--preset preset-name] [--manifest-out manifest.json] [--manifest-checksum] [--sign-manifest private-key.pem] [--signature-path manifest.sig.json] [--signer-policy signer-policy.json]');
    console.log('       node organizer.js --undo manifest.json [--dry-run] [--json] [--skip-manifest-verification] [--verify-manifest-signature public-key.pem] [--signature-path manifest.sig.json] [--signer-policy signer-policy.json]');
    console.log('       node organizer.js --list-presets [--json]');
    console.log('       node organizer.js --write-preset preset-name destination.json [--force] [--json]');
    console.log('       node organizer.js --lint-config buckets.json [--json]');
    console.log('       node organizer.js --preview-normalized-config buckets.json [--json]');
    console.log('       node organizer.js --fix-config buckets.json [--json]');
    console.log('       node organizer.js --write-normalized-config source.json destination.json [--force] [--json]');
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
  } else if (options.writeNormalizedConfigSource) {
    result = await writeNormalizedBucketConfig(
      options.writeNormalizedConfigSource,
      options.writeNormalizedConfigDestination,
      { force: options.force },
    );
  } else if (options.previewConfigPath) {
    result = await previewNormalizedBucketConfig(options.previewConfigPath);
  } else if (options.fixConfigPath) {
    result = await writeNormalizedBucketConfig(options.fixConfigPath, options.fixConfigPath);
  } else if (options.lintConfigPath) {
    result = await lintBucketConfig(options.lintConfigPath);
  } else if (options.undoManifest) {
    result = await undoFromManifest(options.undoManifest, {
      dryRun: options.dryRun,
      verifyIntegrity: !options.skipManifestVerification,
      verifySignatureKeyPath: options.verifyManifestSignatureKeyPath,
      signaturePath: options.signaturePath,
      signerPolicyPath: options.signerPolicyPath,
    });
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
      skipPaths: collectProtectedPathsForOrganize(options),
    });
    if (options.manifestOut) {
      result = await writeManifest(result, options.manifestOut, {
        includeChecksum: options.manifestChecksum,
      });
      if (options.signManifestKeyPath) {
        result.detachedSignature = await writeDetachedManifestSignature(result.manifestPath, options.signManifestKeyPath, {
          signaturePath: options.signaturePath,
          signerPolicyPath: options.signerPolicyPath,
        });
      }
    }
  }

  if (options.json) {
    console.log(JSON.stringify(result, null, 2));
  } else {
    console.log(formatTextReport(result));
  }

  if ((result.action === 'lint-config' || result.action === 'preview-normalized-config') && !result.valid) {
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
  buildNormalizedConfigPayload,
  presetNames,
  getPresetDefinition,
  listPresetCatalog,
  loadPresetBucketConfig,
  writePresetConfig,
  loadBucketConfig,
  lintBucketConfig,
  previewNormalizedBucketConfig,
  writeNormalizedBucketConfig,
  describeBucketConfig,
  bucketFor,
  mimeMatchFor,
  detectMimeTypeFromText,
  detectMimeTypeFromBuffer,
  detectMimeType,
  classifyFile,
  pathExists,
  uniqueDestination,
  moveFile,
  organize,
  collectProtectedPathsForOrganize,
  writeManifest,
  manifestChecksumFor,
  buildManifestIntegrity,
  verifyManifestIntegrity,
  manifestSignatureChecksumFor,
  publicKeyFingerprint,
  normalizeSignerFingerprint,
  loadSignerPolicy,
  trustedSignerEntryFor,
  writeDetachedManifestSignature,
  verifyDetachedManifestSignature,
  undoFromManifest,
  parseArgs,
  formatTextReport,
  removeEmptyDirectories,
};
