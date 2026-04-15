#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

function parseFrontMatter(source) {
  const normalized = source.replace(/^\uFEFF/, '');
  const trimmedStart = normalized.trimStart();
  const match = trimmedStart.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?/);
  if (!match) {
    return { metadata: {}, body: normalized };
  }

  const rawMeta = match[1].trim();
  const body = trimmedStart.slice(match[0].length);
  const metadata = {};

  for (const line of rawMeta.split(/\r?\n/)) {
    if (!line.trim()) continue;
    const separator = line.indexOf(':');
    if (separator === -1) {
      throw new Error(`Invalid front matter line: ${line}`);
    }

    const key = line.slice(0, separator).trim();
    const rawValue = line.slice(separator + 1).trim();
    metadata[key] = parseFrontMatterValue(rawValue);
  }

  return { metadata, body };
}

function parseFrontMatterValue(rawValue) {
  if (!rawValue) return '';

  if (rawValue.startsWith('[') && rawValue.endsWith(']')) {
    const inner = rawValue.slice(1, -1).trim();
    if (!inner) return [];
    return inner
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean)
      .map((item) => stripQuotes(item));
  }

  if (/^(true|false)$/i.test(rawValue)) {
    return rawValue.toLowerCase() === 'true';
  }

  if (/^-?\d+$/.test(rawValue)) {
    return Number(rawValue);
  }

  return stripQuotes(rawValue);
}

function stripQuotes(value) {
  if (
    (value.startsWith('"') && value.endsWith('"')) ||
    (value.startsWith("'") && value.endsWith("'"))
  ) {
    return value.slice(1, -1);
  }
  return value;
}

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function slugify(value) {
  return String(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '') || 'page';
}

