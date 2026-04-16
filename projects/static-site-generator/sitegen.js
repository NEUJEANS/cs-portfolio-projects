#!/usr/bin/env node
const fs = require('fs');
const http = require('http');
const path = require('path');

const PARTIALS_DIR_NAME = '_partials';
const LIVE_RELOAD_PATH = '/__sitegen/live';
const DEFAULT_SERVE_HOST = '127.0.0.1';
const DEFAULT_SERVE_PORT = 4173;
const NOT_FOUND_OUTPUT_NAME = '404.html';

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

function toPosixPath(value) {
  return String(value).split(path.sep).join('/');
}

function isReservedContentPath(relativePath) {
  const normalized = toPosixPath(relativePath);
  return normalized === PARTIALS_DIR_NAME || normalized.startsWith(`${PARTIALS_DIR_NAME}/`);
}

function splitHref(href) {
  const value = String(href);
  const hashIndex = value.indexOf('#');
  const queryIndex = value.indexOf('?');
  let endIndex = value.length;
  if (hashIndex !== -1) endIndex = Math.min(endIndex, hashIndex);
  if (queryIndex !== -1) endIndex = Math.min(endIndex, queryIndex);

  return {
    base: value.slice(0, endIndex),
    suffix: value.slice(endIndex),
  };
}

function toOutputPath(relativeMarkdownPath, metadata = {}) {
  const normalized = toPosixPath(relativeMarkdownPath);
  if (!normalized.endsWith('.md')) {
    return normalized;
  }

  const dirname = path.posix.dirname(normalized);
  const baseName = path.posix.basename(normalized, '.md');
  const derivedName = metadata.slug || (baseName === 'index' || baseName === '404' ? baseName : slugify(metadata.title || baseName));
  const fileName = `${derivedName}.html`;
  return dirname === '.' ? fileName : path.posix.join(dirname, fileName);
}

