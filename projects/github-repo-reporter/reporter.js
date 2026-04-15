const fs = require('fs/promises');
const https = require('https');
const path = require('path');

const DEFAULT_USER_AGENT = 'cs-portfolio-projects';
const DEFAULT_API_VERSION = '2022-11-28';

function buildListReposUrl(subject, options = {}) {
  const params = new URLSearchParams({
    per_page: String(options.perPage || 100),
    sort: options.sort || 'updated',
    direction: options.direction || 'desc',
    page: String(options.page || 1)
  });

  if (options.type) {
    params.set('type', options.type);
  }

  const basePath = options.subjectType === 'org'
    ? `/orgs/${encodeURIComponent(subject)}/repos`
    : `/users/${encodeURIComponent(subject)}/repos`;

  return `https://api.github.com${basePath}?${params.toString()}`;
}

function buildReposUrl(username, options = {}) {
  return buildListReposUrl(username, { ...options, subjectType: 'user' });
}

function buildOrgReposUrl(org, options = {}) {
  return buildListReposUrl(org, { ...options, subjectType: 'org' });
}

function parseLinkHeader(headerValue = '') {
  return headerValue.split(',').reduce((acc, entry) => {
    const trimmed = entry.trim();
    if (!trimmed) return acc;
    const match = trimmed.match(/<([^>]+)>;\s*rel="([^"]+)"/);
    if (match) {
      acc[match[2]] = match[1];
    }
    return acc;
  }, {});
}

function buildRequestHeaders(options = {}) {
  const headers = {
    'User-Agent': DEFAULT_USER_AGENT,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': DEFAULT_API_VERSION,
    ...(options.headers || {})
  };

  if (options.tokenEnv) {
    const token = process.env[options.tokenEnv];
    if (!token || !token.trim()) {
      throw new Error(`Environment variable ${options.tokenEnv} is required when using --token-env`);
    }
    headers.Authorization = `Bearer ${token.trim()}`;
  }

  return headers;
}

function requestJson(url, headers = {}) {
  return new Promise((resolve, reject) => {
    const request = https.get(url, { headers }, res => {
      let data = '';
      res.on('data', chunk => {
        data += chunk;
      });
      res.on('end', () => {
        const statusCode = res.statusCode || 0;
        if (statusCode < 200 || statusCode >= 300) {
          const message = data ? safeErrorMessage(data) : `HTTP ${statusCode}`;
          return reject(new Error(message));
        }

        try {
          resolve({
            body: JSON.parse(data),
            headers: res.headers,
            statusCode
          });
        } catch (error) {
          reject(new Error(`Failed to parse GitHub response JSON: ${error.message}`));
        }
      });
    });

    request.on('error', reject);
  });
}

function safeErrorMessage(body) {
  try {
    const parsed = JSON.parse(body);
    if (parsed && parsed.message) {
      return parsed.message;
    }
  } catch (_) {
    // fall through
  }
  return body;
}

async function fetchRepos(subject, options = {}) {
  const repos = [];
  const subjectType = options.subjectType === 'org' ? 'org' : 'user';
  const requestHeaders = buildRequestHeaders(options);
  let nextUrl = subjectType === 'org'
    ? buildOrgReposUrl(subject, options)
    : buildReposUrl(subject, options);

  while (nextUrl) {
    const { body, headers } = await requestJson(nextUrl, requestHeaders);
    repos.push(...body.map(normalizeRepo));
    const links = parseLinkHeader(headers.link);
    nextUrl = links.next || null;
  }

  return applyRepoFilters(repos, options);
}

function normalizeRepo(repo) {
  return {
    name: repo.name,
    fullName: repo.full_name,
    description: repo.description,
    url: repo.html_url,
    stars: repo.stargazers_count,
    forks: repo.forks_count,
    watchers: repo.watchers_count,
    openIssues: repo.open_issues_count,
    language: repo.language,
    topics: Array.isArray(repo.topics) ? [...new Set(repo.topics.filter(Boolean))] : [],
    isFork: repo.fork,
    archived: repo.archived,
    updatedAt: repo.updated_at,
    pushedAt: repo.pushed_at,
    sizeKb: repo.size
  };
}

function parseDateInput(value, flagName = 'date') {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    throw new Error(`${flagName} must be a valid ISO-8601 date or datetime`);
  }
  return parsed;
}

function applyRepoFilters(repos, options = {}) {
  const pushedSince = options.pushedSince ? parseDateInput(options.pushedSince, '--pushed-since') : null;

  return repos.filter(repo => {
    if (!options.includeForks && repo.isFork) return false;
    if (!options.includeArchived && repo.archived) return false;
    if (options.language && (repo.language || '').toLowerCase() !== options.language.toLowerCase()) return false;
    if (pushedSince) {
      if (!repo.pushedAt) return false;
      if (new Date(repo.pushedAt) < pushedSince) return false;
    }
    return true;
  });
}

