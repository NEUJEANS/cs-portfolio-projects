# static-site-generator

## Overview
Generate a small multi-page static website from Markdown files with optional front matter.

## Why it is portfolio-worthy
This project shows practical compiler-style text processing, file-system automation, deterministic build output, lightweight templating, and test-driven Node.js development.

## Stack
- Node.js
- CommonJS
- built-in `node:test`

## Features
- converts Markdown files into standalone HTML pages while preserving nested content folders
- supports front matter metadata such as `title`, `description`, `order`, `slug`, `tags`, and `nav`
- builds top navigation automatically from page metadata while allowing hidden pages via `nav: false`
- renders a focused Markdown subset: headings, paragraphs, bullet lists, links, images, inline code, fenced code blocks, bold, and italics
- recursively copies non-Markdown assets into the output directory so screenshots, CSS files, and downloadable artifacts ship with the site
- preserves nested page paths and rewrites internal Markdown `.md` links into working relative `.html` links across folders
- applies a clean shared HTML layout and inline stylesheet
- sorts pages by explicit order and slug for predictable portfolio presentation
- keeps output dependency-free and runnable locally

## Supported front matter
```yaml
---
title: Projects
description: Short summary shown in the page header
order: 2
slug: student-projects
tags: [node, portfolio]
nav: true
---
```

## Usage
Create a content directory with Markdown files. Nested folders are preserved in the generated site, so `guides/setup.md` becomes `guides/setup.html` and links like `[Home](../index.md)` are rewritten automatically:

```md
---
title: Home
order: 1
description: My CS portfolio
---
# Welcome

- systems projects
- web projects
```

Then build the site:

```bash
node sitegen.js content dist
```

Fenced code blocks are preserved for technical write-ups:

~~~md
```python
from pathlib import Path
print(Path('portfolio').resolve())
```
~~~

Generated files are written to `dist/` and the CLI prints a short build summary.

## Test
```bash
node --test test_static_site_generator.js
```

## Example portfolio use cases
- personal project showcase
- class project microsite
- internship application portfolio
- learning journal or technical blog prototype

## Future Improvements
- blog collections such as date-based post indexes or tag archive pages
- syntax highlighting themes and line-number support for fenced code blocks
- shared header/footer partials loaded from template files
- incremental rebuilds or a watch mode for faster authoring
