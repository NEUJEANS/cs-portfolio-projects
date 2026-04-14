const test = require('node:test');
const assert = require('node:assert/strict');
const { summarize } = require('./reporter');

test('summarize counts repos and languages', () => {
  const summary = summarize([
    { name: 'a', stars: 2, language: 'Python' },
    { name: 'b', stars: 5, language: 'JS' },
    { name: 'c', stars: 1, language: 'Python' }
  ]);
  assert.equal(summary.count, 3);
  assert.equal(summary.languages.Python, 2);
  assert.equal(summary.topStarred[0].name, 'b');
});
