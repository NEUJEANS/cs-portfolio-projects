const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');

const {
  PARTIALS_DIR_NAME,
  buildSite,
  copyStaticAssets,
  loadPages,
  markdownToHtml,
  parseFrontMatter,
  relativeLink,
  replaceMarkdownImages,
  resolveDocumentHref,
  sanitizeHref,
  slugify,
  toOutputPath,
  walkContentEntries,
} = require('./sitegen');

function makeTempDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'sitegen-suite-'));
}

test('parseFrontMatter extracts metadata and body', () => {
  const parsed = parseFrontMatter(`---\r\ntitle: Portfolio\r\norder: 2\r\ntags: [node, markdown]\r\nnav: false\r\n---\r\n# Heading`);
  assert.equal(parsed.metadata.title, 'Portfolio');
  assert.equal(parsed.metadata.order, 2);
  assert.deepEqual(parsed.metadata.tags, ['node', 'markdown']);
  assert.equal(parsed.metadata.nav, false);
  assert.equal(parsed.body, '# Heading');
});

test('markdownToHtml renders headings, lists, quotes, emphasis, code, links, images, and fenced blocks', () => {
  const html = markdownToHtml('# Title\n\n![Diagram](assets/graph.png)\n\n- one\n- two\n\n3. third\n4. fourth\n\n> quoted **note**\n>\n> follow-up line\n\nHello **world** with `code` and [docs](https://example.com) plus [bad](javascript:alert(1))\n\n```js\nconst x = 1 < 2;\nconsole.log(x);\n```');
  assert.match(html, /<h1>Title<\/h1>/);
  assert.match(html, /<img src="assets\/graph.png" alt="Diagram" loading="lazy">/);
  assert.match(html, /<ul><li>one<\/li><li>two<\/li><\/ul>/);
  assert.match(html, /<ol start="3"><li>third<\/li><li>fourth<\/li><\/ol>/);
  assert.match(html, /<blockquote><p>quoted <strong>note<\/strong><\/p>\s*<p>follow-up line<\/p><\/blockquote>/);
  assert.match(html, /<strong>world<\/strong>/);
  assert.match(html, /<code>code<\/code>/);
  assert.match(html, /<a href="https:\/\/example.com">docs<\/a>/);
  assert.match(html, /<a href="#">bad<\/a>/);
  assert.match(html, /<pre><code class="language-js">const x = 1 &lt; 2;\nconsole\.log\(x\);<\/code><\/pre>/);
});

test('replaceMarkdownImages sanitizes unsafe image URLs', () => {
  const html = replaceMarkdownImages('![blocked](javascript:alert(1)) and ![ok](images/demo.png)');
  assert.match(html, /<img src="#" alt="blocked" loading="lazy">/);
  assert.match(html, /<img src="images\/demo.png" alt="ok" loading="lazy">/);
});

test('slugify normalizes custom output names', () => {
  assert.equal(slugify('My Project Page'), 'my-project-page');
  assert.equal(slugify('  C++ & Rust  '), 'c-rust');
});

test('toOutputPath keeps nested directories and rewrites markdown extension', () => {
  assert.equal(toOutputPath('index.md'), 'index.html');
  assert.equal(toOutputPath('guides/setup.md'), 'guides/setup.html');
  assert.equal(toOutputPath('posts/hello-world.md', { slug: 'intro-post' }), 'posts/intro-post.html');
});

test('resolveDocumentHref rewrites markdown links relative to the rendered page', () => {
  const page = {
    sourceName: 'guides/setup.md',
    outputName: 'guides/setup.html',
  };

  assert.equal(resolveDocumentHref('../index.md', page), '../index.html');
  assert.equal(resolveDocumentHref('../posts/welcome.md#demo', page), '../posts/welcome.html#demo');
  assert.equal(resolveDocumentHref('assets/diagram.png', page), 'assets/diagram.png');
});

test('relativeLink computes nav hrefs across nested pages', () => {
  assert.equal(relativeLink('guides/setup.html', 'index.html'), '../index.html');
  assert.equal(relativeLink('guides/setup.html', 'posts/welcome.html'), '../posts/welcome.html');
  assert.equal(relativeLink('posts/welcome.html', 'posts/welcome.html'), 'welcome.html');
});

