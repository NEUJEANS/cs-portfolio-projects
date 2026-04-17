#!/usr/bin/env node
const fs = require('fs');
const http = require('http');
const path = require('path');

const PARTIALS_DIR_NAME = '_partials';
const SITE_CONFIG_NAME = '_site.json';
const LIVE_RELOAD_PATH = '/__sitegen/live';
const DEFAULT_SERVE_HOST = '127.0.0.1';
const DEFAULT_SERVE_PORT = 4173;
const NOT_FOUND_OUTPUT_NAME = '404.html';
const ARCHIVE_INDEX_OUTPUT_NAME = 'archives/index.html';
const SITEMAP_OUTPUT_NAME = 'sitemap.xml';
const RSS_OUTPUT_NAME = 'rss.xml';
const MONTH_LABELS = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
];
const CALLOUT_DEFINITIONS = {
  note: { label: 'Note', icon: 'ℹ', tone: 'note' },
  reviewer: { label: 'Reviewer note', icon: '👀', tone: 'reviewer' },
  architecture: { label: 'Architecture note', icon: '🏗️', tone: 'architecture' },
  performance: { label: 'Performance note', icon: '⚡', tone: 'performance' },
  tradeoff: { label: 'Trade-off', icon: '⚖️', tone: 'tradeoff' },
  testing: { label: 'Testing note', icon: '🧪', tone: 'testing' },
  tip: { label: 'Tip', icon: '💡', tone: 'tip' },
  warning: { label: 'Warning', icon: '⚠️', tone: 'warning' },
};
const COMPARISON_PANEL_DEFINITIONS = {
  before: { label: 'Before', eyebrow: 'Baseline', tone: 'before' },
  after: { label: 'After', eyebrow: 'Improved', tone: 'after' },
  delta: { label: 'Delta', eyebrow: 'Impact', tone: 'delta' },
};

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

function escapeXml(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}

function normalizeSiteUrl(rawValue) {
  const trimmed = String(rawValue || '').trim();
  if (!trimmed) {
    throw new Error(`Site config must include a non-empty "siteUrl".`);
  }

  let parsed;
  try {
    parsed = new URL(trimmed);
  } catch {
    throw new Error(`Invalid siteUrl in ${SITE_CONFIG_NAME}: ${trimmed}`);
  }

  if (!/^https?:$/.test(parsed.protocol)) {
    throw new Error(`siteUrl in ${SITE_CONFIG_NAME} must use http or https: ${trimmed}`);
  }

  parsed.hash = '';
  parsed.search = '';
  parsed.pathname = parsed.pathname.replace(/\/+$/, '');
  if (!parsed.pathname) {
    parsed.pathname = '/';
  } else if (!parsed.pathname.endsWith('/')) {
    parsed.pathname = `${parsed.pathname}/`;
  }

  return parsed.toString();
}

function pageOutputToPublicHref(outputName) {
  const normalized = toPosixPath(outputName);
  if (!normalized || normalized === 'index.html') {
    return '';
  }

  if (normalized.endsWith('/index.html')) {
    return normalized.slice(0, -'index.html'.length);
  }

  return normalized;
}

function buildAbsoluteSiteUrl(siteUrl, outputName) {
  return new URL(pageOutputToPublicHref(outputName), normalizeSiteUrl(siteUrl)).toString();
}

function loadSiteConfig(contentDir) {
  const configPath = path.join(contentDir, SITE_CONFIG_NAME);
  if (!fs.existsSync(configPath)) {
    return null;
  }

  if (!fs.statSync(configPath).isFile()) {
    throw new Error(`Site config path is not a file: ${configPath}`);
  }

  let parsed;
  try {
    parsed = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  } catch (error) {
    throw new Error(`Invalid JSON in ${SITE_CONFIG_NAME}: ${error.message}`);
  }

  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    throw new Error(`${SITE_CONFIG_NAME} must contain a JSON object.`);
  }

  return {
    siteUrl: normalizeSiteUrl(parsed.siteUrl),
    title: typeof parsed.title === 'string' ? parsed.title.trim() : '',
    description: typeof parsed.description === 'string' ? parsed.description.trim() : '',
    language: typeof parsed.language === 'string' && parsed.language.trim() ? parsed.language.trim() : 'en-us',
    copyright: typeof parsed.copyright === 'string' ? parsed.copyright.trim() : '',
  };
}

