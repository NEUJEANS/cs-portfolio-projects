const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs/promises');
const os = require('os');
const path = require('path');
const { bucketFor, organize } = require('./organizer');

test('bucketFor categorizes by extension', () => {
  assert.equal(bucketFor('photo.png'), 'images');
  assert.equal(bucketFor('notes.md'), 'documents');
  assert.equal(bucketFor('main.py'), 'code');
});

test('organize moves files into folders', async () => {
  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), 'organizer-'));
  await fs.writeFile(path.join(tmp, 'a.txt'), 'x');
  await organize(tmp);
  const moved = await fs.readFile(path.join(tmp, 'documents', 'a.txt'), 'utf8');
  assert.equal(moved, 'x');
});
