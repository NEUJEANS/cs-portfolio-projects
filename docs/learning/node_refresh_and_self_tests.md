# Node.js Refresh + Self Tests

## Topics refreshed
- `fs/promises` for file IO
- `path` normalization and safe joins
- `readline/promises` for simple interactive flows
- `https` requests and JSON parsing
- `node:test` and `assert/strict`

## Mini self-tests
### 1. Read JSON safely
- load file text with `fs.readFile`
- parse in try/catch
- fall back to empty array when bootstrapping

### 2. HTTPS API fetch
- wrap `https.get` in a Promise
- collect chunks
- `JSON.parse` response body
- reject on non-2xx where appropriate

### 3. Directory organizer
- `readdir(..., { withFileTypes: true })`
- derive extension bucket
- create destination directory with `mkdir({ recursive: true })`
- rename or copy files

### 4. node:test
- small pure helper functions first
- then integration tests in temp dirs

## Practical rules used in these projects
- keep CLIs non-interactive by default with flags for easier testing
- isolate filesystem mutations behind helper functions
- keep API clients pure and mockable