function sanitizeHref(url) {
  const trimmed = String(url).trim();
  if (/^(https?:|mailto:|#|\/)/i.test(trimmed) || !trimmed.includes(':')) {
    return escapeHtml(trimmed);
  }
  return '#';
}

function replaceMarkdownLinks(html) {
  let result = '';
  let index = 0;

  while (index < html.length) {
    const labelStart = html.indexOf('[', index);
    if (labelStart === -1) {
      result += html.slice(index);
      break;
    }

    const labelEnd = html.indexOf(']', labelStart + 1);
    const urlStart = html.indexOf('(', labelEnd + 1);
    if (labelEnd === -1 || urlStart !== labelEnd + 1) {
      result += html.slice(index, labelStart + 1);
      index = labelStart + 1;
      continue;
    }

    let depth = 0;
    let urlEnd = -1;
    for (let cursor = urlStart; cursor < html.length; cursor += 1) {
      if (html[cursor] === '(') depth += 1;
      if (html[cursor] === ')') {
        depth -= 1;
        if (depth === 0) {
          urlEnd = cursor;
          break;
        }
      }
    }

    if (urlEnd === -1) {
      result += html.slice(index, labelStart + 1);
      index = labelStart + 1;
      continue;
    }

    const label = html.slice(labelStart + 1, labelEnd);
    const href = html.slice(urlStart + 1, urlEnd);
    result += html.slice(index, labelStart);
    result += `<a href="${sanitizeHref(href)}">${label}</a>`;
    index = urlEnd + 1;
  }

  return result;
}

function inlineMarkdown(text) {
  let html = escapeHtml(text);
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
  html = replaceMarkdownLinks(html);
  return html;
}

function markdownToHtml(markdown) {
  const lines = markdown.replace(/\r/g, '').split('\n');
  const parts = [];
  let paragraph = [];
  let listItems = [];

  const flushParagraph = () => {
    if (!paragraph.length) return;
    parts.push(`<p>${inlineMarkdown(paragraph.join(' '))}</p>`);
    paragraph = [];
  };

  const flushList = () => {
    if (!listItems.length) return;
    parts.push(`<ul>${listItems.map((item) => `<li>${inlineMarkdown(item)}</li>`).join('')}</ul>`);
    listItems = [];
  };

  for (const rawLine of lines) {
    const line = rawLine.trim();

    if (!line) {
      flushParagraph();
      flushList();
      continue;
    }

    const heading = /^(#{1,6})\s+(.*)$/.exec(line);
    if (heading) {
      flushParagraph();
      flushList();
      const level = heading[1].length;
      parts.push(`<h${level}>${inlineMarkdown(heading[2].trim())}</h${level}>`);
      continue;
    }

    const listMatch = /^[-*]\s+(.*)$/.exec(line);
    if (listMatch) {
      flushParagraph();
      listItems.push(listMatch[1].trim());
      continue;
    }

    flushList();
    paragraph.push(line);
  }

  flushParagraph();
  flushList();

  return parts.join('\n');
}

function renderTemplate(page, navigation, contentHtml) {
  const title = page.metadata.title || page.slug;
  const description = page.metadata.description || '';
  const tags = Array.isArray(page.metadata.tags) ? page.metadata.tags : [];
  const navHtml = navigation.length
    ? `<nav><ul>${navigation
        .map((item) => {
          const className = item.outputName === page.outputName ? ' class="active"' : '';
          return `<li><a${className} href="${escapeHtml(item.outputName)}">${escapeHtml(item.title)}</a></li>`;
        })
        .join('')}</ul></nav>`
    : '';
  const tagsHtml = tags.length
    ? `<p class="tags">${tags.map((tag) => `<span>${escapeHtml(tag)}</span>`).join('')}</p>`
    : '';

  return `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>${escapeHtml(title)}</title>
    <meta name="description" content="${escapeHtml(description)}">
    <style>
      :root { color-scheme: light dark; }
      body { font-family: system-ui, sans-serif; max-width: 860px; margin: 0 auto; padding: 2rem 1.25rem 3rem; line-height: 1.6; }
      header { margin-bottom: 2rem; }
      nav ul { list-style: none; display: flex; flex-wrap: wrap; gap: 0.75rem; padding: 0; margin: 0 0 1rem; }
      nav a { text-decoration: none; color: inherit; padding: 0.35rem 0.6rem; border: 1px solid #9994; border-radius: 999px; }
      nav a.active { font-weight: 700; border-color: #2563eb; }
      main { display: grid; gap: 1rem; }
      code { background: #9992; padding: 0.1rem 0.3rem; border-radius: 0.25rem; }
      .tags { display: flex; flex-wrap: wrap; gap: 0.5rem; }
      .tags span { font-size: 0.9rem; background: #9992; padding: 0.2rem 0.55rem; border-radius: 999px; }
      footer { margin-top: 2rem; font-size: 0.9rem; color: #666; }
    </style>
  </head>
  <body>
    <header>
      ${navHtml}
      <h1>${escapeHtml(title)}</h1>
      ${description ? `<p>${escapeHtml(description)}</p>` : ''}
      ${tagsHtml}
    </header>
    <main>
      ${contentHtml}
    </main>
    <footer>
      Built with static-site-generator.
    </footer>
  </body>
</html>`;
}

function loadPages(contentDir) {
  const entries = fs.readdirSync(contentDir, { withFileTypes: true });
  return entries
    .filter((entry) => entry.isFile() && entry.name.endsWith('.md'))
    .map((entry) => {
      const sourcePath = path.join(contentDir, entry.name);
      const raw = fs.readFileSync(sourcePath, 'utf8');
      const { metadata, body } = parseFrontMatter(raw);
      const baseName = path.basename(entry.name, '.md');
      const slug = metadata.slug || slugify(metadata.title || baseName);
      return {
        sourcePath,
        sourceName: entry.name,
        slug,
        outputName: `${slug}.html`,
        metadata,
        body,
      };
    })
    .sort((left, right) => {
      const leftOrder = Number.isFinite(left.metadata.order) ? left.metadata.order : Number.MAX_SAFE_INTEGER;
      const rightOrder = Number.isFinite(right.metadata.order) ? right.metadata.order : Number.MAX_SAFE_INTEGER;
      if (leftOrder !== rightOrder) return leftOrder - rightOrder;
      return left.slug.localeCompare(right.slug);
    });
}

function buildSite(contentDir, outputDir) {
  if (!fs.existsSync(contentDir)) {
    throw new Error(`Content directory not found: ${contentDir}`);
  }

  const pages = loadPages(contentDir);
  if (!pages.length) {
    throw new Error(`No markdown files found in: ${contentDir}`);
  }

  fs.mkdirSync(outputDir, { recursive: true });

  const navigation = pages
    .filter((page) => page.metadata.nav !== false)
    .map((page) => ({
      title: page.metadata.title || page.slug,
      outputName: page.outputName,
      order: page.metadata.order,
    }));

  for (const page of pages) {
    const contentHtml = markdownToHtml(page.body.trim());
    const html = renderTemplate(page, navigation, contentHtml);
    fs.writeFileSync(path.join(outputDir, page.outputName), html, 'utf8');
  }

  return pages.map((page) => ({
    source: page.sourceName,
    output: page.outputName,
    title: page.metadata.title || page.slug,
  }));
}

function main(argv) {
  const [contentDir, outputDir] = argv;
  if (!contentDir || !outputDir) {
    console.error('Usage: node sitegen.js <content-dir> <output-dir>');
    process.exitCode = 1;
    return;
  }

  const pages = buildSite(path.resolve(contentDir), path.resolve(outputDir));
  console.log(`Built ${pages.length} page(s):`);
  for (const page of pages) {
    console.log(`- ${page.title} -> ${page.output}`);
  }
}

if (require.main === module) {
  main(process.argv.slice(2));
}

module.exports = {
  buildSite,
  escapeHtml,
  loadPages,
  markdownToHtml,
  parseFrontMatter,
  sanitizeHref,
  slugify,
  replaceMarkdownLinks,
};
