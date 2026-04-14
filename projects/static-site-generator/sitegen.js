const fs = require('fs/promises');
const path = require('path');

function normalizeNewlines(value) {
  return String(value).replace(/\r\n/g, '\n');
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function slugify(value) {
  return String(value)
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '') || 'page';
}

function parseValue(raw) {
  const value = raw.trim();
  if (value === 'true') return true;
  if (value === 'false') return false;
  if (/^-?\d+$/.test(value)) return Number(value);
  if (value.startsWith('[') && value.endsWith(']')) {
    return value
      .slice(1, -1)
      .split(',')
      .map(item => item.trim())
      .filter(Boolean)
      .map(item => item.replace(/^['"]|['"]$/g, ''));
  }
  return value.replace(/^['"]|['"]$/g, '');
}

function parseFrontMatter(source) {
  const normalizedSource = normalizeNewlines(source);
  if (!normalizedSource.startsWith('---\n')) {
    return { data: {}, content: normalizedSource.trim() };
  }

  const end = normalizedSource.indexOf('\n---\n', 4);
  if (end === -1) {
    return { data: {}, content: normalizedSource.trim() };
  }

  const frontMatter = normalizedSource.slice(4, end).trim();
  const content = normalizedSource.slice(end + 5).trim();
  const data = {};

  for (const line of frontMatter.split('\n')) {
    if (!line.trim()) continue;
    const colonIndex = line.indexOf(':');
    if (colonIndex === -1) continue;
    const key = line.slice(0, colonIndex).trim();
    const value = line.slice(colonIndex + 1);
    data[key] = parseValue(value);
  }

  return { data, content };
}

function sanitizeHref(href) {
  const trimmed = href.trim();
  if (/^(https?:\/\/|\/|\.\/|\.\.\/|#)/i.test(trimmed)) {
    return escapeHtml(trimmed);
  }
  return '#';
}

function renderInline(text) {
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/\[(.+?)\]\((.+?)\)/g, (_, label, href) => `<a href="${sanitizeHref(href)}">${label}</a>`);
}

function markdownToHtml(md) {
  const blocks = md
    .split(/\n{2,}/)
    .map(block => block.trim())
    .filter(Boolean);

  return blocks
    .map(block => {
      const lines = block.split('\n');
      if (lines.every(line => /^- /.test(line))) {
        const items = lines
          .map(line => `  <li>${renderInline(line.slice(2).trim())}</li>`)
          .join('\n');
        return `<ul>\n${items}\n</ul>`;
      }

      if (block.startsWith('### ')) return `<h3>${renderInline(block.slice(4).trim())}</h3>`;
      if (block.startsWith('## ')) return `<h2>${renderInline(block.slice(3).trim())}</h2>`;
      if (block.startsWith('# ')) return `<h1>${renderInline(block.slice(2).trim())}</h1>`;
      return `<p>${renderInline(block.replace(/\n/g, '<br />'))}</p>`;
    })
    .join('\n');
}

function humanizeTitle(filename) {
  return filename
    .replace(/\.md$/, '')
    .replace(/[-_]+/g, ' ')
    .replace(/\b\w/g, letter => letter.toUpperCase());
}

function normalizePages(pages) {
  return [...pages].sort((a, b) => {
    const orderA = Number.isFinite(a.order) ? a.order : Number.MAX_SAFE_INTEGER;
    const orderB = Number.isFinite(b.order) ? b.order : Number.MAX_SAFE_INTEGER;
    if (orderA !== orderB) return orderA - orderB;
    return a.title.localeCompare(b.title);
  });
}

function renderNavigation(pages, currentOutputName) {
  const links = normalizePages(pages)
    .filter(page => page.nav !== false)
    .map(page => {
      const className = page.outputName === currentOutputName ? ' class="active"' : '';
      return `<a${className} href="${page.outputName}">${escapeHtml(page.title)}</a>`;
    })
    .join('');

  return `<nav>${links}</nav>`;
}

function renderTags(tags) {
  if (!Array.isArray(tags) || tags.length === 0) return '';
  const items = tags.map(tag => `<span>${escapeHtml(tag)}</span>`).join('');
  return `<div class="tags">${items}</div>`;
}

function renderPage(page, pages) {
  const title = page.title || 'Untitled Page';
  const description = page.description ? `<p class="description">${escapeHtml(page.description)}</p>` : '';
  const tags = renderTags(page.tags);
  const body = markdownToHtml(page.content);

  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${escapeHtml(title)}</title>
    <style>
      :root { color-scheme: light; }
      body { font-family: Arial, sans-serif; margin: 0; background: #f5f7fb; color: #172033; }
      header { background: #172033; color: white; padding: 2rem 1.5rem; }
      header h1 { margin: 0 0 0.5rem; }
      .description { margin: 0.75rem 0 0; max-width: 60ch; }
      nav { display: flex; flex-wrap: wrap; gap: 0.75rem; margin-top: 1rem; }
      nav a { color: #d8e7ff; text-decoration: none; font-weight: 600; }
      nav a.active { text-decoration: underline; }
      main { max-width: 800px; margin: 0 auto; padding: 1.5rem; }
      article { background: white; border-radius: 12px; padding: 1.5rem; box-shadow: 0 10px 30px rgba(23, 32, 51, 0.08); }
      code { background: #eef3ff; padding: 0.1rem 0.35rem; border-radius: 4px; }
      .tags { display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 1rem 0; }
      .tags span { background: #eef3ff; color: #244585; padding: 0.3rem 0.6rem; border-radius: 999px; font-size: 0.9rem; }
      ul { padding-left: 1.25rem; }
      footer { max-width: 800px; margin: 0 auto; padding: 0 1.5rem 2rem; color: #5a6475; }
    </style>
  </head>
  <body>
    <header>
      <h1>${escapeHtml(title)}</h1>
      ${description}
      ${renderNavigation(pages, page.outputName)}
    </header>
    <main>
      <article>
        ${tags}
        ${body}
      </article>
    </main>
    <footer>Generated by static-site-generator.</footer>
  </body>
</html>`;
}

async function loadPages(srcDir) {
  const entries = await fs.readdir(srcDir, { withFileTypes: true });
  const pages = [];

  for (const entry of entries) {
    if (!entry.isFile() || !entry.name.endsWith('.md')) continue;
    const filePath = path.join(srcDir, entry.name);
    const raw = await fs.readFile(filePath, 'utf8');
    const { data, content } = parseFrontMatter(raw);
    const title = data.title || humanizeTitle(entry.name);
    const outputName = data.slug ? `${slugify(data.slug)}.html` : entry.name.replace(/\.md$/, '.html');
    pages.push({
      ...data,
      title,
      content,
      sourceName: entry.name,
      outputName,
    });
  }

  return normalizePages(pages);
}

async function build(srcDir, outDir) {
  await fs.mkdir(outDir, { recursive: true });
  const pages = await loadPages(srcDir);

  for (const page of pages) {
    const html = renderPage(page, pages);
    await fs.writeFile(path.join(outDir, page.outputName), html);
  }

  return pages.map(page => page.outputName);
}

if (require.main === module) {
  build(process.argv[2] || 'content', process.argv[3] || 'dist').catch(err => {
    console.error(err);
    process.exit(1);
  });
}

module.exports = {
  build,
  escapeHtml,
  loadPages,
  markdownToHtml,
  parseFrontMatter,
  renderPage,
  humanizeTitle,
  slugify,
};
