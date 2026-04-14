const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs/promises');
const os = require('os');
const path = require('path');
const {
  markdownToHtml,
  build,
  parseFrontMatter,
  loadPages,
  humanizeTitle,
  slugify,
} = require('./sitegen');

test('parseFrontMatter extracts metadata and body', () => {
  const parsed = parseFrontMatter(`---\r\ntitle: Portfolio\r\norder: 2\r\ntags: [node, markdown]\r\nnav: false\r\n---\r\n# Heading`);
  assert.equal(parsed.data.title, 'Portfolio');
  assert.equal(parsed.data.order, 2);
  assert.deepEqual(parsed.data.tags, ['node', 'markdown']);
  assert.equal(parsed.data.nav, false);
  assert.equal(parsed.content, '# Heading');
});

test('markdownToHtml renders headings, lists, emphasis, code, and links', () => {
  const html = markdownToHtml('# Title\n\n- one\n- two\n\nHello **world** with `code` and [docs](https://example.com) plus [bad](javascript:alert(1))');
  assert.match(html, /<h1>Title<\/h1>/);
  assert.match(html, /<ul>/);
  assert.match(html, /<strong>world<\/strong>/);
  assert.match(html, /<code>code<\/code>/);
  assert.match(html, /<a href="https:\/\/example.com">docs<\/a>/);
  assert.match(html, /<a href="#">bad<\/a>/);
});

test('slugify normalizes custom output names', () => {
  assert.equal(slugify('My Project Page'), 'my-project-page');
  assert.equal(slugify('  C++ & Rust  '), 'c-rust');
});

test('humanizeTitle creates a readable fallback from filenames', () => {
  assert.equal(humanizeTitle('about_me.md'), 'About Me');
  assert.equal(humanizeTitle('systems-projects.md'), 'Systems Projects');
});

test('loadPages sorts by order and title', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'sitegen-pages-'));
  await fs.writeFile(path.join(tmp, 'b.md'), `---\ntitle: Beta\norder: 2\n---\nBody`);
  await fs.writeFile(path.join(tmp, 'a.md'), `---\ntitle: Alpha\norder: 1\n---\nBody`);
  await fs.writeFile(path.join(tmp, 'c.md'), '# Gamma');
  const pages = await loadPages(tmp);
  assert.deepEqual(
    pages.map(page => page.title),
    ['Alpha', 'Beta', 'C']
  );
});

test('build writes styled pages with navigation, descriptions, and tags', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'sitegen-build-'));
  const src = path.join(tmp, 'content');
  const out = path.join(tmp, 'dist');
  await fs.mkdir(src);

  await fs.writeFile(
    path.join(src, 'index.md'),
    `---\ntitle: Home\norder: 1\ndescription: Landing page\ntags: [portfolio, featured]\n---\n# Welcome\n\n- project one\n- project two`
  );
  await fs.writeFile(
    path.join(src, 'about.md'),
    `---\ntitle: About\norder: 2\nslug: about-me\n---\nHello **there**`
  );

  const outputs = await build(src, out);
  assert.deepEqual(outputs, ['index.html', 'about-me.html']);

  const home = await fs.readFile(path.join(out, 'index.html'), 'utf8');
  const about = await fs.readFile(path.join(out, 'about-me.html'), 'utf8');

  assert.match(home, /Landing page/);
  assert.match(home, /portfolio/);
  assert.match(home, /href="about-me.html"/);
  assert.match(home, /class="active" href="index.html"/);
  assert.match(about, /<strong>there<\/strong>/);
  assert.match(about, /href="index.html"/);
});