function isReservedContentPath(relativePath) {
  const normalized = toPosixPath(relativePath);
  return normalized === SITE_CONFIG_NAME || normalized === PARTIALS_DIR_NAME || normalized.startsWith(`${PARTIALS_DIR_NAME}/`);
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

function parseNamedFields(rawValue = '') {
  const fields = {};
  const fieldPattern = /([a-zA-Z0-9_-]+)=(\".*?\"|'.*?'|[^\s]+)/g;

  for (const match of String(rawValue).matchAll(fieldPattern)) {
    const key = match[1].toLowerCase();
    const value = stripQuotes(match[2]);
    if (value) {
      fields[key] = value;
    }
  }

  return fields;
}

function parseCodeFenceInfo(rawInfo = '') {
  const info = {
    language: '',
    title: '',
  };

  const trimmed = String(rawInfo).trim();
  if (!trimmed) {
    return info;
  }

  const languageMatch = /^([^\s=]+)(?:\s+|$)/.exec(trimmed);
  let remainder = trimmed;
  if (languageMatch) {
    info.language = stripQuotes(languageMatch[1]).toLowerCase();
    remainder = trimmed.slice(languageMatch[0].length).trim();
  }

  for (const [key, value] of Object.entries(parseNamedFields(remainder))) {
    if (key === 'title' || key === 'file' || key === 'filename') {
      info.title = value;
    } else {
      info[key] = value;
    }
  }

  return info;
}

function parseComparisonFenceInfo(rawInfo = '') {
  const fields = parseNamedFields(rawInfo);
  return {
    title: fields.title || '',
    summary: fields.summary || fields.description || '',
  };
}

function formatCodeLanguageLabel(language) {
  const normalized = String(language || '').trim().toLowerCase();
  const labels = {
    bash: 'Bash',
    console: 'Console',
    css: 'CSS',
    html: 'HTML',
    javascript: 'JavaScript',
    js: 'JavaScript',
    json: 'JSON',
    md: 'Markdown',
    markdown: 'Markdown',
    py: 'Python',
    python: 'Python',
    sh: 'Shell',
    sql: 'SQL',
    text: 'Text',
    ts: 'TypeScript',
    typescript: 'TypeScript',
    xml: 'XML',
    yaml: 'YAML',
    yml: 'YAML',
  };

  return labels[normalized] || (normalized ? normalized[0].toUpperCase() + normalized.slice(1) : 'Plain text');
}

function createCodeBlockEnhancementSnippet() {
  return `<script>
(() => {
  const resetTimers = new WeakMap();

  function getCodeText(figure) {
    return Array.from(figure.querySelectorAll('.code-block__line-content'))
      .map((line) => line.textContent || '')
      .join('\\n');
  }

  async function copyText(text) {
    if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
      await navigator.clipboard.writeText(text);
      return;
    }

    const helper = document.createElement('textarea');
    helper.value = text;
    helper.setAttribute('readonly', '');
    helper.setAttribute('aria-hidden', 'true');
    helper.style.position = 'fixed';
    helper.style.left = '-9999px';
    helper.style.top = '0';
    helper.style.opacity = '0';
    helper.style.pointerEvents = 'none';
    document.body.appendChild(helper);
    helper.focus();
    helper.select();
    helper.setSelectionRange(0, helper.value.length);

    let copied = false;
    try {
      copied = document.execCommand('copy');
    } finally {
      helper.remove();
    }

    if (!copied) {
      throw new Error('Copy command failed.');
    }
  }

  function resetFeedback(button, status) {
    const existingTimer = resetTimers.get(button);
    if (existingTimer) {
      clearTimeout(existingTimer);
    }

    const timer = window.setTimeout(() => {
      button.textContent = 'Copy';
      button.dataset.copyState = 'idle';
      status.textContent = '';
      resetTimers.delete(button);
    }, 2200);

    resetTimers.set(button, timer);
  }

  document.addEventListener('click', async (event) => {
    const button = event.target.closest('.code-block__copy');
    if (!button) return;

    const figure = button.closest('.code-block');
    const status = figure ? figure.querySelector('.code-block__status') : null;
    if (!figure || !status) return;

    event.preventDefault();
    const text = getCodeText(figure);
    if (!text) {
      button.dataset.copyState = 'error';
      button.textContent = 'Copy failed';
      status.textContent = 'Nothing to copy from this code sample.';
      resetFeedback(button, status);
      return;
    }

    button.disabled = true;
    button.dataset.copyState = 'working';
    button.textContent = 'Copying…';
    status.textContent = '';

    try {
      await copyText(text);
      button.dataset.copyState = 'success';
      button.textContent = 'Copied';
      status.textContent = 'Code sample copied to clipboard.';
    } catch (error) {
      button.dataset.copyState = 'error';
      button.textContent = 'Copy failed';
      status.textContent = 'Copy unavailable in this browser context.';
    } finally {
      button.disabled = false;
      resetFeedback(button, status);
    }
  });
})();
</script>`;
}

function renderCodeBlock(codeLines, codeFence) {
  const info = typeof codeFence === 'string' ? parseCodeFenceInfo(codeFence) : codeFence || { language: '', title: '' };
  const language = info.language || '';
  const title = info.title || '';
  const languageLabel = formatCodeLanguageLabel(language);
  const lineCount = codeLines.length;
  const lineLabel = `${lineCount} line${lineCount === 1 ? '' : 's'}`;
  const ariaLabel = [title, languageLabel].filter(Boolean).join(' — ') || 'Code sample';
  const copyTargetLabel = title || (language ? `${languageLabel} code sample` : 'code sample');
  const codeClass = language ? ` class="language-${escapeHtml(language)}"` : '';
  const metaBits = [];

  if (title) {
    metaBits.push(`<span class="code-block__title">${escapeHtml(title)}</span>`);
  }
  metaBits.push(`<span class="code-block__language">${escapeHtml(languageLabel)}</span>`);
  metaBits.push(`<span class="code-block__line-count">${lineLabel}</span>`);
  metaBits.push('<span class="code-block__meta-spacer"></span>');
  metaBits.push(`<span class="code-block__actions"><span class="code-block__status" role="status" aria-live="polite" aria-atomic="true"></span><button type="button" class="code-block__copy" data-copy-state="idle" aria-label="${escapeHtml(`Copy ${copyTargetLabel} to clipboard`)}">Copy</button></span>`);

  const linesHtml = codeLines
    .map((line, index) => {
      const content = line.length ? escapeHtml(line) : '&nbsp;';
      return `<span class="code-block__line" data-line="${index + 1}"><span class="code-block__line-content">${content}</span></span>`;
    })
    .join('\n');

  return `<figure class="code-block"><figcaption class="code-block__meta">${metaBits.join('')}</figcaption><pre aria-label="${escapeHtml(ariaLabel)}"><code${codeClass}>${linesHtml}</code></pre></figure>`;
}

function normalizeCalloutType(value) {
  return String(value || '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-');
}

function resolveCalloutDefinition(rawType) {
  const normalized = normalizeCalloutType(rawType);
  return normalized ? { type: normalized, ...(CALLOUT_DEFINITIONS[normalized] || {}) } : null;
}

function parseCalloutMarker(line) {
  const match = /^\[!([A-Za-z0-9_-]+)\](?:\s+(.*))?$/.exec(String(line || '').trim());
  if (!match) {
    return null;
  }

  const definition = resolveCalloutDefinition(match[1]);
  if (!definition || !definition.label) {
    return null;
  }

  return {
    ...definition,
    title: (match[2] || '').trim(),
  };
}

function trimBlankLines(lines) {
  const normalizedLines = Array.isArray(lines) ? [...lines] : [];

  while (normalizedLines.length && !normalizedLines[0].trim()) {
    normalizedLines.shift();
  }
  while (normalizedLines.length && !normalizedLines[normalizedLines.length - 1].trim()) {
    normalizedLines.pop();
  }

  return normalizedLines;
}

function renderCallout(marker, bodyLines, page) {
  const titleHtml = marker.title ? `<p class="callout__title">${inlineMarkdown(marker.title, page)}</p>` : '';
  const bodyHtml = bodyLines.length ? `<div class="callout__body">${markdownToHtml(bodyLines.join('\n'), page)}</div>` : '';
  const tone = escapeHtml(marker.tone || marker.type || 'note');
  const type = escapeHtml(marker.type || 'note');

  return `<aside class="callout callout--${tone}" data-callout-type="${type}"><div class="callout__header"><p class="callout__eyebrow"><span class="callout__icon" aria-hidden="true">${escapeHtml(marker.icon || 'ℹ')}</span><span>${escapeHtml(marker.label)}</span></p>${titleHtml}</div>${bodyHtml}</aside>`;
}

function renderBlockquote(lines, page) {
  const normalizedLines = trimBlankLines(lines);
  const marker = parseCalloutMarker(normalizedLines[0]);
  if (!marker) {
    return `<blockquote>${markdownToHtml(normalizedLines.join('\n'), page)}</blockquote>`;
  }

  return renderCallout(marker, trimBlankLines(normalizedLines.slice(1)), page);
}

function resolveComparisonPanelDefinition(rawType) {
  const normalized = normalizeCalloutType(rawType);
  return normalized && COMPARISON_PANEL_DEFINITIONS[normalized]
    ? { type: normalized, ...(COMPARISON_PANEL_DEFINITIONS[normalized]) }
    : null;
}

function parseComparisonBlock(lines, fenceInfo = {}) {
  const normalizedLines = Array.isArray(lines) ? [...lines] : [];
  const introLines = [];
  const panels = [];
  let currentPanel = null;

  const flushPanel = () => {
    if (!currentPanel) return;
    const bodyLines = trimBlankLines(currentPanel.lines);
    if (bodyLines.length) {
      panels.push({
        ...currentPanel,
        title: currentPanel.title || currentPanel.label,
        bodyLines,
      });
    }
    currentPanel = null;
  };

  for (const rawLine of normalizedLines) {
    const trimmed = rawLine.trim();
    const sectionMatch = /^::([a-zA-Z0-9_-]+)::(?:\s+(.*))?$/.exec(trimmed);
    const definition = sectionMatch ? resolveComparisonPanelDefinition(sectionMatch[1]) : null;

    if (definition) {
      flushPanel();
      currentPanel = {
        ...definition,
        title: (sectionMatch[2] || '').trim(),
        lines: [],
      };
      continue;
    }

    if (currentPanel) {
      currentPanel.lines.push(rawLine);
    } else {
      introLines.push(rawLine);
    }
  }

  flushPanel();

  return {
    title: fenceInfo.title || '',
    summary: fenceInfo.summary || '',
    introLines: trimBlankLines(introLines),
    panels,
  };
}

function renderComparisonBlock(lines, page, fenceInfo = {}) {
  const comparison = parseComparisonBlock(lines, fenceInfo);
  if (!comparison.panels.length) {
    return '';
  }

  const order = ['before', 'after', 'delta'];
  const orderedPanels = comparison.panels
    .slice()
    .sort((left, right) => order.indexOf(left.type) - order.indexOf(right.type));
  const primaryPanels = orderedPanels.filter((panel) => panel.type !== 'delta');
  const deltaPanels = orderedPanels.filter((panel) => panel.type === 'delta');
  const introHtml = comparison.introLines.length ? markdownToHtml(comparison.introLines.join('\n'), page) : '';
  const summaryHtml = comparison.summary ? `<p class="comparison-block__summary">${inlineMarkdown(comparison.summary, page)}</p>` : '';
  const titleHtml = comparison.title ? `<h2 class="comparison-block__title">${inlineMarkdown(comparison.title, page)}</h2>` : '';
  const headerHtml = titleHtml || summaryHtml || introHtml
    ? `<div class="comparison-block__header"><p class="comparison-block__eyebrow">Comparison</p>${titleHtml}${summaryHtml}${introHtml}</div>`
    : '';

  const renderPanel = (panel) => {
    const bodyHtml = markdownToHtml(panel.bodyLines.join('\n'), page);
    return `<article class="comparison-panel comparison-panel--${escapeHtml(panel.tone)}"><div class="comparison-panel__header"><p class="comparison-panel__eyebrow">${escapeHtml(panel.eyebrow || panel.label)}</p><h3 class="comparison-panel__title">${inlineMarkdown(panel.title || panel.label, page)}</h3></div><div class="comparison-panel__body">${bodyHtml}</div></article>`;
  };

  const primaryHtml = primaryPanels.length
    ? `<div class="comparison-block__grid comparison-block__grid--${Math.min(primaryPanels.length, 2)}">${primaryPanels.map(renderPanel).join('')}</div>`
    : '';
  const deltaHtml = deltaPanels.length
    ? `<div class="comparison-block__delta-stack">${deltaPanels.map(renderPanel).join('')}</div>`
    : '';

  return `<section class="comparison-block">${headerHtml}${primaryHtml}${deltaHtml}</section>`;
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
  let comparisonFence = null;
  let comparisonLines = [];

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
    parts.push(renderBlockquote(blockquoteLines, page));
    blockquoteLines = [];
  };

  const flushCodeBlock = () => {
    if (codeFence === null) return;
    parts.push(renderCodeBlock(codeLines, codeFence));
    codeFence = null;
    codeLines = [];
  };

  const flushComparisonBlock = () => {
    if (comparisonFence === null) return;
    parts.push(renderComparisonBlock(comparisonLines, page, comparisonFence));
    comparisonFence = null;
    comparisonLines = [];
  };

  for (const rawLine of lines) {
    if (comparisonFence !== null) {
      if (rawLine.trim() === ':::') {
        flushComparisonBlock();
      } else {
        comparisonLines.push(rawLine);
      }
      continue;
    }
    const fenceMatch = /^```\s*([^`]*)$/.exec(rawLine.trim());
    if (fenceMatch) {
      if (codeFence !== null) {
        flushCodeBlock();
      } else {
        flushParagraph();
        flushLists();
        flushBlockquote();
        codeFence = parseCodeFenceInfo(fenceMatch[1]);
      }
      continue;
    }

    if (codeFence !== null) {
      codeLines.push(rawLine);
      continue;
    }

    const comparisonFenceMatch = /^:::\s*(comparison|compare)\b(.*)$/.exec(rawLine.trim());
    if (comparisonFenceMatch) {
      flushParagraph();
      flushLists();
      flushBlockquote();
      comparisonFence = parseComparisonFenceInfo(comparisonFenceMatch[2] || '');
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
  flushComparisonBlock();

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

function buildDateArchiveCollections(pages) {
  const collections = new Map();

  const datedEntries = pages
    .filter((page) => !isNotFoundOutputName(page.outputName) && page.metadata?.date && page.metadata?.archive !== false)
    .map((page) => {
      const date = resolveArchiveDate(page.metadata.date, page);
      const year = String(date.getUTCFullYear());
      const monthNumber = String(date.getUTCMonth() + 1).padStart(2, '0');
      return {
        title: page.metadata.title || page.slug,
        description: page.metadata.description || '',
        excerpt: resolveArchiveEntryExcerpt(page),
        outputName: page.outputName,
        sourceName: page.sourceName,
        isoDate: date.toISOString(),
        dateLabel: formatArchiveDateLabel(date),
        sortKey: date.getTime(),
        archivePin: page.metadata?.archivePin === true,
        archivePinRank: Number.isInteger(page.metadata?.archivePinRank) ? page.metadata.archivePinRank : Number.MAX_SAFE_INTEGER,
        year,
        monthNumber,
      };
    })
    .sort((left, right) => right.sortKey - left.sortKey || left.outputName.localeCompare(right.outputName));

  for (const entry of datedEntries) {
    if (!collections.has(entry.year)) {
      collections.set(entry.year, {
        year: entry.year,
        outputName: `archives/${entry.year}/index.html`,
        totalPages: 0,
        monthMap: new Map(),
      });
    }

    const yearCollection = collections.get(entry.year);
    const monthKey = `${entry.year}-${entry.monthNumber}`;
    if (!yearCollection.monthMap.has(monthKey)) {
      yearCollection.monthMap.set(monthKey, {
        key: monthKey,
        year: entry.year,
        monthNumber: entry.monthNumber,
        label: formatArchiveMonthLabel(entry.year, entry.monthNumber),
        anchorId: `month-${monthKey}`,
        outputName: buildArchiveMonthOutputName(entry.year, entry.monthNumber),
        pages: [],
      });
    }

    yearCollection.monthMap.get(monthKey).pages.push(entry);
    yearCollection.totalPages += 1;
  }

  return Array.from(collections.values())
    .map((collection) => ({
      year: collection.year,
      outputName: collection.outputName,
      totalPages: collection.totalPages,
      months: Array.from(collection.monthMap.values()).sort((left, right) => right.key.localeCompare(left.key)),
    }))
    .sort((left, right) => right.year.localeCompare(left.year));
}

function buildNavigation(pages, tagCollections, dateArchiveCollections = []) {
  const navigation = pages
    .filter((page) => page.metadata.nav !== false)
    .map((page) => ({
      title: page.metadata.title || page.slug,
      outputName: page.outputName,
      order: page.metadata.order,
    }));

  if (dateArchiveCollections.length) {
    navigation.push({
      title: 'Archive',
      outputName: ARCHIVE_INDEX_OUTPUT_NAME,
      order: Number.MAX_SAFE_INTEGER - 1,
      section: 'archives',
    });
  }

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

function resolveArchiveDate(rawValue, page) {
  const parsed = new Date(String(rawValue));
  if (Number.isNaN(parsed.getTime())) {
    throw new Error(`Invalid archive date for ${page.sourceName || page.outputName}: ${rawValue}`);
  }
  return parsed;
}

function formatArchiveMonthLabel(year, monthNumber) {
  const monthIndex = Number(monthNumber) - 1;
  return `${MONTH_LABELS[monthIndex]} ${year}`;
}

function buildArchiveMonthOutputName(year, monthNumber) {
  return `archives/${year}/${monthNumber}/index.html`;
}

function formatArchiveDateLabel(date) {
  return `${MONTH_LABELS[date.getUTCMonth()]} ${date.getUTCDate()}, ${date.getUTCFullYear()}`;
}

function stripMarkdownToText(text) {
  return String(text || '')
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/__([^_]+)__/g, '$1')
    .replace(/_([^_]+)_/g, '$1')
    .replace(/~~([^~]+)~~/g, '$1')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function truncateExcerpt(text, maxLength = 220) {
  const normalized = String(text || '').trim();
  if (!normalized || normalized.length <= maxLength) {
    return normalized;
  }

  const clipped = normalized.slice(0, maxLength - 1);
  const boundary = clipped.lastIndexOf(' ');
  const safeClip = boundary >= Math.max(40, Math.floor(maxLength * 0.55)) ? clipped.slice(0, boundary) : clipped;
  return `${safeClip.replace(/[\s.,;:!?-]+$/g, '')}…`;
}

function extractArchiveExcerptParagraph(markdown) {
  const lines = String(markdown || '').replace(/\r/g, '').split('\n');
  const paragraph = [];
  let inCodeBlock = false;
  let inComparisonBlock = false;

  for (const rawLine of lines) {
    const trimmed = rawLine.trim();

    if (/^```/.test(trimmed)) {
      inCodeBlock = !inCodeBlock;
      continue;
    }

    if (/^:::\s*(comparison|compare)\b/.test(trimmed)) {
      inComparisonBlock = true;
      continue;
    }

    if (inComparisonBlock && trimmed === ':::') {
      inComparisonBlock = false;
      continue;
    }

    if (inCodeBlock || inComparisonBlock) {
      continue;
    }

    if (!trimmed) {
      if (paragraph.length) {
        break;
      }
      continue;
    }

    if (
      /^#{1,6}\s+/.test(trimmed) ||
      /^>\s?/.test(trimmed) ||
      /^[-*]\s+/.test(trimmed) ||
      /^\d+\.\s+/.test(trimmed) ||
      /^::(?:before|after|delta)::/.test(trimmed)
    ) {
      if (paragraph.length) {
        break;
      }
      continue;
    }

    paragraph.push(trimmed);
  }

  return paragraph.join(' ');
}

function resolveArchiveEntryExcerpt(page) {
  const explicitExcerpt = typeof page.metadata?.excerpt === 'string' ? page.metadata.excerpt.trim() : '';
  const bodyParagraph = extractArchiveExcerptParagraph(page.body || '');
  const description = typeof page.metadata?.description === 'string' ? page.metadata.description.trim() : '';
  return truncateExcerpt(stripMarkdownToText(explicitExcerpt || bodyParagraph || description));
}

function renderDateArchiveEntryMeta(entry) {
  return `<p class="date-archive-entry__meta"><time datetime="${escapeHtml(entry.isoDate)}">${escapeHtml(entry.dateLabel)}</time> <span aria-hidden="true">·</span> <code>${escapeHtml(entry.sourceName)}</code></p>`;
}

function collectArchiveEntries(collection) {
  return collection.months.flatMap((month) => month.pages);
}

function getPinnedArchiveEntries(entries) {
  return entries
    .filter((entry) => entry.archivePin === true)
    .sort(
      (left, right) =>
        left.archivePinRank - right.archivePinRank ||
        right.sortKey - left.sortKey ||
        left.outputName.localeCompare(right.outputName)
    );
}

function getChronologicalArchiveEntries(entries) {
  return entries.filter((entry) => entry.archivePin !== true);
}

function selectArchiveLeadEntry(entries) {
  return getChronologicalArchiveEntries(entries)[0] || entries[0] || null;
}

function renderDateArchiveEntryCard(entry, page, options = {}) {
  const featured = options.featured === true;
  const pinned = options.pinned === true || entry.archivePin === true;
  const headingLevel = Number.isInteger(options.headingLevel) ? Math.min(Math.max(options.headingLevel, 2), 6) : featured ? 2 : 3;
  const headingTag = `h${headingLevel}`;
  const eyebrowLabel = options.eyebrow || (pinned ? 'Pinned entry' : '');
  const eyebrow = eyebrowLabel ? `<p class="date-archive-eyebrow date-archive-entry__eyebrow">${escapeHtml(eyebrowLabel)}</p>` : '';
  const excerpt = entry.excerpt ? `<p class="date-archive-entry__excerpt">${escapeHtml(entry.excerpt)}</p>` : '';
  const href = escapeHtml(relativeLink(page.outputName, entry.outputName));
  const actions = featured || pinned ? `<p class="date-archive-entry__actions"><a href="${href}">Read entry</a></p>` : '';
  const classNames = ['date-archive-entry'];
  if (featured) classNames.push('date-archive-entry--featured');
  if (pinned) classNames.push('date-archive-entry--pinned');

  return `<article class="${classNames.join(' ')}">${eyebrow}${renderDateArchiveEntryMeta(entry)}<${headingTag}><a href="${href}">${escapeHtml(entry.title)}</a></${headingTag}>${excerpt}${actions}</article>`;
}

function renderDateArchiveEntry(entry, page, options = {}) {
  return `<li>${renderDateArchiveEntryCard(entry, page, options)}</li>`;
}

function renderDateArchiveFeaturedEntry(entry, page, options = {}) {
  return renderDateArchiveEntryCard(entry, page, {
    ...options,
    featured: true,
  });
}

function renderDateArchiveEntryGrid(entries, page, options = {}) {
  if (!entries.length) {
    return '';
  }

  const classNames = ['date-archive-entry-list', 'date-archive-entry-list--cards'];
  if (options.variant === 'pinned') {
    classNames.push('date-archive-entry-list--pinned');
  }

  return `<ol class="${classNames.join(' ')}">${entries
    .map((entry) =>
      renderDateArchiveEntry(entry, page, {
        pinned: options.variant === 'pinned',
        eyebrow: options.eyebrow,
      })
    )
    .join('')}</ol>`;
}

function renderDateArchivePinnedSection(entries, page, options = {}) {
  if (!entries.length) {
    return '';
  }

  const title = options.title || 'Pinned archive entries';
  const description = options.description || `${entries.length} pinned update${entries.length === 1 ? ' stays' : 's stay'} surfaced for quick recruiter or reviewer scans.`;
  return `<section class="date-archive-pinned"><div class="date-archive-pinned__header"><p class="date-archive-eyebrow">Pinned</p><h2>${escapeHtml(title)}</h2><p>${escapeHtml(description)}</p></div>${renderDateArchiveEntryGrid(entries, page, { variant: 'pinned' })}</section>`;
}

function renderDateArchiveIndexContent(dateArchiveCollections, page) {
  const totalPages = dateArchiveCollections.reduce((sum, collection) => sum + collection.totalPages, 0);
  return `<section class="date-archive-index">
  <p>Browse ${totalPages} dated portfolio page${totalPages === 1 ? '' : 's'} in reverse chronological order. Use these generated archive pages for project logs, shipped slices, and timeline-style portfolio updates.</p>
  <ul class="date-archive-year-list">${dateArchiveCollections
    .map((collection) => {
      const yearEntries = collectArchiveEntries(collection);
      const pinnedEntries = getPinnedArchiveEntries(yearEntries);
      const featuredEntry = selectArchiveLeadEntry(yearEntries);
      return `<li><article class="date-archive-year-card"><p class="date-archive-eyebrow">Year archive</p><h2><a href="${escapeHtml(relativeLink(page.outputName, collection.outputName))}">${escapeHtml(collection.year)}</a></h2><p>${collection.totalPages} dated page${collection.totalPages === 1 ? '' : 's'} across ${collection.months.length} month${collection.months.length === 1 ? '' : 's'}.</p>${pinnedEntries.length ? renderDateArchivePinnedSection(pinnedEntries, page, { title: `${collection.year} pinned updates`, description: `${pinnedEntries.length} pinned update${pinnedEntries.length === 1 ? ' stays' : 's stay'} visible ahead of the generated timeline.` }) : ''}${featuredEntry && featuredEntry.archivePin !== true ? renderDateArchiveFeaturedEntry(featuredEntry, page, { eyebrow: `Latest in ${collection.year}`, headingLevel: 3 }) : ''}<ul class="date-archive-month-list">${collection.months
        .map((month) => {
          const latestEntry = selectArchiveLeadEntry(month.pages);
          const pinnedCount = getPinnedArchiveEntries(month.pages).length;
          return `<li><a href="${escapeHtml(relativeLink(page.outputName, month.outputName))}">${escapeHtml(month.label)}</a> <span class="date-archive-count">${month.pages.length} page${month.pages.length === 1 ? '' : 's'}</span>${pinnedCount ? ` <span class="date-archive-pinned-count">${pinnedCount} pinned</span>` : ''}${latestEntry ? ` <span class="date-archive-latest">Latest: <a href="${escapeHtml(relativeLink(page.outputName, latestEntry.outputName))}">${escapeHtml(latestEntry.title)}</a></span>` : ''}</li>`;
        })
        .join('')}</ul></article></li>`;
    })
    .join('')}</ul>
</section>`;
}

function renderDateArchiveYearContent(collection, page) {
  const yearEntries = collectArchiveEntries(collection);
  const pinnedEntries = getPinnedArchiveEntries(yearEntries);
  const featuredEntry = selectArchiveLeadEntry(yearEntries);
  return `<section class="date-archive-year">
  <p><a href="${escapeHtml(relativeLink(page.outputName, ARCHIVE_INDEX_OUTPUT_NAME))}">← All archives</a></p>
  <p>${collection.totalPages} dated page${collection.totalPages === 1 ? '' : 's'} grouped by month for ${escapeHtml(collection.year)}.</p>
  ${renderDateArchivePinnedSection(pinnedEntries, page, { title: `${collection.year} pinned updates`, description: `${pinnedEntries.length} pinned update${pinnedEntries.length === 1 ? ' stays' : 's stay'} ahead of the reverse-chronological monthly timeline.` })}
  ${featuredEntry && featuredEntry.archivePin !== true ? renderDateArchiveFeaturedEntry(featuredEntry, page, { eyebrow: `Latest in ${collection.year}`, headingLevel: 2 }) : ''}
  <ul class="date-archive-month-jump-list">${collection.months
    .map((month) => {
      const monthLeadEntry = selectArchiveLeadEntry(month.pages);
      const pinnedCount = getPinnedArchiveEntries(month.pages).length;
      return `<li><a href="#${month.anchorId}">${escapeHtml(month.label)}</a> <span class="date-archive-count">${month.pages.length} page${month.pages.length === 1 ? '' : 's'}</span>${pinnedCount ? ` <span class="date-archive-pinned-count">${pinnedCount} pinned</span>` : ''} <a href="${escapeHtml(relativeLink(page.outputName, month.outputName))}">Open month page</a>${monthLeadEntry ? ` <span class="date-archive-latest">Latest: <a href="${escapeHtml(relativeLink(page.outputName, monthLeadEntry.outputName))}">${escapeHtml(monthLeadEntry.title)}</a></span>` : ''}</li>`;
    })
    .join('')}</ul>
  ${collection.months
    .map((month) => {
      const pinnedMonthEntries = getPinnedArchiveEntries(month.pages);
      const visibleEntries = getChronologicalArchiveEntries(month.pages);
      const monthLeadEntry = visibleEntries[0] || null;
      const repeatsYearFeature = featuredEntry && monthLeadEntry && monthLeadEntry.outputName === featuredEntry.outputName;
      const featuredMonthEntry = repeatsYearFeature ? null : monthLeadEntry;
      const remainingEntries = visibleEntries.slice(monthLeadEntry ? 1 : 0);
      return `<section class="date-archive-month-section" id="${month.anchorId}"><p class="date-archive-eyebrow">Month archive</p><h2>${escapeHtml(month.label)}</h2><p class="date-archive-section-links"><a href="${escapeHtml(relativeLink(page.outputName, month.outputName))}">Browse ${escapeHtml(month.label)}</a></p>${renderDateArchivePinnedSection(pinnedMonthEntries, page, { title: `${month.label} pinned updates`, description: `${pinnedMonthEntries.length} pinned update${pinnedMonthEntries.length === 1 ? ' stays' : 's stay'} attached to this month page and yearly archive.` })}${featuredMonthEntry ? renderDateArchiveFeaturedEntry(featuredMonthEntry, page, { eyebrow: 'Featured entry', headingLevel: 3 }) : ''}${renderDateArchiveEntryGrid(remainingEntries, page)}</section>`;
    })
    .join('')}
</section>`;
}

function renderDateArchiveMonthContent(collection, month, page) {
  const pinnedEntries = getPinnedArchiveEntries(month.pages);
  const visibleEntries = getChronologicalArchiveEntries(month.pages);
  const featuredEntry = visibleEntries[0] || null;
  const remainingEntries = visibleEntries.slice(featuredEntry ? 1 : 0);
  return `<section class="date-archive-month-page">
  <p class="date-archive-section-links"><a href="${escapeHtml(relativeLink(page.outputName, ARCHIVE_INDEX_OUTPUT_NAME))}">← All archives</a> <span aria-hidden="true">·</span> <a href="${escapeHtml(relativeLink(page.outputName, collection.outputName))}">${escapeHtml(collection.year)} archive</a></p>
  <p>${month.pages.length} dated page${month.pages.length === 1 ? '' : 's'} published in ${escapeHtml(month.label)}.</p>
  ${renderDateArchivePinnedSection(pinnedEntries, page, { title: `${month.label} pinned updates`, description: `${pinnedEntries.length} pinned update${pinnedEntries.length === 1 ? ' stays' : 's stay'} surfaced above the monthly timeline.` })}
  ${featuredEntry ? renderDateArchiveFeaturedEntry(featuredEntry, page, { eyebrow: `Latest in ${month.label}`, headingLevel: 2 }) : ''}
  ${renderDateArchiveEntryGrid(remainingEntries, page)}
</section>`;
}

function selectFallbackHomePage(pages) {
  return pages.find((page) => page.outputName === 'index.html') || pages.find((page) => page.metadata.nav !== false) || null;
}

function resolveSiteMetadata(siteConfig, pages) {
  const homePage = selectFallbackHomePage(pages);
  return {
    title: siteConfig.title || (homePage ? homePage.metadata.title || homePage.slug : 'Portfolio site'),
    description:
      siteConfig.description ||
      (homePage ? homePage.metadata.description || `Generated portfolio feed for ${homePage.metadata.title || homePage.slug}.` : 'Generated portfolio feed.'),
    language: siteConfig.language || 'en-us',
    copyright: siteConfig.copyright || '',
  };
}

function normalizeSitemapLastmod(rawValue, page) {
  if (rawValue === undefined || rawValue === null || rawValue === '') {
    return '';
  }

  const parsed = new Date(String(rawValue));
  if (Number.isNaN(parsed.getTime())) {
    throw new Error(`Invalid sitemap lastmod for ${page.sourceName || page.outputName}: ${rawValue}`);
  }

  return parsed.toISOString();
}

function normalizeSitemapChangefreq(rawValue, page) {
  if (rawValue === undefined || rawValue === null || rawValue === '') {
    return '';
  }

  const normalized = String(rawValue).trim().toLowerCase();
  const supported = new Set(['always', 'hourly', 'daily', 'weekly', 'monthly', 'yearly', 'never']);
  if (!supported.has(normalized)) {
    throw new Error(`Invalid sitemap changefreq for ${page.sourceName || page.outputName}: ${rawValue}`);
  }

  return normalized;
}

function normalizeSitemapPriority(rawValue, page) {
  if (rawValue === undefined || rawValue === null || rawValue === '') {
    return '';
  }

  const parsed = Number(rawValue);
  if (!Number.isFinite(parsed) || parsed < 0 || parsed > 1) {
    throw new Error(`Invalid sitemap priority for ${page.sourceName || page.outputName}: ${rawValue}`);
  }

  return parsed.toFixed(1);
}

function resolveRssPubDate(rawValue, page) {
  if (rawValue === undefined || rawValue === null || rawValue === '') {
    return '';
  }

  const parsed = new Date(String(rawValue));
  if (Number.isNaN(parsed.getTime())) {
    throw new Error(`Invalid RSS date for ${page.sourceName || page.outputName}: ${rawValue}`);
  }

  return parsed.toUTCString();
}

function renderSitemapXml(siteConfig, pages) {
  const eligiblePages = pages.filter((page) => !isNotFoundOutputName(page.outputName) && page.metadata?.sitemap !== false);
  const entries = eligiblePages
    .map((page) => {
      const lastmod = normalizeSitemapLastmod(page.metadata?.lastmod || page.metadata?.date || '', page);
      const changefreq = normalizeSitemapChangefreq(page.metadata?.changefreq || '', page);
      const priority = normalizeSitemapPriority(page.metadata?.priority, page);
      const lines = [`  <url>`, `    <loc>${escapeXml(buildAbsoluteSiteUrl(siteConfig.siteUrl, page.outputName))}</loc>`];
      if (lastmod) {
        lines.push(`    <lastmod>${escapeXml(lastmod)}</lastmod>`);
      }
      if (changefreq) {
        lines.push(`    <changefreq>${escapeXml(changefreq)}</changefreq>`);
      }
      if (priority) {
        lines.push(`    <priority>${escapeXml(priority)}</priority>`);
      }
      lines.push('  </url>');
      return lines.join('\n');
    })
    .join('\n');

  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${entries}
</urlset>
`;
}

function renderRssFeedXml(siteConfig, pages) {
  const metadata = resolveSiteMetadata(siteConfig, pages);
  const feedPages = pages
    .filter((page) => !isNotFoundOutputName(page.outputName) && page.metadata?.rss !== false && page.metadata?.date)
    .map((page) => ({ page, pubDate: resolveRssPubDate(page.metadata.date, page) }))
    .sort((left, right) => new Date(right.page.metadata.date).getTime() - new Date(left.page.metadata.date).getTime());

  const items = feedPages
    .map(({ page, pubDate }) => {
      const title = page.metadata.title || page.slug;
      const description = page.metadata.description || title;
      const link = buildAbsoluteSiteUrl(siteConfig.siteUrl, page.outputName);
      const categories = (page.tags || []).map((tag) => `    <category>${escapeXml(tag.label)}</category>`);
      return [
        '    <item>',
        `      <title>${escapeXml(title)}</title>`,
        `      <link>${escapeXml(link)}</link>`,
        `      <guid isPermaLink="true">${escapeXml(link)}</guid>`,
        `      <description>${escapeXml(description)}</description>`,
        `      <pubDate>${escapeXml(pubDate)}</pubDate>`,
        ...categories.map((category) => category.replace(/^ {4}/, '      ')),
        '    </item>',
      ].join('\n');
    })
    .join('\n');

  const feedLines = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<rss version="2.0">',
    '  <channel>',
    `    <title>${escapeXml(metadata.title)}</title>`,
    `    <link>${escapeXml(siteConfig.siteUrl)}</link>`,
    `    <description>${escapeXml(metadata.description)}</description>`,
    `    <language>${escapeXml(metadata.language)}</language>`,
  ];

  if (metadata.copyright) {
    feedLines.push(`    <copyright>${escapeXml(metadata.copyright)}</copyright>`);
  }
  if (feedPages[0]) {
    feedLines.push(`    <lastBuildDate>${escapeXml(feedPages[0].pubDate)}</lastBuildDate>`);
  }
  if (items) {
    feedLines.push(items);
  }

  feedLines.push('  </channel>');
  feedLines.push('</rss>');
  feedLines.push('');

  return feedLines.join('\n');
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
  const includesCodeBlocks = contentHtml.includes('class="code-block"');
  const enhancementScripts = includesCodeBlocks ? [createCodeBlockEnhancementSnippet()] : [];

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
      .code-block { margin: 0; border: 1px solid #0f172a22; border-radius: 1rem; overflow: hidden; background: #f8fafc; box-shadow: 0 12px 30px -24px #0f172a; }
      .code-block__meta { display: flex; flex-wrap: wrap; align-items: center; gap: 0.55rem; padding: 0.75rem 0.9rem; background: #e2e8f0; border-bottom: 1px solid #cbd5e1; }
      .code-block__title, .code-block__language, .code-block__line-count { display: inline-flex; align-items: center; border-radius: 999px; padding: 0.15rem 0.55rem; font-size: 0.85rem; }
      .code-block__title { background: #dbeafe; color: #1d4ed8; font-weight: 600; }
      .code-block__language { background: #dcfce7; color: #166534; font-weight: 600; }
      .code-block__line-count { background: #e5e7eb; color: #334155; }
      .code-block__meta-spacer { flex: 1 1 auto; }
      .code-block__actions { display: inline-flex; flex-wrap: wrap; align-items: center; justify-content: flex-end; gap: 0.5rem; margin-left: auto; }
      .code-block__status { min-height: 1rem; font-size: 0.82rem; color: #475569; }
      .code-block__copy { appearance: none; border: 1px solid #94a3b8; background: #fff; color: #0f172a; border-radius: 999px; padding: 0.35rem 0.75rem; font: inherit; font-size: 0.82rem; font-weight: 600; cursor: pointer; transition: background 120ms ease, border-color 120ms ease, color 120ms ease, opacity 120ms ease; }
      .code-block__copy:hover { border-color: #2563eb; color: #1d4ed8; }
      .code-block__copy:focus-visible { outline: 2px solid #2563eb; outline-offset: 2px; }
      .code-block__copy:disabled { cursor: progress; opacity: 0.85; }
      .code-block__copy[data-copy-state="success"] { background: #dcfce7; border-color: #22c55e; color: #166534; }
      .code-block__copy[data-copy-state="error"] { background: #fee2e2; border-color: #ef4444; color: #991b1b; }
      .code-block pre { margin: 0; overflow-x: auto; background: transparent; color: inherit; padding: 0.85rem 0; border-radius: 0; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size: 0.95rem; line-height: 1.6; tab-size: 2; }
      .code-block pre code { display: grid; min-width: max-content; background: transparent; padding: 0; border-radius: 0; }
      .code-block__line { display: grid; grid-template-columns: minmax(2.5rem, auto) 1fr; gap: 1rem; align-items: start; padding: 0 1rem; }
      .code-block__line::before { content: attr(data-line); text-align: right; color: #64748b; user-select: none; }
      .code-block__line-content { white-space: pre; }
      blockquote { margin: 0; padding: 0.25rem 1rem; border-left: 4px solid #2563eb; background: #2563eb11; border-radius: 0 0.85rem 0.85rem 0; }
      .callout { --callout-accent: #2563eb; --callout-bg: #eff6ff; --callout-fg: #1e3a8a; margin: 0; padding: 1rem 1.1rem; border: 1px solid #cbd5e1; border-left: 5px solid var(--callout-accent); background: var(--callout-bg); border-radius: 0 1rem 1rem 0; }
      .callout--reviewer { --callout-accent: #7c3aed; --callout-bg: #f5f3ff; --callout-fg: #5b21b6; }
      .callout--architecture { --callout-accent: #0f766e; --callout-bg: #ecfeff; --callout-fg: #115e59; }
      .callout--performance { --callout-accent: #ea580c; --callout-bg: #fff7ed; --callout-fg: #9a3412; }
      .callout--tradeoff { --callout-accent: #b45309; --callout-bg: #fffbeb; --callout-fg: #92400e; }
      .callout--testing { --callout-accent: #2563eb; --callout-bg: #eff6ff; --callout-fg: #1d4ed8; }
      .callout--tip { --callout-accent: #15803d; --callout-bg: #f0fdf4; --callout-fg: #166534; }
      .callout--warning { --callout-accent: #dc2626; --callout-bg: #fef2f2; --callout-fg: #991b1b; }
      .callout__header { display: grid; gap: 0.35rem; margin-bottom: 0.75rem; }
      .callout__eyebrow { display: inline-flex; align-items: center; gap: 0.45rem; margin: 0; font-size: 0.82rem; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase; color: var(--callout-fg); }
      .callout__icon { font-size: 0.95rem; }
      .callout__title { margin: 0; font-size: 1.05rem; font-weight: 700; color: inherit; }
      .callout__body { display: grid; gap: 0.8rem; }
      .callout__body > :first-child { margin-top: 0; }
      .callout__body > :last-child { margin-bottom: 0; }
      .comparison-block { display: grid; gap: 1rem; padding: 1.15rem; border: 1px solid #cbd5e1; border-radius: 1.1rem; background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%); box-shadow: 0 14px 32px -28px #0f172a; }
      .date-archive-eyebrow { margin: 0; font-size: 0.78rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #475569; }
      .date-archive-year-list, .date-archive-month-list, .date-archive-month-jump-list, .date-archive-entry-list { list-style: none; padding: 0; margin: 0; display: grid; gap: 0.85rem; }
      .date-archive-year-card, .date-archive-month-section { padding: 1rem 1.05rem; border: 1px solid #cbd5e1; border-radius: 1rem; background: #ffffffcc; box-shadow: 0 10px 24px -24px #0f172a; }
      .date-archive-entry { display: grid; gap: 0.65rem; padding: 1rem 1.05rem; border: 1px solid #cbd5e1; border-radius: 1rem; background: #ffffffcc; box-shadow: 0 10px 24px -24px #0f172a; height: 100%; }
      .date-archive-entry--featured { border-left: 4px solid #2563eb; background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%); box-shadow: 0 16px 30px -26px #1d4ed8; }
      .date-archive-entry--pinned { border-style: dashed; border-color: #f59e0b; background: linear-gradient(180deg, #fffbeb 0%, #ffffff 100%); }
      .date-archive-year, .date-archive-index, .date-archive-month-page, .date-archive-year-card, .date-archive-month-section, .date-archive-pinned { display: grid; gap: 1rem; }
      .date-archive-pinned { padding: 1rem 1.05rem; border: 1px solid #fbbf24; border-radius: 1rem; background: #fffbebcc; box-shadow: 0 10px 24px -24px #d97706; }
      .date-archive-pinned__header { display: grid; gap: 0.4rem; }
      .date-archive-month-jump-list { grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }
      .date-archive-month-list li, .date-archive-month-jump-list li { display: flex; flex-wrap: wrap; gap: 0.4rem; align-items: baseline; }
      .date-archive-entry-list { counter-reset: archive-item; }
      .date-archive-entry-list > li { counter-increment: archive-item; }
      .date-archive-entry-list--cards { grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }
      .date-archive-entry-list--pinned { grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); }
      .date-archive-entry__meta, .date-archive-count, .date-archive-latest, .date-archive-pinned-count, .date-archive-section-links { margin: 0; color: #475569; font-size: 0.92rem; }
      .date-archive-entry__eyebrow { color: #1d4ed8; }
      .date-archive-entry--pinned .date-archive-entry__eyebrow, .date-archive-pinned .date-archive-eyebrow { color: #b45309; }
      .date-archive-entry__excerpt { margin: 0; color: #334155; }
      .date-archive-entry__actions { margin: 0; font-weight: 600; }
      .date-archive-entry h2, .date-archive-entry h3, .date-archive-year-card h2, .date-archive-month-section h2, .date-archive-pinned h2 { margin-top: 0.1rem; margin-bottom: 0.2rem; }
      .date-archive-entry p:last-child, .date-archive-year-card p:last-child, .date-archive-month-section p:last-child, .date-archive-month-page p:last-child, .date-archive-pinned p:last-child { margin-bottom: 0; }
      .comparison-block__header { display: grid; gap: 0.55rem; }
      .comparison-block__eyebrow, .comparison-panel__eyebrow { margin: 0; font-size: 0.78rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #475569; }
      .comparison-block__title, .comparison-panel__title { margin: 0; }
      .comparison-block__summary { margin: 0; color: #334155; }
      .comparison-block__grid, .comparison-block__delta-stack { display: grid; gap: 0.9rem; }
      .comparison-block__grid--2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .comparison-panel { --comparison-accent: #2563eb; --comparison-bg: #eff6ff; --comparison-fg: #1e3a8a; display: grid; gap: 0.8rem; padding: 1rem; border-radius: 0.95rem; border: 1px solid #cbd5e1; background: var(--comparison-bg); border-top: 4px solid var(--comparison-accent); }
      .comparison-panel--before { --comparison-accent: #b45309; --comparison-bg: #fffbeb; --comparison-fg: #92400e; }
      .comparison-panel--after { --comparison-accent: #15803d; --comparison-bg: #f0fdf4; --comparison-fg: #166534; }
      .comparison-panel--delta { --comparison-accent: #7c3aed; --comparison-bg: #f5f3ff; --comparison-fg: #5b21b6; }
      .comparison-panel__header { display: grid; gap: 0.3rem; }
      .comparison-panel__eyebrow, .comparison-panel__title { color: var(--comparison-fg); }
      .comparison-panel__body { display: grid; gap: 0.8rem; }
      .comparison-panel__body > :first-child { margin-top: 0; }
      .comparison-panel__body > :last-child { margin-bottom: 0; }
      @media (max-width: 720px) {
        .comparison-block__grid--2 { grid-template-columns: 1fr; }
      }
      @media (prefers-color-scheme: dark) {
        .code-block { border-color: #ffffff1f; background: #0f172a; box-shadow: none; }
        .code-block__meta { background: #111827; border-bottom-color: #1f2937; }
        .code-block__title { background: #1d4ed833; color: #bfdbfe; }
        .code-block__language { background: #14532d; color: #bbf7d0; }
        .code-block__line-count { background: #1f2937; color: #cbd5e1; }
        .code-block__status { color: #cbd5e1; }
        .code-block__copy { background: #111827; border-color: #334155; color: #e5e7eb; }
        .code-block__copy:hover { border-color: #60a5fa; color: #bfdbfe; }
        .code-block__copy[data-copy-state="success"] { background: #14532d; border-color: #22c55e; color: #dcfce7; }
        .code-block__copy[data-copy-state="error"] { background: #7f1d1d; border-color: #f87171; color: #fee2e2; }
        .code-block pre { color: #e5e7eb; }
        .code-block__line::before { color: #94a3b8; }
        .callout { border-color: #334155; color: #e5e7eb; }
        .callout--note { --callout-bg: #172554; --callout-fg: #bfdbfe; }
        .callout--reviewer { --callout-bg: #2e1065; --callout-fg: #ddd6fe; }
        .callout--architecture { --callout-bg: #042f2e; --callout-fg: #99f6e4; }
        .callout--performance { --callout-bg: #431407; --callout-fg: #fdba74; }
        .callout--tradeoff { --callout-bg: #451a03; --callout-fg: #fcd34d; }
        .callout--testing { --callout-bg: #172554; --callout-fg: #bfdbfe; }
        .callout--tip { --callout-bg: #052e16; --callout-fg: #bbf7d0; }
        .callout--warning { --callout-bg: #450a0a; --callout-fg: #fecaca; }
        .comparison-block { border-color: #334155; background: linear-gradient(180deg, #0f172a 0%, #111827 100%); box-shadow: none; }
        .date-archive-eyebrow, .date-archive-entry__meta, .date-archive-count, .date-archive-latest, .date-archive-pinned-count, .date-archive-section-links { color: #cbd5e1; }
        .date-archive-year-card, .date-archive-month-section, .date-archive-entry { border-color: #334155; background: #111827; box-shadow: none; }
        .date-archive-entry--featured { border-left-color: #60a5fa; background: linear-gradient(180deg, #172554 0%, #111827 100%); }
        .date-archive-entry--pinned, .date-archive-pinned { border-color: #b45309; background: linear-gradient(180deg, #451a03 0%, #111827 100%); }
        .date-archive-entry__eyebrow { color: #93c5fd; }
        .date-archive-entry--pinned .date-archive-entry__eyebrow, .date-archive-pinned .date-archive-eyebrow { color: #fdba74; }
        .date-archive-entry__excerpt { color: #e2e8f0; }
        .comparison-block__eyebrow { color: #cbd5e1; }
        .comparison-block__summary { color: #cbd5e1; }
        .comparison-panel { border-color: #334155; color: #e5e7eb; }
        .comparison-panel--before { --comparison-bg: #451a03; --comparison-fg: #fcd34d; }
        .comparison-panel--after { --comparison-bg: #052e16; --comparison-fg: #bbf7d0; }
        .comparison-panel--delta { --comparison-bg: #2e1065; --comparison-fg: #ddd6fe; }
      }
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
    ${enhancementScripts.join('\n    ')}
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
    throw new Error(`Generated page path conflicts with source page output: ${conflicts.join(', ')}`);
  }
}

function assertNoGeneratedAssetConflicts(assetOutputNames, generatedOutputNames) {
  const authoredAssets = new Set(assetOutputNames);
  const conflicts = generatedOutputNames.filter((outputName) => authoredAssets.has(outputName));
  if (conflicts.length) {
    throw new Error(`Generated page path conflicts with static asset output: ${conflicts.join(', ')}`);
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

  const siteConfig = loadSiteConfig(contentDir);
  const partials = loadTemplatePartials(contentDir);
  fs.mkdirSync(outputDir, { recursive: true });

  const tagCollections = buildTagCollections(pages);
  const dateArchiveCollections = buildDateArchiveCollections(pages);
  const tagCollectionsBySlug = new Map(tagCollections.map((collection) => [collection.slug, collection]));
  const hasAuthoredNotFoundPage = pages.some((page) => isNotFoundOutputName(page.outputName));
  const generatedOutputNames = [];
  if (!hasAuthoredNotFoundPage) {
    generatedOutputNames.push(NOT_FOUND_OUTPUT_NAME);
  }
  if (dateArchiveCollections.length) {
    generatedOutputNames.push(
      ARCHIVE_INDEX_OUTPUT_NAME,
      ...dateArchiveCollections.flatMap((collection) => [collection.outputName, ...collection.months.map((month) => month.outputName)])
    );
  }
  if (tagCollections.length) {
    generatedOutputNames.push('tags/index.html', ...tagCollections.map((collection) => collection.outputName));
  }
  if (siteConfig) {
    generatedOutputNames.push(SITEMAP_OUTPUT_NAME, RSS_OUTPUT_NAME);
  }
  if (generatedOutputNames.length) {
    assertNoGeneratedPageConflicts(pages, generatedOutputNames);
    assertNoGeneratedAssetConflicts(listStaticAssetOutputNames(contentDir), generatedOutputNames);
  }
  const navigation = buildNavigation(pages, tagCollections, dateArchiveCollections);
  const assets = copyStaticAssets(contentDir, outputDir);

  for (const page of pages) {
    const contentHtml = markdownToHtml(page.body.trim(), page);
    const html = renderTemplate(page, navigation, contentHtml, tagCollectionsBySlug, partials);
    writeRenderedPage(outputDir, page.outputName, html);
  }

  const generatedPages = [];
  const generatedHtmlPages = [];
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
    generatedHtmlPages.push(notFoundPage);
  }

  if (dateArchiveCollections.length) {
    const archiveIndexPage = {
      slug: 'archive',
      outputName: ARCHIVE_INDEX_OUTPUT_NAME,
      section: 'archives',
      metadata: {
        title: 'Archive',
        description: 'Browse dated portfolio updates grouped into generated yearly and monthly archives.',
      },
      sourceName: '(generated)',
      tags: [],
    };

    writeRenderedPage(
      outputDir,
      archiveIndexPage.outputName,
      renderTemplate(archiveIndexPage, navigation, renderDateArchiveIndexContent(dateArchiveCollections, archiveIndexPage), tagCollectionsBySlug, partials)
    );
    generatedPages.push({
      source: '(generated)',
      output: archiveIndexPage.outputName,
      title: archiveIndexPage.metadata.title,
    });
    generatedHtmlPages.push(archiveIndexPage);

    for (const collection of dateArchiveCollections) {
      const archiveYearPage = {
        slug: `archive-${collection.year}`,
        outputName: collection.outputName,
        section: 'archives',
        metadata: {
          title: `Archive: ${collection.year}`,
          description: `${collection.totalPages} dated page${collection.totalPages === 1 ? '' : 's'} grouped by month in ${collection.year}.`,
        },
        sourceName: '(generated)',
        tags: [],
      };

      writeRenderedPage(
        outputDir,
        archiveYearPage.outputName,
        renderTemplate(archiveYearPage, navigation, renderDateArchiveYearContent(collection, archiveYearPage), tagCollectionsBySlug, partials)
      );
      generatedPages.push({
        source: '(generated)',
        output: archiveYearPage.outputName,
        title: archiveYearPage.metadata.title,
      });
      generatedHtmlPages.push(archiveYearPage);

      for (const month of collection.months) {
        const archiveMonthPage = {
          slug: `archive-${collection.year}-${month.monthNumber}`,
          outputName: month.outputName,
          section: 'archives',
          metadata: {
            title: `Archive: ${month.label}`,
            description: `${month.pages.length} dated page${month.pages.length === 1 ? '' : 's'} published in ${month.label}.`,
          },
          sourceName: '(generated)',
          tags: [],
        };

        writeRenderedPage(
          outputDir,
          archiveMonthPage.outputName,
          renderTemplate(archiveMonthPage, navigation, renderDateArchiveMonthContent(collection, month, archiveMonthPage), tagCollectionsBySlug, partials)
        );
        generatedPages.push({
          source: '(generated)',
          output: archiveMonthPage.outputName,
          title: archiveMonthPage.metadata.title,
        });
        generatedHtmlPages.push(archiveMonthPage);
      }
    }
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
      sourceName: '(generated)',
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
    generatedHtmlPages.push(tagIndexPage);

    for (const collection of tagCollections) {
      const archivePage = {
        slug: collection.slug,
        outputName: collection.outputName,
        section: 'tags',
        metadata: {
          title: `Tag: ${collection.label}`,
          description: `${collection.pages.length} page${collection.pages.length === 1 ? '' : 's'} tagged "${collection.label}".`,
        },
        sourceName: '(generated)',
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
      generatedHtmlPages.push(archivePage);
    }
  }

  if (siteConfig) {
    const sitemapXml = renderSitemapXml(siteConfig, [...pages, ...generatedHtmlPages]);
    fs.writeFileSync(path.join(outputDir, SITEMAP_OUTPUT_NAME), sitemapXml, 'utf8');
    generatedPages.push({
      source: '(generated)',
      output: SITEMAP_OUTPUT_NAME,
      title: 'Sitemap',
    });

    const rssXml = renderRssFeedXml(siteConfig, pages);
    fs.writeFileSync(path.join(outputDir, RSS_OUTPUT_NAME), rssXml, 'utf8');
    generatedPages.push({
      source: '(generated)',
      output: RSS_OUTPUT_NAME,
      title: 'RSS Feed',
    });
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
  ARCHIVE_INDEX_OUTPUT_NAME,
  DEFAULT_SERVE_HOST,
  DEFAULT_SERVE_PORT,
  LIVE_RELOAD_PATH,
  NOT_FOUND_OUTPUT_NAME,
  PARTIALS_DIR_NAME,
  RSS_OUTPUT_NAME,
  SITE_CONFIG_NAME,
  SITEMAP_OUTPUT_NAME,
  applyPreviewPlaceholders,
  assertNoGeneratedAssetConflicts,
  assertNoGeneratedPageConflicts,
  buildDateArchiveCollections,
  buildNavigation,
  buildSite,
  buildTagCollections,
  buildWithLogging,
  copyStaticAssets,
  createCodeBlockEnhancementSnippet,
  createLiveReloadClientSnippet,
  createWatchSnapshot,
  detectContentType,
  escapeHtml,
  escapeXml,
  formatBuildSummary,
  injectLiveReloadClient,
  isNotFoundOutputName,
  isReservedContentPath,
  listStaticAssetOutputNames,
  loadPages,
  loadSiteConfig,
  loadTemplatePartials,
  markdownToHtml,
  normalizePreviewPathname,
  renderCodeBlock,
  renderComparisonBlock,
  normalizeTags,
  parseCliArgs,
  parseCodeFenceInfo,
  parseComparisonFenceInfo,
  pageOutputToPublicHref,
  parseFrontMatter,
  parseServePort,
  parseWatchInterval,
  relativeLink,
  renderDefaultNotFoundContent,
  renderPartial,
  renderRssFeedXml,
  renderSitemapXml,
  replaceMarkdownImages,
  replaceMarkdownLinks,
  resolveDocumentHref,
  resolvePreviewNotFoundPath,
  resolvePreviewRequestPath,
  resolveSiteMetadata,
  rootPathForPage,
  sanitizeHref,
  selectFallbackHomePage,
  sendPreviewFile,
  slugify,
  buildAbsoluteSiteUrl,
  startPreviewServer,
  toOutputPath,
  walkContentEntries,
  walkWatchFiles,
  watchSite,
};