function countBy(items, getKeys) {
  return items.reduce((acc, item) => {
    const keys = getKeys(item);
    for (const key of keys) {
      acc[key] = (acc[key] || 0) + 1;
    }
    return acc;
  }, {});
}

function sortObjectCounts(counts) {
  return Object.fromEntries(
    Object.entries(counts).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
  );
}

function summarize(repos, options = {}) {
  const topN = Number.isInteger(options.topN) && options.topN > 0 ? options.topN : 5;
  const safeRepos = Array.isArray(repos) ? repos : [];
  const totalStars = safeRepos.reduce((sum, repo) => sum + repo.stars, 0);
  const totalForks = safeRepos.reduce((sum, repo) => sum + repo.forks, 0);
  const totalWatchers = safeRepos.reduce((sum, repo) => sum + repo.watchers, 0);
  const totalOpenIssues = safeRepos.reduce((sum, repo) => sum + repo.openIssues, 0);
  const totalSizeKb = safeRepos.reduce((sum, repo) => sum + repo.sizeKb, 0);

  const languageCounts = sortObjectCounts(countBy(safeRepos, repo => [repo.language || 'Unknown']));
  const topicCounts = sortObjectCounts(countBy(safeRepos, repo => repo.topics));

  const mostRecentPush = safeRepos
    .filter(repo => repo.pushedAt)
    .sort((a, b) => new Date(b.pushedAt) - new Date(a.pushedAt))[0] || null;

  const topStarred = [...safeRepos].sort((a, b) => b.stars - a.stars || a.name.localeCompare(b.name)).slice(0, topN);
  const recentlyUpdated = [...safeRepos].sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt)).slice(0, topN);
  const topTopics = Object.entries(topicCounts)
    .slice(0, topN)
    .map(([topic, count]) => ({ topic, count }));

  return {
    count: safeRepos.length,
    totalStars,
    averageStars: safeRepos.length ? Number((totalStars / safeRepos.length).toFixed(2)) : 0,
    totalForks,
    averageForks: safeRepos.length ? Number((totalForks / safeRepos.length).toFixed(2)) : 0,
    totalWatchers,
    totalOpenIssues,
    totalSizeKb,
    totalSizeMb: Number((totalSizeKb / 1024).toFixed(2)),
    topStarred,
    recentlyUpdated,
    languages: languageCounts,
    topics: topicCounts,
    topTopics,
    forkCount: safeRepos.filter(repo => repo.isFork).length,
    archivedCount: safeRepos.filter(repo => repo.archived).length,
    mostRecentPush
  };
}

function formatSummary(summary, options = {}) {
  const format = options.format || 'json';
  if (format === 'markdown') return formatMarkdownSummary(summary);
  if (format === 'text') return formatTextSummary(summary);
  return JSON.stringify(summary, null, 2);
}

function formatTextSummary(summary) {
  const lines = [
    `Repositories: ${summary.count}`,
    `Total stars: ${summary.totalStars}`,
    `Average stars/repo: ${summary.averageStars}`,
    `Total forks across result set: ${summary.totalForks}`,
    `Average forks/repo: ${summary.averageForks}`,
    `Total watchers across result set: ${summary.totalWatchers}`,
    `Total open issues across result set: ${summary.totalOpenIssues}`,
    `Estimated code size: ${summary.totalSizeMb} MB (${summary.totalSizeKb} KB)`,
    `Fork repos included: ${summary.forkCount}`,
    `Archived repos included: ${summary.archivedCount}`,
    'Languages:'
  ];

  for (const [language, count] of Object.entries(summary.languages)) {
    lines.push(`- ${language}: ${count}`);
  }

  lines.push('Top topics:');
  if (summary.topTopics.length) {
    for (const topic of summary.topTopics) {
      lines.push(`- ${topic.topic}: ${topic.count}`);
    }
  } else {
    lines.push('- none');
  }

  lines.push('Top starred:');
  for (const repo of summary.topStarred) {
    lines.push(`- ${repo.fullName}: ${repo.stars}★ (${repo.language || 'Unknown'})`);
  }

  if (summary.mostRecentPush) {
    lines.push(`Most recent push: ${summary.mostRecentPush.fullName} at ${summary.mostRecentPush.pushedAt}`);
  }

  return lines.join('\n');
}

