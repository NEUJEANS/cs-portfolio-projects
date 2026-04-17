const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const http = require('http');
const os = require('os');
const path = require('path');
const { spawn } = require('child_process');

const {
  DEFAULT_SERVE_HOST,
  LIVE_RELOAD_PATH,
  NOT_FOUND_OUTPUT_NAME,
  PARTIALS_DIR_NAME,
  applyPreviewPlaceholders,
  buildSite,
  copyStaticAssets,
  createWatchSnapshot,
  injectLiveReloadClient,
  loadPages,
  markdownToHtml,
  parseCliArgs,
  parseCodeFenceInfo,
  parseFrontMatter,
  relativeLink,
  replaceMarkdownImages,
  resolveDocumentHref,
  resolvePreviewRequestPath,
  sanitizeHref,
  slugify,
  startPreviewServer,
  toOutputPath,
  walkContentEntries,
} = require('./sitegen');

function makeTempDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'sitegen-suite-'));
}

async function waitFor(predicate, { timeoutMs = 5000, intervalMs = 100 } = {}) {
  const started = Date.now();

  while (Date.now() - started < timeoutMs) {
    const value = await predicate();
    if (value) {
      return value;
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }

  throw new Error(`Timed out after ${timeoutMs}ms waiting for condition.`);
}

function httpRequest({ host = DEFAULT_SERVE_HOST, port, path: requestPath = '/', method = 'GET' }) {
  return new Promise((resolve, reject) => {
    const req = http.request({ host, port, path: requestPath, method }, (res) => {
      let body = '';
      res.setEncoding('utf8');
      res.on('data', (chunk) => {
        body += chunk;
      });
      res.on('end', () => {
        resolve({ statusCode: res.statusCode, headers: res.headers, body });
      });
    });
    req.on('error', reject);
    req.end();
  });
}

test('parseFrontMatter extracts metadata and body', () => {
  const parsed = parseFrontMatter(`---\r\ntitle: Portfolio\r\norder: 2\r\ntags: [node, markdown]\r\nnav: false\r\n---\r\n# Heading`);
  assert.equal(parsed.metadata.title, 'Portfolio');
  assert.equal(parsed.metadata.order, 2);
  assert.deepEqual(parsed.metadata.tags, ['node', 'markdown']);
  assert.equal(parsed.metadata.nav, false);
  assert.equal(parsed.body, '# Heading');
});

test('parseCliArgs enables watch mode, preview serving, and custom ports', () => {
  const parsed = parseCliArgs(['content', 'dist', '--watch', '--watch-interval', '750', '--serve', '--serve-port', '4321']);
  assert.equal(parsed.contentDir, 'content');
  assert.equal(parsed.outputDir, 'dist');
  assert.equal(parsed.options.watch, true);
  assert.equal(parsed.options.watchIntervalMs, 750);
  assert.equal(parsed.options.serve, true);
  assert.equal(parsed.options.servePort, 4321);
});

test('parseCodeFenceInfo extracts language aliases and optional code titles', () => {
  assert.deepEqual(parseCodeFenceInfo('js title=sitegen.js'), { language: 'js', title: 'sitegen.js' });
  assert.deepEqual(parseCodeFenceInfo('python filename="demo script.py"'), { language: 'python', title: 'demo script.py' });
  assert.deepEqual(parseCodeFenceInfo('title="notes.txt"'), { language: '', title: 'notes.txt' });
});

test('createWatchSnapshot changes when shared partial templates change', () => {
  const contentDir = makeTempDir();
  fs.mkdirSync(path.join(contentDir, PARTIALS_DIR_NAME), { recursive: true });
  fs.writeFileSync(path.join(contentDir, 'index.md'), '# Home', 'utf8');
  fs.writeFileSync(path.join(contentDir, PARTIALS_DIR_NAME, 'header.html'), '<p>One</p>', 'utf8');

  const before = createWatchSnapshot(contentDir);
  const partialPath = path.join(contentDir, PARTIALS_DIR_NAME, 'header.html');
  const stats = fs.statSync(partialPath);
  fs.utimesSync(partialPath, stats.atime, new Date(Date.now() + 1500));
  fs.writeFileSync(partialPath, '<p>Two</p>', 'utf8');
  const after = createWatchSnapshot(contentDir);

  assert.notEqual(before, after);
  assert.match(after, /_partials\/header\.html/);
});

test('injectLiveReloadClient adds an EventSource script before </body>', () => {
  const html = injectLiveReloadClient('<html><body><main>Hello</main></body></html>');
  assert.match(html, /<main>Hello<\/main>/);
  assert.match(html, /EventSource/);
  assert.match(html, new RegExp(LIVE_RELOAD_PATH.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
});

test('applyPreviewPlaceholders escapes missing-route context for custom 404 pages', () => {
  const html = applyPreviewPlaceholders('<p>{{statusCode}} {{requestedPath}} {{requestedUrl}}</p>', '/missing/%3Cdemo%3E?from=preview', 404);
  assert.equal(html, '<p>404 /missing/<demo> /missing/<demo>?from=preview</p>'.replaceAll('<demo>', '&lt;demo&gt;'));
});

test('applyPreviewPlaceholders tolerates malformed escape sequences', () => {
  const html = applyPreviewPlaceholders('<p>{{requestedPath}}</p>', '/broken/%E0%A4%A', 404);
  assert.equal(html, '<p>/broken/%E0%A4%A</p>');
});

test('markdownToHtml renders headings, lists, quotes, emphasis, code, links, images, and fenced blocks', () => {
  const html = markdownToHtml('# Title\n\n![Diagram](assets/graph.png)\n\n- one\n- two\n\n3. third\n4. fourth\n\n> quoted **note**\n>\n> follow-up line\n\nHello **world** with `code` and [docs](https://example.com) plus [bad](javascript:alert(1))\n\n```js title="sitegen.js"\nconst x = 1 < 2;\nconsole.log(x);\n```');
  assert.match(html, /<h1>Title<\/h1>/);
  assert.match(html, /<img src="assets\/graph.png" alt="Diagram" loading="lazy">/);
  assert.match(html, /<ul><li>one<\/li><li>two<\/li><\/ul>/);
  assert.match(html, /<ol start="3"><li>third<\/li><li>fourth<\/li><\/ol>/);
  assert.match(html, /<blockquote><p>quoted <strong>note<\/strong><\/p>\s*<p>follow-up line<\/p><\/blockquote>/);
  assert.match(html, /<strong>world<\/strong>/);
  assert.match(html, /<code>code<\/code>/);
  assert.match(html, /<a href="https:\/\/example.com">docs<\/a>/);
  assert.match(html, /<a href="#">bad<\/a>/);
  assert.match(html, /<figure class="code-block">/);
  assert.match(html, /<span class="code-block__title">sitegen\.js<\/span>/);
  assert.match(html, /<span class="code-block__language">JavaScript<\/span>/);
  assert.match(html, /<span class="code-block__line-count">2 lines<\/span>/);
  assert.match(html, /<code class="language-js"><span class="code-block__line" data-line="1"><span class="code-block__line-content">const x = 1 &lt; 2;<\/span><\/span>\n<span class="code-block__line" data-line="2"><span class="code-block__line-content">console\.log\(x\);<\/span><\/span><\/code>/);
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
  assert.equal(toOutputPath('404.md', { title: 'Page Not Found' }), '404.html');
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
  const html = markdownToHtml('```python title="demo.py"\nprint("hi")');
  assert.match(html, /<span class="code-block__title">demo\.py<\/span>/);
  assert.match(html, /<span class="code-block__language">Python<\/span>/);
  assert.match(html, /<span class="code-block__line-count">1 line<\/span>/);
  assert.match(html, /<code class="language-python"><span class="code-block__line" data-line="1"><span class="code-block__line-content">print\(&quot;hi&quot;\)<\/span><\/span><\/code>/);
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
  assert.equal(result.pages.length, 6);
  assert.deepEqual(result.assets, [path.join('images', 'hero.png')]);
  assert.deepEqual(
    result.pages.map((page) => page.output).sort(),
    ['404.html', 'guides/setup.html', 'index.html', 'tags/docs.html', 'tags/index.html', 'tags/portfolio.html']
  );

  const homeHtml = fs.readFileSync(path.join(outputDir, 'index.html'), 'utf8');
  const setupHtml = fs.readFileSync(path.join(outputDir, 'guides', 'setup.html'), 'utf8');
  const notFoundHtml = fs.readFileSync(path.join(outputDir, NOT_FOUND_OUTPUT_NAME), 'utf8');
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
  assert.match(setupHtml, /<figure class="code-block">/);
  assert.match(setupHtml, /<span class="code-block__language">Bash<\/span>/);
  assert.match(setupHtml, /<span class="code-block__line-count">1 line<\/span>/);
  assert.match(setupHtml, /<code class="language-bash"><span class="code-block__line" data-line="1"><span class="code-block__line-content">node sitegen\.js content dist<\/span><\/span><\/code>/);
  assert.match(setupHtml, /href="\.\.\/index.html">home<\/a>/i);
  assert.match(setupHtml, /<a class="tag-pill" href="\.\.\/tags\/portfolio.html">portfolio<\/a>/);
  assert.match(setupHtml, /<a class="tag-pill" href="\.\.\/tags\/docs.html">docs<\/a>/);
  assert.match(notFoundHtml, /Page Not Found/);
  assert.match(notFoundHtml, /href="index.html">Home<\/a>/);
  assert.doesNotMatch(notFoundHtml, /href="404.html">Page Not Found<\/a>/);

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
  assert.match(docsTagHtml, /<p class="source">Source: <code>\(generated\)<\/code><\/p>/);
  assert.equal(fs.existsSync(path.join(outputDir, PARTIALS_DIR_NAME, 'header.html')), false);
});

test('buildSite lets authors provide a custom 404 page without adding it to navigation by default', () => {
  const contentDir = makeTempDir();
  const outputDir = makeTempDir();

  fs.writeFileSync(
    path.join(contentDir, 'index.md'),
    `---
title: Home
order: 1
---
# Welcome`,
    'utf8'
  );

  fs.writeFileSync(
    path.join(contentDir, '404.md'),
    '# Missing page\n\nTried: `{{requestedPath}}`\n',
    'utf8'
  );

  const result = buildSite(contentDir, outputDir);
  const notFoundEntries = result.pages.filter((page) => page.output === NOT_FOUND_OUTPUT_NAME);
  const notFoundHtml = fs.readFileSync(path.join(outputDir, NOT_FOUND_OUTPUT_NAME), 'utf8');

  assert.equal(notFoundEntries.length, 1);
  assert.equal(notFoundEntries[0].source, '404.md');
  assert.match(notFoundHtml, /<title>Page Not Found<\/title>/);
  assert.match(notFoundHtml, /Tried: <code>\{\{requestedPath\}\}<\/code>/);
  assert.doesNotMatch(notFoundHtml, /href="404.html">Page Not Found<\/a>/);
});

test('resolvePreviewRequestPath maps extensionless routes and blocks traversal', () => {
  const outputDir = makeTempDir();
  fs.mkdirSync(path.join(outputDir, 'guides'), { recursive: true });
  fs.mkdirSync(path.join(outputDir, 'assets'), { recursive: true });
  fs.writeFileSync(path.join(outputDir, 'index.html'), '<h1>Home</h1>', 'utf8');
  fs.writeFileSync(path.join(outputDir, 'guides', 'setup.html'), '<h1>Setup</h1>', 'utf8');
  fs.writeFileSync(path.join(outputDir, 'assets', 'logo.png'), 'png', 'utf8');

  assert.equal(resolvePreviewRequestPath(outputDir, '/'), path.join(outputDir, 'index.html'));
  assert.equal(resolvePreviewRequestPath(outputDir, '/guides/setup'), path.join(outputDir, 'guides', 'setup.html'));
  assert.equal(resolvePreviewRequestPath(outputDir, '/guides/setup.html'), path.join(outputDir, 'guides', 'setup.html'));
  assert.equal(resolvePreviewRequestPath(outputDir, '/assets/logo.png'), path.join(outputDir, 'assets', 'logo.png'));
  assert.equal(resolvePreviewRequestPath(outputDir, '/../secret.txt'), null);
});

test('preview server serves extensionless html routes and injects live reload only into html', async (t) => {
  const outputDir = makeTempDir();
  fs.mkdirSync(path.join(outputDir, 'guides'), { recursive: true });
  fs.mkdirSync(path.join(outputDir, 'assets'), { recursive: true });
  fs.writeFileSync(path.join(outputDir, 'index.html'), '<html><body><h1>Home</h1></body></html>', 'utf8');
  fs.writeFileSync(path.join(outputDir, 'guides', 'setup.html'), '<html><body><h1>Setup</h1></body></html>', 'utf8');
  fs.writeFileSync(path.join(outputDir, 'assets', 'app.js'), 'console.log("ok");', 'utf8');

  const preview = await startPreviewServer(outputDir, { port: 0, liveReload: true });
  t.after(async () => {
    await preview.close();
  });

  const setupPage = await httpRequest({ port: preview.port, path: '/guides/setup' });
  assert.equal(setupPage.statusCode, 200);
  assert.match(setupPage.body, /<h1>Setup<\/h1>/);
  assert.match(setupPage.body, /EventSource/);

  const scriptAsset = await httpRequest({ port: preview.port, path: '/assets/app.js' });
  assert.equal(scriptAsset.statusCode, 200);
  assert.equal(scriptAsset.body, 'console.log("ok");');
  assert.doesNotMatch(scriptAsset.body, /EventSource/);
});

test('preview server serves custom html 404 pages with request placeholders on missing routes', async (t) => {
  const outputDir = makeTempDir();
  fs.writeFileSync(
    path.join(outputDir, NOT_FOUND_OUTPUT_NAME),
    '<html><body><h1>Missing</h1><p>{{statusCode}} {{requestedPath}}</p></body></html>',
    'utf8'
  );

  const preview = await startPreviewServer(outputDir, { port: 0, liveReload: true });
  t.after(async () => {
    await preview.close();
  });

  const response = await httpRequest({ port: preview.port, path: '/docs/missing' });
  assert.equal(response.statusCode, 404);
  assert.match(response.body, /<h1>Missing<\/h1>/);
  assert.match(response.body, /<p>404 \/docs\/missing<\/p>/);
  assert.match(response.body, /EventSource/);
});

test('preview server leaves 404 placeholders untouched on regular html routes', async (t) => {
  const outputDir = makeTempDir();
  fs.writeFileSync(
    path.join(outputDir, 'index.html'),
    '<html><body><p>{{requestedPath}}</p></body></html>',
    'utf8'
  );

  const preview = await startPreviewServer(outputDir, { port: 0, liveReload: true });
  t.after(async () => {
    await preview.close();
  });

  const response = await httpRequest({ port: preview.port, path: '/' });
  assert.equal(response.statusCode, 200);
  assert.match(response.body, /<p>\{\{requestedPath\}\}<\/p>/);
  assert.match(response.body, /EventSource/);
});

test('preview server returns an empty body for HEAD misses without a custom 404 page', async (t) => {
  const outputDir = makeTempDir();
  const preview = await startPreviewServer(outputDir, { port: 0, liveReload: false });
  t.after(async () => {
    await preview.close();
  });

  const response = await httpRequest({ port: preview.port, path: '/missing', method: 'HEAD' });
  assert.equal(response.statusCode, 404);
  assert.equal(response.body, '');
});

test('preview server can serve static output without injecting live reload when watch mode is off', async (t) => {
  const outputDir = makeTempDir();
  fs.writeFileSync(path.join(outputDir, 'index.html'), '<html><body><h1>Standalone preview</h1></body></html>', 'utf8');

  const preview = await startPreviewServer(outputDir, { port: 0, liveReload: false });
  t.after(async () => {
    await preview.close();
  });

  const response = await httpRequest({ port: preview.port, path: '/' });
  assert.equal(response.statusCode, 200);
  assert.match(response.body, /Standalone preview/);
  assert.doesNotMatch(response.body, /EventSource/);

  const liveReloadEndpoint = await httpRequest({ port: preview.port, path: LIVE_RELOAD_PATH });
  assert.equal(liveReloadEndpoint.statusCode, 404);
});

test('watch CLI rebuilds generated pages after content changes', async (t) => {
  const contentDir = makeTempDir();
  const outputDir = makeTempDir();
  const sourcePath = path.join(contentDir, 'index.md');
  fs.writeFileSync(sourcePath, '# First version', 'utf8');

  const child = spawn(process.execPath, ['sitegen.js', contentDir, outputDir, '--watch', '--watch-interval', '100'], {
    cwd: __dirname,
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  let stdout = '';
  let stderr = '';
  child.stdout.on('data', (chunk) => {
    stdout += chunk.toString();
  });
  child.stderr.on('data', (chunk) => {
    stderr += chunk.toString();
  });

  const closePromise = new Promise((resolve, reject) => {
    child.once('error', reject);
    child.once('close', (code, signal) => resolve({ code, signal }));
  });

  t.after(async () => {
    if (!child.killed) {
      child.kill('SIGTERM');
    }
    await closePromise;
  });

  await waitFor(() => fs.existsSync(path.join(outputDir, 'index.html')) && stdout.includes('Watching'));
  await waitFor(() => fs.readFileSync(path.join(outputDir, 'index.html'), 'utf8').includes('First version'));

  const stats = fs.statSync(sourcePath);
  fs.utimesSync(sourcePath, stats.atime, new Date(Date.now() + 1500));
  fs.writeFileSync(sourcePath, '# Second version', 'utf8');

  await waitFor(() => fs.readFileSync(path.join(outputDir, 'index.html'), 'utf8').includes('Second version'));
  assert.equal(stderr, '');
});

test('watch + serve mode broadcasts live reload events after rebuilds', async (t) => {
  const contentDir = makeTempDir();
  const outputDir = makeTempDir();
  const sourcePath = path.join(contentDir, 'index.md');
  fs.writeFileSync(sourcePath, '# First preview', 'utf8');

  const child = spawn(
    process.execPath,
    ['sitegen.js', contentDir, outputDir, '--watch', '--watch-interval', '100', '--serve', '--serve-port', '0'],
    {
      cwd: __dirname,
      stdio: ['ignore', 'pipe', 'pipe'],
    }
  );

  let stdout = '';
  let stderr = '';
  child.stdout.on('data', (chunk) => {
    stdout += chunk.toString();
  });
  child.stderr.on('data', (chunk) => {
    stderr += chunk.toString();
  });

  const closePromise = new Promise((resolve, reject) => {
    child.once('error', reject);
    child.once('close', (code, signal) => resolve({ code, signal }));
  });

  t.after(async () => {
    if (!child.killed) {
      child.kill('SIGTERM');
    }
    await closePromise;
  });

  const serverUrl = await waitFor(() => {
    const match = stdout.match(/Preview server listening at (http:\/\/127\.0\.0\.1:(\d+))/);
    return match ? match[1] : null;
  });
  const port = Number(new URL(serverUrl).port);

  await waitFor(() => stdout.includes('Watching'));
  const initialPage = await httpRequest({ port, path: '/' });
  assert.equal(initialPage.statusCode, 200);
  assert.match(initialPage.body, /First preview/);
  assert.match(initialPage.body, /EventSource/);

  let sseBuffer = '';
  const sseRequest = http.get({ host: DEFAULT_SERVE_HOST, port, path: LIVE_RELOAD_PATH, headers: { Accept: 'text/event-stream' } });
  sseRequest.on('response', (res) => {
    res.setEncoding('utf8');
    res.on('data', (chunk) => {
      sseBuffer += chunk;
    });
  });
  sseRequest.on('error', (error) => {
    throw error;
  });

  t.after(() => {
    sseRequest.destroy();
  });

  await waitFor(() => sseBuffer.includes(': connected'));

  const stats = fs.statSync(sourcePath);
  fs.utimesSync(sourcePath, stats.atime, new Date(Date.now() + 1500));
  fs.writeFileSync(sourcePath, '# Second preview', 'utf8');

  await waitFor(() => sseBuffer.includes('event: reload'));
  const refreshedPage = await httpRequest({ port, path: '/' });
  assert.match(refreshedPage.body, /Second preview/);
  assert.equal(stderr, '');
});

test('sanitizeHref still blocks unsafe protocols', () => {
  assert.equal(sanitizeHref('https://example.com'), 'https://example.com');
  assert.equal(sanitizeHref('student-projects.html'), 'student-projects.html');
  assert.equal(sanitizeHref('javascript:alert(1)'), '#');
});