test('walkContentEntries and loadPages ignore reserved partial templates and keep nested content in stable order', () => {
  const tmp = makeTempDir();
  fs.mkdirSync(path.join(tmp, 'nested'), { recursive: true });
  fs.mkdirSync(path.join(tmp, PARTIALS_DIR_NAME), { recursive: true });
  fs.writeFileSync(path.join(tmp, PARTIALS_DIR_NAME, 'header.html'), '<p>Shared header</p>', 'utf8');
  fs.writeFileSync(path.join(tmp, 'nested', 'diagram.png'), 'fake-image', 'utf8');
  fs.writeFileSync(path.join(tmp, 'b.md'), `---\ntitle: Beta\norder: 2\n---\nBody`, 'utf8');
  fs.writeFileSync(path.join(tmp, 'nested', 'a.md'), `---\ntitle: Alpha\norder: 1\n---\nBody`, 'utf8');
  fs.writeFileSync(path.join(tmp, 'c.md'), '# Gamma', 'utf8');

  const entries = walkContentEntries(tmp).map((entry) => entry.relativePath);
  assert.deepEqual(entries, ['b.md', 'c.md', path.join('nested', 'a.md'), path.join('nested', 'diagram.png')]);

  const pages = loadPages(tmp);
  assert.deepEqual(
    pages.map((page) => page.metadata.title || page.slug),
    ['Alpha', 'Beta', 'c']
  );
  assert.deepEqual(
    pages.map((page) => page.outputName),
    ['nested/alpha.html', 'beta.html', 'c.html']
  );
});

test('copyStaticAssets preserves nested asset paths while excluding reserved partial files', () => {
  const contentDir = makeTempDir();
  const outputDir = makeTempDir();
  fs.mkdirSync(path.join(contentDir, 'assets'), { recursive: true });
  fs.mkdirSync(path.join(contentDir, PARTIALS_DIR_NAME), { recursive: true });
  fs.writeFileSync(path.join(contentDir, 'index.md'), '# Home', 'utf8');
  fs.writeFileSync(path.join(contentDir, PARTIALS_DIR_NAME, 'footer.html'), '<p>Footer</p>', 'utf8');
  fs.writeFileSync(path.join(contentDir, 'assets', 'styles.css'), 'body { color: red; }', 'utf8');

  const copied = copyStaticAssets(contentDir, outputDir);
  assert.deepEqual(copied, [path.join('assets', 'styles.css')]);
  assert.equal(fs.readFileSync(path.join(outputDir, 'assets', 'styles.css'), 'utf8'), 'body { color: red; }');
  assert.equal(fs.existsSync(path.join(outputDir, PARTIALS_DIR_NAME, 'footer.html')), false);
});

test('markdownToHtml closes an unclosed fenced code block at end of document', () => {
  const html = markdownToHtml('```python\nprint("hi")');
  assert.match(html, /<pre><code class="language-python">print\(&quot;hi&quot;\)<\/code><\/pre>/);
});

test('buildSite writes nested pages, relative nav links, copied assets, and generated tag archives', () => {
  const contentDir = makeTempDir();
  const outputDir = makeTempDir();
  fs.mkdirSync(path.join(contentDir, 'images'), { recursive: true });
  fs.mkdirSync(path.join(contentDir, 'guides'), { recursive: true });

  fs.writeFileSync(
    path.join(contentDir, 'index.md'),
    `---
title: Home
order: 1
description: Landing page
nav: true
---
# Welcome

See the [setup guide](guides/setup.md).`,
    'utf8'
  );

  fs.writeFileSync(
    path.join(contentDir, 'guides', 'setup.md'),
    `---
title: Setup Guide
order: 2
slug: setup
tags: [portfolio, docs]
---
# Setup

![Hero](../images/hero.png)

1. Install Node.js
2. Run the builder

> Tip: keep screenshots next to your Markdown files for easy copying.

test command:

\`\`\`bash
node sitegen.js content dist
\`\`\`

Return [home](../index.md).`,
    'utf8'
  );

  fs.writeFileSync(path.join(contentDir, 'images', 'hero.png'), 'png-data', 'utf8');

  const result = buildSite(contentDir, outputDir);
  assert.equal(result.pages.length, 5);
  assert.deepEqual(result.assets, [path.join('images', 'hero.png')]);
  assert.deepEqual(
    result.pages.map((page) => page.output).sort(),
    ['guides/setup.html', 'index.html', 'tags/docs.html', 'tags/index.html', 'tags/portfolio.html']
  );

  const homeHtml = fs.readFileSync(path.join(outputDir, 'index.html'), 'utf8');
  const setupHtml = fs.readFileSync(path.join(outputDir, 'guides', 'setup.html'), 'utf8');
  const tagIndexHtml = fs.readFileSync(path.join(outputDir, 'tags', 'index.html'), 'utf8');
  const docsTagHtml = fs.readFileSync(path.join(outputDir, 'tags', 'docs.html'), 'utf8');

  assert.match(homeHtml, /<a class="active" href="index.html">Home<\/a>/);
  assert.match(homeHtml, /<a href="guides\/setup.html">Setup Guide<\/a>/);
  assert.match(homeHtml, /<a href="tags\/index.html">Tags<\/a>/);
  assert.match(homeHtml, /href="guides\/setup.html"/);
  assert.match(setupHtml, /<a href="\.\.\/index.html">Home<\/a>/);
  assert.match(setupHtml, /<a class="active" href="setup.html">Setup Guide<\/a>/);
  assert.match(setupHtml, /<img src="\.\.\/images\/hero.png" alt="Hero" loading="lazy">/);
  assert.match(setupHtml, /<ol><li>Install Node\.js<\/li><li>Run the builder<\/li><\/ol>/);
  assert.match(setupHtml, /<blockquote><p>Tip: keep screenshots next to your Markdown files for easy copying\.<\/p><\/blockquote>/);
  assert.match(setupHtml, /<pre><code class="language-bash">node sitegen\.js content dist<\/code><\/pre>/);
  assert.match(setupHtml, /href="\.\.\/index.html">home<\/a>/i);
  assert.match(setupHtml, /<a class="tag-pill" href="\.\.\/tags\/portfolio.html">portfolio<\/a>/);
  assert.match(setupHtml, /<a class="tag-pill" href="\.\.\/tags\/docs.html">docs<\/a>/);

  assert.match(tagIndexHtml, /<a class="active" href="index.html">Tags<\/a>/);
  assert.match(tagIndexHtml, /href="docs.html">docs<\/a> <span class="tag-count">1 page<\/span>/);
  assert.match(docsTagHtml, /href="index.html">← All tags<\/a>/);
  assert.match(docsTagHtml, /href="\.\.\/guides\/setup.html">Setup Guide<\/a>/);
  assert.equal(fs.readFileSync(path.join(outputDir, 'images', 'hero.png'), 'utf8'), 'png-data');
});

