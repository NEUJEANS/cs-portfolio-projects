const fs = require('fs/promises');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const {
  applyRepoFilters,
  buildListReposUrl,
  buildOrgReposUrl,
  buildReposUrl,
  formatMarkdownSummary,
  formatTextSummary,
  normalizeRepo,
  parseArgs,
  parseLinkHeader,
  requireArgValue,
  summarize,
  writeOutputIfRequested
} = require('./reporter');

const sampleRepos = [
  {
    name: 'alpha',
    fullName: 'demo/alpha',
    url: 'https://github.com/demo/alpha',
    stars: 2,
    forks: 1,
    watchers: 2,
    openIssues: 0,
    language: 'Python',
    topics: ['cli', 'portfolio'],
    isFork: false,
    archived: false,
    updatedAt: '2026-04-01T10:00:00Z',
    pushedAt: '2026-04-01T09:00:00Z',
    sizeKb: 120
  },
  {
    name: 'beta',
    fullName: 'demo/beta',
    url: 'https://github.com/demo/beta',
    stars: 5,
    forks: 2,
    watchers: 5,
    openIssues: 1,
    language: 'JavaScript',
    topics: ['portfolio', 'api'],
    isFork: true,
    archived: false,
    updatedAt: '2026-04-02T10:00:00Z',
    pushedAt: '2026-04-02T09:00:00Z',
    sizeKb: 480
  },
  {
    name: 'gamma',
    fullName: 'demo/gamma',
    url: 'https://github.com/demo/gamma',
    stars: 1,
    forks: 0,
    watchers: 1,
    openIssues: 0,
    language: null,
    topics: [],
    isFork: false,
    archived: true,
    updatedAt: '2026-04-03T10:00:00Z',
    pushedAt: '2026-04-03T09:00:00Z',
    sizeKb: 424
  }
];

test('normalizeRepo removes empty and duplicate topics', () => {
  const repo = normalizeRepo({
    name: 'delta',
    full_name: 'demo/delta',
    description: null,
    html_url: 'https://github.com/demo/delta',
    stargazers_count: 0,
    forks_count: 0,
    watchers_count: 0,
    open_issues_count: 0,
    language: 'JavaScript',
    topics: ['cli', '', 'cli', 'portfolio'],
    fork: false,
    archived: false,
    updated_at: '2026-04-01T00:00:00Z',
    pushed_at: '2026-04-01T00:00:00Z',
    size: 10
  });

  assert.deepEqual(repo.topics, ['cli', 'portfolio']);
});

test('summarize counts repos, stars, languages, topics, and activity totals', () => {
  const summary = summarize(sampleRepos, { topN: 2 });
  assert.equal(summary.count, 3);
  assert.equal(summary.totalStars, 8);
  assert.equal(summary.averageStars, 2.67);
  assert.equal(summary.totalForks, 3);
  assert.equal(summary.averageForks, 1);
  assert.equal(summary.totalWatchers, 8);
  assert.equal(summary.totalOpenIssues, 1);
  assert.equal(summary.totalSizeKb, 1024);
  assert.equal(summary.totalSizeMb, 1);
  assert.equal(summary.languages.Python, 1);
  assert.equal(summary.languages.JavaScript, 1);
  assert.equal(summary.languages.Unknown, 1);
  assert.equal(summary.topTopics[0].topic, 'portfolio');
  assert.equal(summary.topTopics[0].count, 2);
  assert.equal(summary.topStarred[0].name, 'beta');
  assert.equal(summary.recentlyUpdated[0].name, 'gamma');
  assert.equal(summary.mostRecentPush.name, 'gamma');
});

test('applyRepoFilters excludes forks and archived repos by default', () => {
  const filtered = applyRepoFilters(sampleRepos, {});
  assert.deepEqual(filtered.map(repo => repo.name), ['alpha']);
});

test('applyRepoFilters can include forks, archived repos, and language filters', () => {
  const includeAll = applyRepoFilters(sampleRepos, { includeForks: true, includeArchived: true });
  assert.equal(includeAll.length, 3);

  const pythonOnly = applyRepoFilters(sampleRepos, {
    includeForks: true,
    includeArchived: true,
    language: 'python'
  });
  assert.deepEqual(pythonOnly.map(repo => repo.name), ['alpha']);
});

