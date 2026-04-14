const https = require('https');

function fetchRepos(username) {
  return new Promise((resolve, reject) => {
    https.get(`https://api.github.com/users/${username}/repos`, {
      headers: { 'User-Agent': 'cs-portfolio-projects' }
    }, res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode !== 200) return reject(new Error(`HTTP ${res.statusCode}`));
        const repos = JSON.parse(data).map(r => ({
          name: r.name,
          stars: r.stargazers_count,
          language: r.language
        }));
        resolve(repos);
      });
    }).on('error', reject);
  });
}

function summarize(repos) {
  return {
    count: repos.length,
    topStarred: [...repos].sort((a,b) => b.stars - a.stars).slice(0, 5),
    languages: repos.reduce((acc, repo) => {
      const key = repo.language || 'Unknown';
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {})
  };
}

async function main() {
  const username = process.argv[2];
  if (!username) throw new Error('usage: node reporter.js <username>');
  const repos = await fetchRepos(username);
  console.log(JSON.stringify(summarize(repos), null, 2));
}

if (require.main === module) {
  main().catch(err => { console.error(err.message); process.exit(1); });
}

module.exports = { summarize };