function formatMarkdownSummary(summary) {
  const languageRows = Object.entries(summary.languages)
    .map(([language, count]) => `| ${language} | ${count} |`)
    .join('\n') || '| None | 0 |';

  const topicRows = summary.topTopics
    .map(topic => `| ${topic.topic} | ${topic.count} |`)
    .join('\n') || '| None | 0 |';

  const topRows = summary.topStarred
    .map(repo => `| [${repo.fullName}](${repo.url}) | ${repo.stars} | ${repo.language || 'Unknown'} | ${repo.updatedAt} |`)
    .join('\n') || '| None | 0 | Unknown | n/a |';

  return [
    '# GitHub Repository Report',
    '',
    `- Repositories: **${summary.count}**`,
    `- Total stars: **${summary.totalStars}**`,
    `- Average stars per repo: **${summary.averageStars}**`,
    `- Total forks across result set: **${summary.totalForks}**`,
    `- Average forks per repo: **${summary.averageForks}**`,
    `- Total watchers across result set: **${summary.totalWatchers}**`,
    `- Total open issues across result set: **${summary.totalOpenIssues}**`,
    `- Estimated code size: **${summary.totalSizeMb} MB** (${summary.totalSizeKb} KB)`,
    `- Fork repos included in result set: **${summary.forkCount}**`,
    `- Archived repos included in result set: **${summary.archivedCount}**`,
    summary.mostRecentPush
      ? `- Most recent push: **${summary.mostRecentPush.fullName}** at ${summary.mostRecentPush.pushedAt}`
      : '- Most recent push: n/a',
    '',
    '## Languages',
    '',
    '| Language | Repositories |',
    '| --- | ---: |',
    languageRows,
    '',
    '## Top Topics',
    '',
    '| Topic | Repositories |',
    '| --- | ---: |',
    topicRows,
    '',
    '## Top Starred',
    '',
    '| Repository | Stars | Language | Updated |',
    '| --- | ---: | --- | --- |',
    topRows
  ].join('\n');
}

async function writeOutputIfRequested(output, outPath) {
  if (!outPath) {
    return;
  }

  const resolved = path.resolve(outPath);
  await fs.mkdir(path.dirname(resolved), { recursive: true });
  await fs.writeFile(resolved, output, 'utf8');
}

function requireArgValue(args, index, flag) {
  const value = args[index + 1];
  if (!value || value.startsWith('--')) {
    throw new Error(`${flag} requires a value`);
  }
  return value;
}

function parseArgs(argv) {
  const args = argv.slice(2);
  const options = {
    format: 'json',
    includeForks: false,
    includeArchived: false,
    topN: 5,
    perPage: 100,
    sort: 'updated',
    direction: 'desc',
    subjectType: 'user',
    outPath: null,
    pushedSince: null,
    tokenEnv: null
  };

  let subject = null;

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (!arg.startsWith('--') && !subject) {
      subject = arg;
      continue;
    }

    if (arg === '--include-forks') {
      options.includeForks = true;
    } else if (arg === '--include-archived') {
      options.includeArchived = true;
    } else if (arg === '--org') {
      options.subjectType = 'org';
    } else if (arg === '--format') {
      options.format = requireArgValue(args, index, '--format');
      index += 1;
    } else if (arg === '--language') {
      options.language = requireArgValue(args, index, '--language');
      index += 1;
    } else if (arg === '--top') {
      options.topN = Number.parseInt(requireArgValue(args, index, '--top'), 10);
      index += 1;
    } else if (arg === '--sort') {
      options.sort = requireArgValue(args, index, '--sort');
      index += 1;
    } else if (arg === '--direction') {
      options.direction = requireArgValue(args, index, '--direction');
      index += 1;
    } else if (arg === '--out') {
      options.outPath = requireArgValue(args, index, '--out');
      index += 1;
    } else if (arg === '--pushed-since') {
      options.pushedSince = requireArgValue(args, index, '--pushed-since');
      index += 1;
    } else if (arg === '--token-env') {
      options.tokenEnv = requireArgValue(args, index, '--token-env');
      index += 1;
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  if (!subject) {
    throw new Error('usage: node reporter.js <username-or-org> [--org] [--format json|text|markdown] [--language <name>] [--top <n>] [--include-forks] [--include-archived] [--pushed-since <iso-date>] [--token-env <ENV_VAR>] [--out <file>]');
  }

  if (!['json', 'text', 'markdown'].includes(options.format)) {
    throw new Error('format must be one of: json, text, markdown');
  }

  if (!Number.isInteger(options.topN) || options.topN <= 0) {
    throw new Error('--top must be a positive integer');
  }

  if (!['created', 'updated', 'pushed', 'full_name'].includes(options.sort)) {
    throw new Error('--sort must be one of: created, updated, pushed, full_name');
  }

  if (!['asc', 'desc'].includes(options.direction)) {
    throw new Error('--direction must be one of: asc, desc');
  }

  if (options.pushedSince) {
    parseDateInput(options.pushedSince, '--pushed-since');
  }

  return { subject, options };
}

async function main() {
  const { subject, options } = parseArgs(process.argv);
  const repos = await fetchRepos(subject, options);
  const summary = summarize(repos, options);
  const output = formatSummary(summary, options);
  await writeOutputIfRequested(output, options.outPath);
  console.log(output);
}

if (require.main === module) {
  main().catch(err => {
    console.error(err.message);
    process.exit(1);
  });
}

module.exports = {
  applyRepoFilters,
  buildListReposUrl,
  buildOrgReposUrl,
  buildReposUrl,
  buildRequestHeaders,
  fetchRepos,
  formatMarkdownSummary,
  formatSummary,
  formatTextSummary,
  normalizeRepo,
  parseArgs,
  parseDateInput,
  parseLinkHeader,
  requireArgValue,
  summarize,
  writeOutputIfRequested
};
