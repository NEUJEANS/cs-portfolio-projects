const https = require('https');

const DEFAULT_USER_AGENT = 'cs-portfolio-projects';

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

function requestJson(url, headers = {}) {
  return new Promise((resolve, reject) => {
    const request = https.get(url, {
      headers: {
        'User-Agent': DEFAULT_USER_AGENT,
        Accept: 'application/vnd.github+json',
        ...headers
      }
    }, res => {
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
  let nextUrl = subjectType === 'org'
    ? buildOrgReposUrl(subject, options)
    : buildReposUrl(subject, options);

  while (nextUrl) {
    const { body, headers } = await requestJson(nextUrl, options.headers);
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
    topics: repo.topics || [],
    isFork: repo.fork,
    archived: repo.archived,
    updatedAt: repo.updated_at,
    pushedAt: repo.pushed_at,
    sizeKb: repo.size
  };
}

function applyRepoFilters(repos, options = {}) {
  return repos.filter(repo => {
    if (!options.includeForks && repo.isFork) return false;
    if (!options.includeArchived && repo.archived) return false;
    if (options.language && (repo.language || '').toLowerCase() !== options.language.toLowerCase()) return false;
    return true;
  });
}

function summarize(repos, options = {}) {
  const topN = Number.isInteger(options.topN) && options.topN > 0 ? options.topN : 5;
  const safeRepos = Array.isArray(repos) ? repos : [];
  const totalStars = safeRepos.reduce((sum, repo) => sum + repo.stars, 0);
  const languageCounts = safeRepos.reduce((acc, repo) => {
    const key = repo.language || 'Unknown';
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});

  const mostRecentPush = safeRepos
    .filter(repo => repo.pushedAt)
    .sort((a, b) => new Date(b.pushedAt) - new Date(a.pushedAt))[0] || null;

  return {
    count: safeRepos.length,
    totalStars,
    averageStars: safeRepos.length ? Number((totalStars / safeRepos.length).toFixed(2)) : 0,
    topStarred: [...safeRepos].sort((a, b) => b.stars - a.stars || a.name.localeCompare(b.name)).slice(0, topN),
    recentlyUpdated: [...safeRepos].sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt)).slice(0, topN),
    languages: Object.fromEntries(
      Object.entries(languageCounts).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    ),
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
    `Forks included: ${summary.forkCount}`,
    `Archived included: ${summary.archivedCount}`,
    'Languages:'
  ];

  for (const [language, count] of Object.entries(summary.languages)) {
    lines.push(`- ${language}: ${count}`);
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

  const topRows = summary.topStarred
    .map(repo => `| [${repo.fullName}](${repo.url}) | ${repo.stars} | ${repo.language || 'Unknown'} | ${repo.updatedAt} |`)
    .join('\n') || '| None | 0 | Unknown | n/a |';

  return [
    '# GitHub Repository Report',
    '',
    `- Repositories: **${summary.count}**`,
    `- Total stars: **${summary.totalStars}**`,
    `- Average stars per repo: **${summary.averageStars}**`,
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
    '## Top Starred',
    '',
    '| Repository | Stars | Language | Updated |',
    '| --- | ---: | --- | --- |',
    topRows
  ].join('\n');
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
    subjectType: 'user'
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
      options.format = args[++index];
    } else if (arg === '--language') {
      options.language = args[++index];
    } else if (arg === '--top') {
      options.topN = Number.parseInt(args[++index], 10);
    } else if (arg === '--sort') {
      options.sort = args[++index];
    } else if (arg === '--direction') {
      options.direction = args[++index];
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  if (!subject) {
    throw new Error('usage: node reporter.js <username-or-org> [--org] [--format json|text|markdown] [--language <name>] [--top <n>] [--include-forks] [--include-archived]');
  }

  if (!['json', 'text', 'markdown'].includes(options.format)) {
    throw new Error('format must be one of: json, text, markdown');
  }

  if (!Number.isInteger(options.topN) || options.topN <= 0) {
    throw new Error('--top must be a positive integer');
  }

  return { subject, options };
}

async function main() {
  const { subject, options } = parseArgs(process.argv);
  const repos = await fetchRepos(subject, options);
  const summary = summarize(repos, options);
  console.log(formatSummary(summary, options));
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
  fetchRepos,
  formatMarkdownSummary,
  formatSummary,
  formatTextSummary,
  normalizeRepo,
  parseArgs,
  parseLinkHeader,
  summarize
};
