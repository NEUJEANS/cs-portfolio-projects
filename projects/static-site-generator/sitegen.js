const fs = require('fs/promises');
const path = require('path');

function markdownToHtml(md) {
  return md
    .split(/\n{2,}/)
    .map(block => {
      if (block.startsWith('# ')) return `<h1>${block.slice(2).trim()}</h1>`;
      if (block.startsWith('## ')) return `<h2>${block.slice(3).trim()}</h2>`;
      return `<p>${block.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}</p>`;
    })
    .join('\n');
}

async function build(srcDir, outDir) {
  await fs.mkdir(outDir, { recursive: true });
  const files = await fs.readdir(srcDir);
  for (const file of files) {
    if (!file.endsWith('.md')) continue;
    const md = await fs.readFile(path.join(srcDir, file), 'utf8');
    const html = `<!doctype html><html><body>${markdownToHtml(md)}</body></html>`;
    await fs.writeFile(path.join(outDir, file.replace(/\.md$/, '.html')), html);
  }
}

if (require.main === module) {
  build(process.argv[2] || 'content', process.argv[3] || 'dist').catch(err => {
    console.error(err);
    process.exit(1);
  });
}

module.exports = { markdownToHtml, build };
