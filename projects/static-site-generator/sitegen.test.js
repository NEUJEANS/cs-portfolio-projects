const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs/promises');
const os = require('os');
const path = require('path');
const { markdownToHtml, build } = require('./sitegen');

test('markdownToHtml renders headings and paragraphs', () => {
  const html = markdownToHtml('# Title\n\nHello **world**');
  assert.match(html, /<h1>Title<\/h1>/);
  assert.match(html, /<strong>world<\/strong>/);
});

test('build writes html files', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'sitegen-'));
  const src = path.join(tmp, 'content');
  const out = path.join(tmp, 'dist');
  await fs.mkdir(src);
  await fs.writeFile(path.join(src, 'index.md'), '# Home');
  await build(src, out);
  const html = await fs.readFile(path.join(out, 'index.html'), 'utf8');
  assert.match(html, /Home/);
});