function resolveDocumentHref(rawHref, page = {}) {
  const { base, suffix } = splitHref(rawHref);
  if (!base || /^(https?:|mailto:|#|\/)/i.test(base)) {
    return `${base}${suffix}`;
  }

  const normalizedBase = toPosixPath(base);
  if (!normalizedBase.endsWith('.md')) {
    return `${normalizedBase}${suffix}`;
  }

  const sourceName = toPosixPath(page.sourceName || '');
  const outputName = toPosixPath(page.outputName || '');
  const sourceDir = sourceName ? path.posix.dirname(sourceName) : '.';
  const outputDir = outputName ? path.posix.dirname(outputName) : '.';
  const resolvedSourcePath = path.posix.normalize(path.posix.join(sourceDir, normalizedBase));
  const targetOutputPath = toOutputPath(resolvedSourcePath);
  const relative = path.posix.relative(outputDir, targetOutputPath) || path.posix.basename(targetOutputPath);
  return `${relative}${suffix}`;
}

function replaceMarkdownImages(html, page) {
  let result = '';
  let index = 0;

  while (index < html.length) {
    const markerStart = html.indexOf('![', index);
    if (markerStart === -1) {
      result += html.slice(index);
      break;
    }

    const altEnd = html.indexOf(']', markerStart + 2);
    const urlStart = html.indexOf('(', altEnd + 1);
    if (altEnd === -1 || urlStart !== altEnd + 1) {
      result += html.slice(index, markerStart + 2);
      index = markerStart + 2;
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
      result += html.slice(index, markerStart + 2);
      index = markerStart + 2;
      continue;
    }

    const alt = html.slice(markerStart + 2, altEnd);
    const src = html.slice(urlStart + 1, urlEnd);
    result += html.slice(index, markerStart);
    result += `<img src="${sanitizeHref(resolveDocumentHref(src, page))}" alt="${alt}" loading="lazy">`;
    index = urlEnd + 1;
  }

  return result;
}

function replaceMarkdownLinks(html, page) {
  let result = '';
  let index = 0;

  while (index < html.length) {
    const labelStart = html.indexOf('[', index);
    if (labelStart === -1) {
      result += html.slice(index);
      break;
    }

    if (labelStart > 0 && html[labelStart - 1] === '!') {
      result += html.slice(index, labelStart + 1);
      index = labelStart + 1;
      continue;
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
    result += `<a href="${sanitizeHref(resolveDocumentHref(href, page))}">${label}</a>`;
    index = urlEnd + 1;
  }

  return result;
}

function inlineMarkdown(text, page) {
  let html = escapeHtml(text);
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
  html = replaceMarkdownImages(html, page);
  html = replaceMarkdownLinks(html, page);
  return html;
}

function markdownToHtml(markdown, page) {
  const lines = markdown.replace(/\r/g, '').split('\n');
  const parts = [];
  let paragraph = [];
  let bulletListItems = [];
  let orderedListItems = [];
  let orderedListStart = 1;
  let blockquoteLines = [];
  let codeFence = null;
  let codeLines = [];

  const flushParagraph = () => {
    if (!paragraph.length) return;
    parts.push(`<p>${inlineMarkdown(paragraph.join(' '), page)}</p>`);
    paragraph = [];
  };

  const flushBulletList = () => {
    if (!bulletListItems.length) return;
    parts.push(`<ul>${bulletListItems.map((item) => `<li>${inlineMarkdown(item, page)}</li>`).join('')}</ul>`);
    bulletListItems = [];
  };

  const flushOrderedList = () => {
    if (!orderedListItems.length) return;
    const startAttribute = orderedListStart !== 1 ? ` start="${orderedListStart}"` : '';
    parts.push(`<ol${startAttribute}>${orderedListItems.map((item) => `<li>${inlineMarkdown(item, page)}</li>`).join('')}</ol>`);
    orderedListItems = [];
    orderedListStart = 1;
  };

  const flushLists = () => {
    flushBulletList();
    flushOrderedList();
  };

  const flushBlockquote = () => {
    if (!blockquoteLines.length) return;
    const innerHtml = markdownToHtml(blockquoteLines.join('\n'), page);
    parts.push(`<blockquote>${innerHtml}</blockquote>`);
    blockquoteLines = [];
  };

  const flushCodeBlock = () => {
    if (codeFence === null) return;
    const languageClass = codeFence ? ` class="language-${escapeHtml(codeFence)}"` : '';
    parts.push(`<pre><code${languageClass}>${escapeHtml(codeLines.join('\n'))}</code></pre>`);
    codeFence = null;
    codeLines = [];
  };

  for (const rawLine of lines) {
    const fenceMatch = /^```\s*([^`]*)$/.exec(rawLine.trim());
    if (fenceMatch) {
      if (codeFence !== null) {
        flushCodeBlock();
      } else {
        flushParagraph();
        flushLists();
        flushBlockquote();
        codeFence = fenceMatch[1].trim();
      }
      continue;
    }

    if (codeFence !== null) {
      codeLines.push(rawLine);
      continue;
    }

    const blockquoteMatch = /^>\s?(.*)$/.exec(rawLine.trimStart());
    if (blockquoteMatch) {
      flushParagraph();
      flushLists();
      blockquoteLines.push(blockquoteMatch[1]);
      continue;
    }

    if (blockquoteLines.length) {
      flushBlockquote();
    }

    const line = rawLine.trim();

    if (!line) {
      flushParagraph();
      flushLists();
      continue;
    }

    const heading = /^(#{1,6})\s+(.*)$/.exec(line);
    if (heading) {
      flushParagraph();
      flushLists();
      const level = heading[1].length;
      parts.push(`<h${level}>${inlineMarkdown(heading[2].trim(), page)}</h${level}>`);
      continue;
    }

    const bulletListMatch = /^[-*]\s+(.*)$/.exec(line);
    if (bulletListMatch) {
      flushParagraph();
      flushOrderedList();
      bulletListItems.push(bulletListMatch[1].trim());
      continue;
    }

    const orderedListMatch = /^(\d+)\.\s+(.*)$/.exec(line);
    if (orderedListMatch) {
      flushParagraph();
      flushBulletList();
      if (!orderedListItems.length) {
        orderedListStart = Number(orderedListMatch[1]);
      }
      orderedListItems.push(orderedListMatch[2].trim());
      continue;
    }

    flushLists();
    paragraph.push(line);
  }

  flushBlockquote();
  flushParagraph();
  flushLists();
  flushCodeBlock();

  return parts.join('\n');
}

function relativeLink(fromOutputName, toOutputName) {
  const fromDir = path.posix.dirname(toPosixPath(fromOutputName));
  const target = toPosixPath(toOutputName);
  return path.posix.relative(fromDir, target) || path.posix.basename(target);
}

function isNotFoundOutputName(outputName) {
  return toPosixPath(outputName) === NOT_FOUND_OUTPUT_NAME;
}

function normalizeTags(rawTags) {
  const values = Array.isArray(rawTags) ? rawTags : [];
  const seen = new Set();
  const tags = [];

  for (const value of values) {
    const label = String(value).trim();
    if (!label) continue;
    const slug = slugify(label);
    if (seen.has(slug)) continue;
    seen.add(slug);
    tags.push({ label, slug });
  }

  return tags;
}

function buildTagCollections(pages) {
  const collections = new Map();

  for (const page of pages) {
    for (const tag of page.tags) {
      if (!collections.has(tag.slug)) {
        collections.set(tag.slug, {
          label: tag.label,
          slug: tag.slug,
          outputName: `tags/${tag.slug}.html`,
          pages: [],
        });
      }

      collections.get(tag.slug).pages.push({
        title: page.metadata.title || page.slug,
        description: page.metadata.description || '',
        outputName: page.outputName,
        sourceName: page.sourceName,
      });
    }
  }

  return Array.from(collections.values()).sort((left, right) => left.label.localeCompare(right.label));
}

function buildNavigation(pages, tagCollections) {
  const navigation = pages
    .filter((page) => page.metadata.nav !== false)
    .map((page) => ({
      title: page.metadata.title || page.slug,
      outputName: page.outputName,
      order: page.metadata.order,
    }));

  if (tagCollections.length) {
    navigation.push({
      title: 'Tags',
      outputName: 'tags/index.html',
      order: Number.MAX_SAFE_INTEGER,
      section: 'tags',
    });
  }

  return navigation;
}

function renderTagBadges(page, tagCollectionsBySlug) {
  if (!page.tags || !page.tags.length) return '';

  return `<p class="tags">${page.tags
    .map((tag) => {
      const archive = tagCollectionsBySlug.get(tag.slug);
      const href = archive ? relativeLink(page.outputName, archive.outputName) : '#';
      return `<a class="tag-pill" href="${escapeHtml(href)}">${escapeHtml(tag.label)}</a>`;
    })
    .join('')}</p>`;
}

function renderTagIndexContent(tagCollections, page) {
  return `<section class="tag-index">
  <p>Browse generated tag archive pages for portfolio themes, tools, and subject areas.</p>
  <ul class="tag-directory">${tagCollections
    .map(
      (collection) => `<li><a href="${escapeHtml(relativeLink(page.outputName, collection.outputName))}">${escapeHtml(collection.label)}</a> <span class="tag-count">${collection.pages.length} page${collection.pages.length === 1 ? '' : 's'}</span></li>`
    )
    .join('')}</ul>
</section>`;
}

function renderTagArchiveContent(collection, page) {
  return `<section class="tag-archive">
  <p><a href="${escapeHtml(relativeLink(page.outputName, 'tags/index.html'))}">← All tags</a></p>
  <ul class="tag-archive-list">${collection.pages
    .map(
      (entry) => `<li><article><h2><a href="${escapeHtml(relativeLink(page.outputName, entry.outputName))}">${escapeHtml(entry.title)}</a></h2>${entry.description ? `<p>${escapeHtml(entry.description)}</p>` : ''}<p class="tag-source">Source: <code>${escapeHtml(entry.sourceName)}</code></p></article></li>`
    )
    .join('')}</ul>
</section>`;
}

function selectFallbackHomePage(pages) {
  return pages.find((page) => page.outputName === 'index.html') || pages.find((page) => page.metadata.nav !== false) || null;
}

function renderDefaultNotFoundContent(page, pages) {
  const homePage = selectFallbackHomePage(pages);
  const homeLink = homePage ? relativeLink(page.outputName, homePage.outputName) : null;
  const homeLabel = homePage ? homePage.metadata.title || homePage.slug : 'home page';

  return `<section class="not-found">
  <p>The page you requested could not be found in this generated site.</p>
  <p>Use the navigation above to jump back into the portfolio${homeLink ? `, or return to <a href="${escapeHtml(homeLink)}">${escapeHtml(homeLabel)}</a>.` : '.'}</p>
</section>`;
}

function rootPathForPage(outputName) {
  const normalized = toPosixPath(outputName);
  const dirname = path.posix.dirname(normalized);
  if (dirname === '.' || !dirname) {
    return '';
  }

  return `${dirname.split('/').map(() => '..').join('/')}/`;
}

function loadTemplatePartials(contentDir) {
  const partialsDir = path.join(contentDir, PARTIALS_DIR_NAME);
  const partials = {
    header: null,
    footer: null,
  };

  for (const name of Object.keys(partials)) {
    const partialPath = path.join(partialsDir, `${name}.html`);
    if (fs.existsSync(partialPath) && fs.statSync(partialPath).isFile()) {
      partials[name] = fs.readFileSync(partialPath, 'utf8');
    }
  }

  return partials;
}

function renderPartial(template, context) {
  if (!template) return '';
  return template.replace(/\{\{\s*([a-zA-Z0-9_-]+)\s*\}\}/g, (match, key) => {
    if (!Object.prototype.hasOwnProperty.call(context, key)) {
      return match;
    }
    return context[key];
  });
}

function renderTemplate(page, navigation, contentHtml, tagCollectionsBySlug = new Map(), partials = {}) {
  const title = page.metadata.title || page.slug;
  const description = page.metadata.description || '';
  const navHtml = navigation.length
    ? `<nav><ul>${navigation
        .map((item) => {
          const isActive = item.outputName === page.outputName || (item.section && item.section === page.section);
          const className = isActive ? ' class="active"' : '';
          return `<li><a${className} href="${escapeHtml(relativeLink(page.outputName, item.outputName))}">${escapeHtml(item.title)}</a></li>`;
        })
        .join('')}</ul></nav>`
    : '';
  const tagsHtml = renderTagBadges(page, tagCollectionsBySlug);
  const partialContext = {
    navigation: navHtml,
    title: escapeHtml(title),
    description: escapeHtml(description),
    tags: tagsHtml,
    rootPath: escapeHtml(rootPathForPage(page.outputName)),
    outputPath: escapeHtml(page.outputName || ''),
    sourcePath: escapeHtml(page.sourceName || '(generated)'),
  };
  const headerInnerHtml = partials.header
    ? renderPartial(partials.header, partialContext)
    : `${navHtml}
      <h1>${escapeHtml(title)}</h1>
      ${description ? `<p>${escapeHtml(description)}</p>` : ''}
      ${tagsHtml}`;
  const footerInnerHtml = partials.footer
    ? renderPartial(partials.footer, partialContext)
    : 'Built with static-site-generator.';

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
      img { max-width: 100%; height: auto; border-radius: 0.75rem; }
      code { background: #9992; padding: 0.1rem 0.3rem; border-radius: 0.25rem; }
      pre { overflow-x: auto; background: #111827; color: #f9fafb; padding: 1rem; border-radius: 0.85rem; }
      pre code { display: block; background: transparent; padding: 0; border-radius: 0; }
      blockquote { margin: 0; padding: 0.25rem 1rem; border-left: 4px solid #2563eb; background: #2563eb11; border-radius: 0 0.85rem 0.85rem 0; }
      blockquote p:first-child { margin-top: 0; }
      blockquote p:last-child { margin-bottom: 0; }
      .tags { display: flex; flex-wrap: wrap; gap: 0.5rem; }
      .tag-pill { display: inline-flex; align-items: center; font-size: 0.9rem; background: #9992; padding: 0.2rem 0.55rem; border-radius: 999px; color: inherit; text-decoration: none; }
      .tag-directory, .tag-archive-list { list-style: none; padding: 0; margin: 0; display: grid; gap: 0.85rem; }
      .tag-directory li, .tag-archive-list li article, .not-found { padding: 0.9rem 1rem; border: 1px solid #9993; border-radius: 0.85rem; background: #9991; }
      .tag-directory a, .tag-archive-list a, .not-found a { color: inherit; }
      .tag-count, .tag-source { color: #666; font-size: 0.95rem; }
      .tag-archive-list h2 { margin-top: 0; margin-bottom: 0.4rem; }
      .not-found p:first-child { margin-top: 0; }
      .not-found p:last-child { margin-bottom: 0; }
      footer { margin-top: 2rem; font-size: 0.9rem; color: #666; }
    </style>
  </head>
  <body>
    <header>
      ${headerInnerHtml}
    </header>
    <main>
      ${contentHtml}
    </main>
    <footer>
      ${footerInnerHtml}
    </footer>
  </body>
</html>`;
}

function walkContentEntries(contentDir, currentDir = contentDir) {
  const entries = fs.readdirSync(currentDir, { withFileTypes: true });
  const files = [];

  for (const entry of entries) {
    const fullPath = path.join(currentDir, entry.name);
    const relativePath = path.relative(contentDir, fullPath);
    if (isReservedContentPath(relativePath)) {
      continue;
    }

    if (entry.isDirectory()) {
      files.push(...walkContentEntries(contentDir, fullPath));
      continue;
    }

    if (!entry.isFile()) continue;
    files.push({
      fullPath,
      relativePath,
    });
  }

  return files.sort((left, right) => left.relativePath.localeCompare(right.relativePath));
}

function loadPages(contentDir) {
  return walkContentEntries(contentDir)
    .filter((entry) => entry.relativePath.endsWith('.md'))
    .map((entry) => {
      const raw = fs.readFileSync(entry.fullPath, 'utf8');
      const parsed = parseFrontMatter(raw);
      const metadata = { ...parsed.metadata };
      const sourceName = toPosixPath(entry.relativePath);
      if (sourceName === '404.md') {
        if (!Object.prototype.hasOwnProperty.call(metadata, 'title')) {
          metadata.title = 'Page Not Found';
        }
        if (!Object.prototype.hasOwnProperty.call(metadata, 'description')) {
          metadata.description = 'Friendly fallback page for missing portfolio routes.';
        }
        if (!Object.prototype.hasOwnProperty.call(metadata, 'nav')) {
          metadata.nav = false;
        }
      }
      const baseName = path.basename(entry.relativePath, '.md');
      const slug = metadata.slug || slugify(metadata.title || baseName);
      return {
        sourcePath: entry.fullPath,
        sourceName,
        slug,
        outputName: toOutputPath(sourceName, metadata),
        metadata,
        tags: normalizeTags(metadata.tags),
        body: parsed.body,
      };
    })
    .sort((left, right) => {
      const leftOrder = Number.isFinite(left.metadata.order) ? left.metadata.order : Number.MAX_SAFE_INTEGER;
      const rightOrder = Number.isFinite(right.metadata.order) ? right.metadata.order : Number.MAX_SAFE_INTEGER;
      if (leftOrder !== rightOrder) return leftOrder - rightOrder;
      return left.slug.localeCompare(right.slug);
    });
}

function listStaticAssetOutputNames(contentDir) {
  return walkContentEntries(contentDir)
    .filter((entry) => !entry.relativePath.endsWith('.md'))
    .map((entry) => toPosixPath(entry.relativePath));
}

function copyStaticAssets(contentDir, outputDir) {
  const copied = [];

  for (const entry of walkContentEntries(contentDir)) {
    if (entry.relativePath.endsWith('.md')) continue;
    const destination = path.join(outputDir, entry.relativePath);
    fs.mkdirSync(path.dirname(destination), { recursive: true });
    fs.copyFileSync(entry.fullPath, destination);
    copied.push(entry.relativePath);
  }

  return copied;
}

function writeRenderedPage(outputDir, outputName, html) {
  const destination = path.join(outputDir, outputName);
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  fs.writeFileSync(destination, html, 'utf8');
}

function assertNoGeneratedPageConflicts(pages, generatedOutputNames) {
  const authoredOutputs = new Set(pages.map((page) => page.outputName));
  const conflicts = generatedOutputNames.filter((outputName) => authoredOutputs.has(outputName));
  if (conflicts.length) {
    throw new Error(`Generated tag archive path conflicts with source page output: ${conflicts.join(', ')}`);
  }
}

function assertNoGeneratedAssetConflicts(assetOutputNames, generatedOutputNames) {
  const authoredAssets = new Set(assetOutputNames);
  const conflicts = generatedOutputNames.filter((outputName) => authoredAssets.has(outputName));
  if (conflicts.length) {
    throw new Error(`Generated tag archive path conflicts with static asset output: ${conflicts.join(', ')}`);
  }
}

function buildSite(contentDir, outputDir) {
  if (!fs.existsSync(contentDir)) {
    throw new Error(`Content directory not found: ${contentDir}`);
  }

  const pages = loadPages(contentDir);
  if (!pages.length) {
    throw new Error(`No markdown files found in: ${contentDir}`);
  }

  const partials = loadTemplatePartials(contentDir);
  fs.mkdirSync(outputDir, { recursive: true });

  const tagCollections = buildTagCollections(pages);
  const tagCollectionsBySlug = new Map(tagCollections.map((collection) => [collection.slug, collection]));
  const hasAuthoredNotFoundPage = pages.some((page) => isNotFoundOutputName(page.outputName));
  const generatedOutputNames = [];
  if (!hasAuthoredNotFoundPage) {
    generatedOutputNames.push(NOT_FOUND_OUTPUT_NAME);
  }
  if (tagCollections.length) {
    generatedOutputNames.push('tags/index.html', ...tagCollections.map((collection) => collection.outputName));
  }
  if (generatedOutputNames.length) {
    assertNoGeneratedPageConflicts(pages, generatedOutputNames);
    assertNoGeneratedAssetConflicts(listStaticAssetOutputNames(contentDir), generatedOutputNames);
  }
  const navigation = buildNavigation(pages, tagCollections);
  const assets = copyStaticAssets(contentDir, outputDir);

  for (const page of pages) {
    const contentHtml = markdownToHtml(page.body.trim(), page);
    const html = renderTemplate(page, navigation, contentHtml, tagCollectionsBySlug, partials);
    writeRenderedPage(outputDir, page.outputName, html);
  }

  const generatedPages = [];
  if (!hasAuthoredNotFoundPage) {
    const notFoundPage = {
      slug: '404',
      outputName: NOT_FOUND_OUTPUT_NAME,
      metadata: {
        title: 'Page Not Found',
        description: 'Friendly fallback page for missing portfolio routes.',
        nav: false,
      },
      sourceName: '(generated)',
      tags: [],
    };

    writeRenderedPage(
      outputDir,
      notFoundPage.outputName,
      renderTemplate(notFoundPage, navigation, renderDefaultNotFoundContent(notFoundPage, pages), tagCollectionsBySlug, partials)
    );
    generatedPages.push({
      source: '(generated)',
      output: notFoundPage.outputName,
      title: notFoundPage.metadata.title,
    });
  }

  if (tagCollections.length) {
    const tagIndexPage = {
      slug: 'tags',
      outputName: 'tags/index.html',
      section: 'tags',
      metadata: {
        title: 'Tags',
        description: 'Browse portfolio pages grouped by shared front matter tags.',
      },
      tags: [],
    };

    writeRenderedPage(
      outputDir,
      tagIndexPage.outputName,
      renderTemplate(tagIndexPage, navigation, renderTagIndexContent(tagCollections, tagIndexPage), tagCollectionsBySlug, partials)
    );
    generatedPages.push({
      source: '(generated)',
      output: tagIndexPage.outputName,
      title: tagIndexPage.metadata.title,
    });

    for (const collection of tagCollections) {
      const archivePage = {
        slug: collection.slug,
        outputName: collection.outputName,
        section: 'tags',
        metadata: {
          title: `Tag: ${collection.label}`,
          description: `${collection.pages.length} page${collection.pages.length === 1 ? '' : 's'} tagged \"${collection.label}\".`,
        },
        tags: [],
      };

      writeRenderedPage(
        outputDir,
        archivePage.outputName,
        renderTemplate(archivePage, navigation, renderTagArchiveContent(collection, archivePage), tagCollectionsBySlug, partials)
      );
      generatedPages.push({
        source: '(generated)',
        output: archivePage.outputName,
        title: archivePage.metadata.title,
      });
    }
  }

  return {
    pages: [
      ...pages.map((page) => ({
        source: page.sourceName,
        output: page.outputName,
        title: page.metadata.title || page.slug,
      })),
      ...generatedPages,
    ],
    assets,
  };
}

function walkWatchFiles(contentDir, currentDir = contentDir) {
  if (!fs.existsSync(currentDir)) {
    return [];
  }

  const entries = fs.readdirSync(currentDir, { withFileTypes: true }).sort((left, right) => left.name.localeCompare(right.name));
  const files = [];

  for (const entry of entries) {
    const fullPath = path.join(currentDir, entry.name);
    if (entry.isDirectory()) {
      files.push(...walkWatchFiles(contentDir, fullPath));
      continue;
    }

    if (!entry.isFile()) continue;
    const stat = fs.statSync(fullPath);
    files.push({
      relativePath: toPosixPath(path.relative(contentDir, fullPath)),
      size: stat.size,
      mtimeMs: Math.trunc(stat.mtimeMs),
    });
  }

  return files;
}

function createWatchSnapshot(contentDir) {
  if (!fs.existsSync(contentDir)) {
    return `missing:${path.resolve(contentDir)}`;
  }

  return walkWatchFiles(contentDir)
    .map((entry) => `${entry.relativePath}:${entry.size}:${entry.mtimeMs}`)
    .join('\n');
}

function formatBuildSummary(result) {
  const lines = [`Built ${result.pages.length} page(s):`];
  for (const page of result.pages) {
    lines.push(`- ${page.title} -> ${page.output}`);
  }
  lines.push(`Copied ${result.assets.length} asset(s).`);
  return lines.join('\n');
}

function buildWithLogging(contentDir, outputDir, reason) {
  const timestamp = new Date().toISOString();

  try {
    const result = buildSite(contentDir, outputDir);
    console.log(`[${timestamp}] ${reason} succeeded.`);
    console.log(formatBuildSummary(result));
    return { ok: true, result };
  } catch (error) {
    console.error(`[${timestamp}] ${reason} failed.`);
    console.error(error.stack || error.message);
    return { ok: false, error };
  }
}

function parseWatchInterval(rawValue) {
  const parsed = Number(rawValue);
  if (!Number.isInteger(parsed) || parsed < 50) {
    throw new Error('Watch interval must be an integer >= 50 milliseconds.');
  }
  return parsed;
}

function parseServePort(rawValue) {
  const parsed = Number(rawValue);
  if (!Number.isInteger(parsed) || parsed < 0 || parsed > 65535) {
    throw new Error('Serve port must be an integer between 0 and 65535.');
  }
  return parsed;
}

function parseCliArgs(argv) {
  const positional = [];
  const options = {
    help: false,
    watch: false,
    watchIntervalMs: 500,
    serve: false,
    servePort: DEFAULT_SERVE_PORT,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];

    if (arg === '--help' || arg === '-h') {
      options.help = true;
      continue;
    }

    if (arg === '--watch' || arg === '-w') {
      options.watch = true;
      continue;
    }

    if (arg === '--serve' || arg === '-s') {
      options.serve = true;
      continue;
    }

    if (arg === '--watch-interval') {
      const value = argv[index + 1];
      if (value === undefined) {
        throw new Error('Missing value for --watch-interval.');
      }
      options.watchIntervalMs = parseWatchInterval(value);
      index += 1;
      continue;
    }

    if (arg.startsWith('--watch-interval=')) {
      options.watchIntervalMs = parseWatchInterval(arg.split('=')[1]);
      continue;
    }

    if (arg === '--serve-port') {
      const value = argv[index + 1];
      if (value === undefined) {
        throw new Error('Missing value for --serve-port.');
      }
      options.servePort = parseServePort(value);
      index += 1;
      continue;
    }

    if (arg.startsWith('--serve-port=')) {
      options.servePort = parseServePort(arg.split('=')[1]);
      continue;
    }

    positional.push(arg);
  }

  return {
    contentDir: positional[0],
    outputDir: positional[1],
    options,
  };
}

function createLiveReloadClientSnippet() {
  return `<script>
(() => {
  if (!('EventSource' in window)) return;
  const source = new EventSource('${LIVE_RELOAD_PATH}');
  source.addEventListener('reload', () => {
    window.location.reload();
  });
})();
</script>`;
}

function injectLiveReloadClient(html) {
  const snippet = createLiveReloadClientSnippet();
  if (/<\/body>/i.test(html)) {
    return html.replace(/<\/body>/i, `${snippet}\n  </body>`);
  }
  return `${html}\n${snippet}`;
}

function normalizePreviewPathname(requestUrl) {
  const url = new URL(requestUrl, 'http://127.0.0.1');
  const pathname = decodeURIComponent(url.pathname || '/');
  const segments = pathname.split('/').filter(Boolean);
  if (segments.some((segment) => segment === '.' || segment === '..')) {
    return null;
  }
  return segments.join(path.sep);
}

function resolvePreviewRequestPath(outputDir, requestUrl) {
  const relativePath = normalizePreviewPathname(requestUrl);
  if (relativePath === null) {
    return null;
  }

  const candidates = [];
  if (!relativePath) {
    candidates.push('index.html');
  } else if (path.extname(relativePath)) {
    candidates.push(relativePath);
  } else {
    candidates.push(`${relativePath}.html`, path.join(relativePath, 'index.html'));
  }

  const resolvedOutputDir = path.resolve(outputDir);
  for (const candidate of candidates) {
    const absolute = path.resolve(resolvedOutputDir, candidate);
    if (absolute !== resolvedOutputDir && !absolute.startsWith(`${resolvedOutputDir}${path.sep}`)) {
      continue;
    }
    if (fs.existsSync(absolute) && fs.statSync(absolute).isFile()) {
      return absolute;
    }
  }

  return null;
}

function detectContentType(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const types = {
    '.css': 'text/css; charset=utf-8',
    '.gif': 'image/gif',
    '.html': 'text/html; charset=utf-8',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.js': 'application/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.md': 'text/markdown; charset=utf-8',
    '.pdf': 'application/pdf',
    '.png': 'image/png',
    '.svg': 'image/svg+xml',
    '.txt': 'text/plain; charset=utf-8',
    '.webp': 'image/webp',
  };
  return types[ext] || 'application/octet-stream';
}

function applyPreviewPlaceholders(html, requestUrl, statusCode) {
  const request = new URL(requestUrl, 'http://127.0.0.1');
  let requestedPath = request.pathname || '/';
  try {
    requestedPath = decodeURIComponent(requestedPath);
  } catch {
    requestedPath = request.pathname || '/';
  }
  const requestedUrl = `${requestedPath}${request.search || ''}${request.hash || ''}`;
  const replacements = {
    requestedPath: escapeHtml(requestedPath),
    requestedUrl: escapeHtml(requestedUrl),
    statusCode: escapeHtml(String(statusCode)),
  };

  return html.replace(/\{\{\s*(requestedPath|requestedUrl|statusCode)\s*\}\}/g, (match, key) => replacements[key] || match);
}

function resolvePreviewNotFoundPath(outputDir) {
  const candidate = path.resolve(outputDir, NOT_FOUND_OUTPUT_NAME);
  if (!fs.existsSync(candidate) || !fs.statSync(candidate).isFile()) {
    return null;
  }
  return candidate;
}

function sendPreviewFile(res, request, filePath, options = {}) {
  const statusCode = options.statusCode || 200;
  const liveReload = options.liveReload === true;
  const previewPlaceholders = options.previewPlaceholders === true;
  const contentType = detectContentType(filePath);
  const raw = fs.readFileSync(filePath);

  if (contentType.startsWith('text/html')) {
    let html = raw.toString('utf8');
    if (previewPlaceholders) {
      html = applyPreviewPlaceholders(html, request.url || '/', statusCode);
    }
    if (liveReload) {
      html = injectLiveReloadClient(html);
    }
    res.writeHead(statusCode, {
      'Cache-Control': 'no-cache',
      'Content-Length': Buffer.byteLength(html),
      'Content-Type': contentType,
    });
    if (request.method === 'HEAD') {
      res.end();
      return;
    }
    res.end(html);
    return;
  }

  res.writeHead(statusCode, {
    'Content-Length': raw.length,
    'Content-Type': contentType,
  });
  if (request.method === 'HEAD') {
    res.end();
    return;
  }
  res.end(raw);
}

function startPreviewServer(outputDir, options = {}) {
  const host = options.host || DEFAULT_SERVE_HOST;
  const port = options.port ?? DEFAULT_SERVE_PORT;
  const liveReload = options.liveReload !== false;
  const clients = new Set();
  const server = http.createServer((req, res) => {
    if (!req.url) {
      res.writeHead(400, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('Bad request');
      return;
    }

    if (req.method !== 'GET' && req.method !== 'HEAD') {
      res.writeHead(405, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('Method not allowed');
      return;
    }

    const parsedUrl = new URL(req.url, 'http://127.0.0.1');
    if (liveReload && parsedUrl.pathname === LIVE_RELOAD_PATH) {
      res.writeHead(200, {
        'Cache-Control': 'no-cache',
        Connection: 'keep-alive',
        'Content-Type': 'text/event-stream',
      });
      res.write(': connected\n\n');
      clients.add(res);
      req.on('close', () => {
        clients.delete(res);
      });
      return;
    }

    const filePath = resolvePreviewRequestPath(outputDir, req.url);
    if (!filePath) {
      const notFoundPath = resolvePreviewNotFoundPath(outputDir);
      if (notFoundPath) {
        sendPreviewFile(res, req, notFoundPath, {
          statusCode: 404,
          liveReload,
          previewPlaceholders: true,
        });
        return;
      }

      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      if (req.method === 'HEAD') {
        res.end();
        return;
      }
      res.end('Not found');
      return;
    }

    sendPreviewFile(res, req, filePath, {
      statusCode: 200,
      liveReload,
    });
  });

  const heartbeat = setInterval(() => {
    for (const client of clients) {
      client.write(': ping\n\n');
    }
  }, 15000);
  if (typeof heartbeat.unref === 'function') {
    heartbeat.unref();
  }

  return new Promise((resolve, reject) => {
    const handleError = (error) => {
      clearInterval(heartbeat);
      reject(error);
    };

    server.once('error', handleError);
    server.listen(port, host, () => {
      server.off('error', handleError);
      const address = server.address();
      const resolvedPort = typeof address === 'object' && address ? address.port : port;
      const resolvedHost = typeof address === 'object' && address && address.address ? address.address : host;
      const url = `http://${resolvedHost}:${resolvedPort}`;
      console.log(
        `[${new Date().toISOString()}] Preview server listening at ${url}${liveReload ? ' with live reload.' : '.'}`
      );

      resolve({
        host: resolvedHost,
        port: resolvedPort,
        url,
        broadcastReload(reason = 'content-change') {
          const payload = JSON.stringify({ reason, time: new Date().toISOString() });
          for (const client of clients) {
            client.write(`event: reload\ndata: ${payload}\n\n`);
          }
        },
        close() {
          clearInterval(heartbeat);
          for (const client of clients) {
            client.end();
          }
          clients.clear();
          return new Promise((closeResolve, closeReject) => {
            server.close((error) => {
              if (error) {
                closeReject(error);
                return;
              }
              closeResolve();
            });
          });
        },
      });
    });
  });
}

function watchSite(contentDir, outputDir, options = {}) {
  const intervalMs = options.watchIntervalMs || 500;
  const onBuildSuccess = typeof options.onBuildSuccess === 'function' ? options.onBuildSuccess : null;
  const onStop = typeof options.onStop === 'function' ? options.onStop : null;
  let lastSnapshot = createWatchSnapshot(contentDir);

  if (!options.skipInitialBuild) {
    const initialBuild = buildWithLogging(contentDir, outputDir, 'Initial build');
    if (initialBuild.ok && onBuildSuccess) {
      onBuildSuccess({ reason: 'initial-build', result: initialBuild.result });
    }
  }

  console.log(`[${new Date().toISOString()}] Watching ${contentDir} every ${intervalMs}ms for changes. Press Ctrl+C to stop.`);

  const timer = setInterval(() => {
    const nextSnapshot = createWatchSnapshot(contentDir);
    if (nextSnapshot === lastSnapshot) {
      return;
    }

    lastSnapshot = nextSnapshot;
    console.log(`[${new Date().toISOString()}] Change detected. Rebuilding...`);
    const rebuild = buildWithLogging(contentDir, outputDir, 'Rebuild');
    if (rebuild.ok && onBuildSuccess) {
      onBuildSuccess({ reason: 'rebuild', result: rebuild.result });
    }
  }, intervalMs);

  let stopping = false;
  const stopWatching = () => {
    if (stopping) return;
    stopping = true;
    clearInterval(timer);
    Promise.resolve(onStop ? onStop() : undefined)
      .catch(() => undefined)
      .finally(() => {
        console.log(`\n[${new Date().toISOString()}] Watch mode stopped.`);
        process.exit(0);
      });
  };

  process.once('SIGINT', stopWatching);
  process.once('SIGTERM', stopWatching);
}

function installServeShutdown(preview) {
  let stopping = false;
  const stop = () => {
    if (stopping) return;
    stopping = true;
    Promise.resolve(preview.close())
      .catch(() => undefined)
      .finally(() => {
        console.log(`\n[${new Date().toISOString()}] Preview server stopped.`);
        process.exit(0);
      });
  };

  process.once('SIGINT', stop);
  process.once('SIGTERM', stop);
}

async function main(argv) {
  let parsed;

  try {
    parsed = parseCliArgs(argv);
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
    return;
  }

  const { contentDir, outputDir, options } = parsed;
  if (options.help || !contentDir || !outputDir) {
    console.error(
      'Usage: node sitegen.js <content-dir> <output-dir> [--watch] [--watch-interval <ms>] [--serve] [--serve-port <port>]'
    );
    process.exitCode = options.help ? 0 : 1;
    return;
  }

  const resolvedContentDir = path.resolve(contentDir);
  const resolvedOutputDir = path.resolve(outputDir);

  if (options.watch) {
    const initialOutcome = buildWithLogging(resolvedContentDir, resolvedOutputDir, 'Initial build');
    const preview = options.serve
      ? await startPreviewServer(resolvedOutputDir, {
          host: DEFAULT_SERVE_HOST,
          port: options.servePort,
          liveReload: true,
        })
      : null;

    watchSite(resolvedContentDir, resolvedOutputDir, {
      skipInitialBuild: true,
      watchIntervalMs: options.watchIntervalMs,
      onBuildSuccess: preview ? ({ reason }) => preview.broadcastReload(reason) : undefined,
      onStop: preview ? () => preview.close() : undefined,
    });

    if (!initialOutcome.ok) {
      process.exitCode = 1;
    }
    return;
  }

  const outcome = buildWithLogging(resolvedContentDir, resolvedOutputDir, 'Build');
  if (!outcome.ok) {
    process.exitCode = 1;
    return;
  }

  if (options.serve) {
    const preview = await startPreviewServer(resolvedOutputDir, {
      host: DEFAULT_SERVE_HOST,
      port: options.servePort,
      liveReload: false,
    });
    installServeShutdown(preview);
    return;
  }
}

if (require.main === module) {
  main(process.argv.slice(2)).catch((error) => {
    console.error(error.stack || error.message);
    process.exit(1);
  });
}

module.exports = {
  DEFAULT_SERVE_HOST,
  DEFAULT_SERVE_PORT,
  LIVE_RELOAD_PATH,
  NOT_FOUND_OUTPUT_NAME,
  PARTIALS_DIR_NAME,
  applyPreviewPlaceholders,
  assertNoGeneratedAssetConflicts,
  assertNoGeneratedPageConflicts,
  buildNavigation,
  buildSite,
  buildTagCollections,
  buildWithLogging,
  copyStaticAssets,
  createLiveReloadClientSnippet,
  createWatchSnapshot,
  detectContentType,
  escapeHtml,
  formatBuildSummary,
  injectLiveReloadClient,
  isNotFoundOutputName,
  isReservedContentPath,
  listStaticAssetOutputNames,
  loadPages,
  loadTemplatePartials,
  markdownToHtml,
  normalizePreviewPathname,
  normalizeTags,
  parseCliArgs,
  parseFrontMatter,
  parseServePort,
  parseWatchInterval,
  relativeLink,
  renderDefaultNotFoundContent,
  renderPartial,
  replaceMarkdownImages,
  replaceMarkdownLinks,
  resolveDocumentHref,
  resolvePreviewNotFoundPath,
  resolvePreviewRequestPath,
  rootPathForPage,
  sanitizeHref,
  selectFallbackHomePage,
  sendPreviewFile,
  slugify,
  startPreviewServer,
  toOutputPath,
  walkContentEntries,
  walkWatchFiles,
  watchSite,
};