test('parseLinkHeader extracts rel URLs', () => {
  const parsed = parseLinkHeader('<https://api.github.com/user/repos?page=2>; rel="next", <https://api.github.com/user/repos?page=4>; rel="last"');
  assert.equal(parsed.next, 'https://api.github.com/user/repos?page=2');
  assert.equal(parsed.last, 'https://api.github.com/user/repos?page=4');
});

test('buildReposUrl encodes username and query options', () => {
  const url = buildReposUrl('octo cat', { page: 2, sort: 'created', direction: 'asc', type: 'owner' });
  assert.match(url, /users\/octo%20cat\/repos\?/);
  assert.match(url, /page=2/);
  assert.match(url, /sort=created/);
  assert.match(url, /direction=asc/);
  assert.match(url, /type=owner/);
});

test('buildOrgReposUrl encodes org name and keeps repo list parameters', () => {
  const url = buildOrgReposUrl('student-lab', { page: 3, sort: 'full_name', direction: 'asc', type: 'public' });
  assert.match(url, /orgs\/student-lab\/repos\?/);
  assert.match(url, /page=3/);
  assert.match(url, /sort=full_name/);
  assert.match(url, /direction=asc/);
  assert.match(url, /type=public/);
});

test('buildListReposUrl switches endpoint by subject type', () => {
  assert.match(buildListReposUrl('octocat', { subjectType: 'user' }), /users\/octocat\/repos/);
  assert.match(buildListReposUrl('neu-lab', { subjectType: 'org' }), /orgs\/neu-lab\/repos/);
});

test('requireArgValue rejects missing flag values', () => {
  assert.throws(() => requireArgValue(['--format'], 0, '--format'), /requires a value/);
  assert.throws(() => requireArgValue(['--format', '--top'], 0, '--format'), /requires a value/);
});

test('parseArgs accepts filters, output format, org mode, and output files', () => {
  const { subject, options } = parseArgs([
    'node',
    'reporter.js',
    'openai',
    '--org',
    '--format',
    'markdown',
    '--language',
    'Python',
    '--top',
    '3',
    '--include-forks',
    '--out',
    'reports/openai.md'
  ]);

  assert.equal(subject, 'openai');
  assert.equal(options.subjectType, 'org');
  assert.equal(options.format, 'markdown');
  assert.equal(options.language, 'Python');
  assert.equal(options.topN, 3);
  assert.equal(options.includeForks, true);
  assert.equal(options.includeArchived, false);
  assert.equal(options.outPath, 'reports/openai.md');
});

test('parseArgs defaults to user mode without --org', () => {
  const { subject, options } = parseArgs(['node', 'reporter.js', 'octocat']);
  assert.equal(subject, 'octocat');
  assert.equal(options.subjectType, 'user');
});

test('parseArgs rejects invalid top values', () => {
  assert.throws(() => parseArgs(['node', 'reporter.js', 'octocat', '--top', '0']), /positive integer/);
});

test('parseArgs usage text mentions org mode when subject is missing', () => {
  assert.throws(() => parseArgs(['node', 'reporter.js']), /--org/);
});

test('parseArgs rejects missing --out values', () => {
  assert.throws(() => parseArgs(['node', 'reporter.js', 'octocat', '--out']), /requires a value/);
});

test('parseArgs rejects unsupported sort and direction values', () => {
  assert.throws(() => parseArgs(['node', 'reporter.js', 'octocat', '--sort', 'stars']), /--sort must be one of/);
  assert.throws(() => parseArgs(['node', 'reporter.js', 'octocat', '--direction', 'sideways']), /--direction must be one of/);
});

test('formatters produce readable text and markdown output including topic insights', () => {
  const summary = summarize(sampleRepos, { topN: 2 });
  const text = formatTextSummary(summary);
  const markdown = formatMarkdownSummary(summary);

  assert.match(text, /Repositories: 3/);
  assert.match(text, /Top topics:/);
  assert.match(text, /portfolio: 2/);
  assert.match(markdown, /# GitHub Repository Report/);
  assert.match(markdown, /## Top Topics/);
  assert.match(markdown, /\| Topic \| Repositories \|/);
  assert.match(markdown, /demo\/beta/);
});

test('writeOutputIfRequested writes nested output files', async () => {
  const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'repo-reporter-'));
  const outPath = path.join(tempDir, 'nested', 'report.md');
  await writeOutputIfRequested('hello report', outPath);
  const contents = await fs.readFile(outPath, 'utf8');
  assert.equal(contents, 'hello report');
});

test('writeOutputIfRequested skips writes when no output path is provided', async () => {
  await writeOutputIfRequested('ignored', null);
  assert.ok(true);
});