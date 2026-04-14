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
- converts Markdown files into standalone HTML pages
- supports front matter metadata such as `title`, `description`, `order`, `slug`, `tags`, and `nav`
- builds top navigation automatically from page metadata
- applies a clean shared HTML layout and inline stylesheet
- sorts pages by explicit order for predictable portfolio presentation
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
Create a content directory with Markdown files:

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

Generated files are written to `dist/`.

## Test
```bash
npm test
```

## Example portfolio use cases
- personal project showcase
- class project microsite
- internship application portfolio
- learning journal or technical blog prototype

## Future Improvements
- nested directories and blog collections
- syntax highlighting and fenced code blocks
- shared header/footer partials loaded from template files
- asset copying pipeline for images and CSS files