test('buildSite injects shared header and footer partials with page-aware root paths', () => {
  const contentDir = makeTempDir();
  const outputDir = makeTempDir();
  fs.mkdirSync(path.join(contentDir, 'assets'), { recursive: true });
  fs.mkdirSync(path.join(contentDir, 'guides'), { recursive: true });
  fs.mkdirSync(path.join(contentDir, PARTIALS_DIR_NAME), { recursive: true });

  fs.writeFileSync(
    path.join(contentDir, PARTIALS_DIR_NAME, 'header.html'),
    [
      '<p class="brand"><a href="{{rootPath}}index.html">Portfolio Home</a></p>',
      '{{navigation}}',
      '<div class="hero"><h1>{{title}}</h1><p>{{description}}</p>{{tags}}</div>',
    ].join('\n'),
    'utf8'
  );

  fs.writeFileSync(
    path.join(contentDir, PARTIALS_DIR_NAME, 'footer.html'),
    [
      '<p class="source">Source: <code>{{sourcePath}}</code></p>',
      '<p class="resume-link"><a href="{{rootPath}}assets/resume.pdf">Resume</a></p>',
    ].join('\n'),
    'utf8'
  );

  fs.writeFileSync(
    path.join(contentDir, 'index.md'),
    `---
title: Home
order: 1
description: Landing page
---
# Welcome`,
    'utf8'
  );

  fs.writeFileSync(
    path.join(contentDir, 'guides', 'setup.md'),
    `---
title: Setup Guide
order: 2
description: Nested page
tags: [docs]
---
# Setup`,
    'utf8'
  );

  fs.writeFileSync(path.join(contentDir, 'assets', 'resume.pdf'), 'pdf-data', 'utf8');

  buildSite(contentDir, outputDir);

  const homeHtml = fs.readFileSync(path.join(outputDir, 'index.html'), 'utf8');
  const setupHtml = fs.readFileSync(path.join(outputDir, 'guides', 'setup-guide.html'), 'utf8');
  const docsTagHtml = fs.readFileSync(path.join(outputDir, 'tags', 'docs.html'), 'utf8');

  assert.match(homeHtml, /<a href="index.html">Portfolio Home<\/a>/);
  assert.match(homeHtml, /<p class="source">Source: <code>index.md<\/code><\/p>/);
  assert.match(homeHtml, /<a href="assets\/resume.pdf">Resume<\/a>/);

  assert.match(setupHtml, /<a href="\.\.\/index.html">Portfolio Home<\/a>/);
  assert.match(setupHtml, /<a class="active" href="setup-guide.html">Setup Guide<\/a>/);
  assert.match(setupHtml, /<a class="tag-pill" href="\.\.\/tags\/docs.html">docs<\/a>/);
  assert.match(setupHtml, /<p class="source">Source: <code>guides\/setup.md<\/code><\/p>/);
  assert.match(setupHtml, /<a href="\.\.\/assets\/resume.pdf">Resume<\/a>/);
  assert.equal(fs.existsSync(path.join(outputDir, PARTIALS_DIR_NAME, 'header.html')), false);
});

test('sanitizeHref still blocks unsafe protocols', () => {
  assert.equal(sanitizeHref('https://example.com'), 'https://example.com');
  assert.equal(sanitizeHref('student-projects.html'), 'student-projects.html');
  assert.equal(sanitizeHref('javascript:alert(1)'), '#');
});

