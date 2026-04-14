const fs = require('fs/promises');
const path = require('path');

function bucketFor(filename) {
  const ext = path.extname(filename).toLowerCase();
  if (['.png','.jpg','.jpeg','.gif','.webp'].includes(ext)) return 'images';
  if (['.pdf','.doc','.docx','.txt','.md'].includes(ext)) return 'documents';
  if (['.mp3','.wav'].includes(ext)) return 'audio';
  if (['.js','.py','.ts','.java','.cpp'].includes(ext)) return 'code';
  return 'other';
}

async function organize(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  const moves = [];
  for (const entry of entries) {
    if (!entry.isFile()) continue;
    const bucket = bucketFor(entry.name);
    const targetDir = path.join(dir, bucket);
    await fs.mkdir(targetDir, { recursive: true });
    const from = path.join(dir, entry.name);
    const to = path.join(targetDir, entry.name);
    await fs.rename(from, to);
    moves.push({ from: entry.name, bucket });
  }
  return moves;
}

if (require.main === module) {
  organize(process.argv[2] || '.').then(moves => console.log(JSON.stringify(moves, null, 2))).catch(err => {
    console.error(err);
    process.exit(1);
  });
}

module.exports = { bucketFor, organize };
