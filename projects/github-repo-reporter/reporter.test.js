const test = require('node:test');
const assert = require('node:assert/strict');
const {
  applyRepoFilters,
  buildListReposUrl,
  buildOrgReposUrl,
  buildReposUrl,
  formatMarkdownSummary,
  formatTextSummary,
  parseArgs,
  parseLinkHeader,
  summarize
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
    isFork: false,
    archived: false,
    updatedAt: '2026-04-01T10:00:00Z',
    pushedAt: '2026-04-01T09:00:00Z'
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
    isFork: true,
    archived: false,
    updatedAt: '2026-04-02T10:00:00Z',
    pushedAt: '2026-04-02T09:00:00Z'
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
    isFork: false,
    archived: true,
    updatedAt: '2026-04-03T10:00:00Z',
    pushedAt: '2026-04-03T09:00:00Z'
  }
];

test('summarize counts repos, stars, languages, and recent activity', () => {
  const summary = summarize(sampleRepos, { topN: 2 });
  assert.equal(summary.count, 3);
  assert.equal(summary.totalStars, 8);
  assert.equal(summary.averageStars, 2.67);
  assert.equal(summary.languages.Python, 1);
  assert.equal(summary.languages.JavaScript, 1);
  assert.equal(summary.languages.Unknown, 1);
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

test('parseArgs accepts filters, output format, and org mode', () => {
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
    '--include-forks'
  ]);

  assert.equal(subject, 'openai');
  assert.equal(options.subjectType, 'org');
  assert.equal(options.format, 'markdown');
  assert.equal(options.language, 'Python');
  assert.equal(options.topN, 3);
  assert.equal(options.includeForks, true);
  assert.equal(options.includeArchived, false);
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

test('formatters produce readable text and markdown output', () => {
  const summary = summarize(sampleRepos, { topN: 2 });
  const text = formatTextSummary(summary);
  const markdown = formatMarkdownSummary(summary);

  assert.match(text, /Repositories: 3/);
  assert.match(text, /Top starred:/);
  assert.match(markdown, /# GitHub Repository Report/);
  assert.match(markdown, /\| Repository \| Stars \| Language \| Updated \|/);
  assert.match(markdown, /demo\/beta/);
});
