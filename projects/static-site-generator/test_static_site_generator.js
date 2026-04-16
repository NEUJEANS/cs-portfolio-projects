const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');

const {
  buildSite,
  markdownToHtml,
  parseFrontMatter,
  sanitizeHref,
  slugify,
} = require('./sitegen');

function makeTempDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'sitegen-'));
}

test('parseFrontMatter extracts metadata types and body', () => {
  const doc = [
    '---',
    'title: Home',
    'order: 1',
    'nav: true',
    'tags: [node, portfolio]',
    '---',
    '# Hello',
  ].join('\n');

  const { metadata, body } = parseFrontMatter(doc);
  assert.equal(metadata.title, 'Home');
  assert.equal(metadata.order, 1);
  assert.equal(metadata.nav, true);
  assert.deepEqual(metadata.tags, ['node', 'portfolio']);
  assert.match(body, /# Hello/);
});

test('markdownToHtml handles headings paragraphs lists blockquotes and inline formatting', () => {
  const html = markdownToHtml(`# Title
Paragraph with **bold**, *italics*, [link](https://example.com), and \`code\`.

- alpha
- beta

2. ship docs
3. publish demos

> quote line one
>
> quote line two`);

  assert.match(html, /<h1>Title<\/h1>/);
  assert.match(html, /<strong>bold<\/strong>/);
  assert.match(html, /<em>italics<\/em>/);
  assert.match(html, /<a href="https:\/\/example.com">link<\/a>/);
  assert.match(html, /<code>code<\/code>/);
  assert.match(html, /<ul><li>alpha<\/li><li>beta<\/li><\/ul>/);
  assert.match(html, /<ol start="2"><li>ship docs<\/li><li>publish demos<\/li><\/ol>/);
  assert.match(html, /<blockquote><p>quote line one<\/p>\s*<p>quote line two<\/p><\/blockquote>/);
});

test('buildSite renders nested navigation and relative markdown links', () => {
  const contentDir = makeTempDir();
  const outputDir = makeTempDir();
  fs.mkdirSync(path.join(contentDir, 'guides'), { recursive: true });

  fs.writeFileSync(
    path.join(contentDir, 'home.md'),
    `---
title: Home
order: 1
description: Landing page
nav: true
---
# Welcome
See the [guide](guides/setup.md).`,
    'utf8'
  );

  fs.writeFileSync(
    path.join(contentDir, 'guides', 'setup.md'),
    `---
title: Setup Guide
order: 2
slug: setup
tags: [algorithms, systems]
---
# Setup
1. Install Node
2. Build the site

> Quote callout for the guide.

Return [home](../home.md).`,
    'utf8'
  );

  const result = buildSite(contentDir, outputDir);
  assert.equal(result.pages.length, 2);
  assert.deepEqual(result.assets, []);

  const homeHtml = fs.readFileSync(path.join(outputDir, 'home.html'), 'utf8');
  const guideHtml = fs.readFileSync(path.join(outputDir, 'guides', 'setup.html'), 'utf8');

  assert.match(homeHtml, /<a class="active" href="home.html">Home<\/a>/);
  assert.match(homeHtml, /<a href="guides\/setup.html">Setup Guide<\/a>/);
  assert.match(homeHtml, /href="guides\/setup.html">guide<\/a>/i);
  assert.match(guideHtml, /<a href="\.\.\/home.html">Home<\/a>/);
  assert.match(guideHtml, /<a class="active" href="setup.html">Setup Guide<\/a>/);
  assert.match(guideHtml, /<ol><li>Install Node<\/li><li>Build the site<\/li><\/ol>/);
  assert.match(guideHtml, /<blockquote><p>Quote callout for the guide\.<\/p><\/blockquote>/);
  assert.match(guideHtml, /href="\.\.\/home.html">home<\/a>/i);
  assert.match(guideHtml, /<span>algorithms<\/span><span>systems<\/span>/);
});

test('parseFrontMatter accepts leading whitespace and CRLF front matter fences', () => {
  const doc = ['   ---', 'title: Windows Home', 'order: 2', '---', 'Body line'].join('\r\n');
  const { metadata, body } = parseFrontMatter(doc);
  assert.equal(metadata.title, 'Windows Home');
  assert.equal(metadata.order, 2);
  assert.equal(body, 'Body line');
});

test('sanitizeHref blocks unsafe protocols in markdown links', () => {
  assert.equal(sanitizeHref('https://example.com'), 'https://example.com');
  assert.equal(sanitizeHref('student-projects.html'), 'student-projects.html');
  assert.equal(sanitizeHref('javascript:alert(1)'), '#');
});

test('markdownToHtml consumes full link targets with nested parentheses', () => {
  const html = markdownToHtml('[blocked](javascript:alert(1)) and [safe](https://example.com/path_(draft))');
  assert.match(html, /<a href="#">blocked<\/a>/);
  assert.match(html, /<a href="https:\/\/example.com\/path_\(draft\)">safe<\/a>/);
  assert.doesNotMatch(html, /blocked<\/a>\)/);
});

test('slugify normalizes titles into clean filenames', () => {
  assert.equal(slugify(' My Cool Portfolio Page! '), 'my-cool-portfolio-page');
  assert.equal(slugify('###'), 'page');
});

test('buildSite rejects missing content or empty input', () => {
  const missing = path.join(os.tmpdir(), 'sitegen-nope');
  assert.throws(() => buildSite(missing, makeTempDir()), /Content directory not found/);

  const emptyContentDir = makeTempDir();
  assert.throws(() => buildSite(emptyContentDir, makeTempDir()), /No markdown files found/);
});
