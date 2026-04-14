# GitHub Repo Reporter Refresh — endpoint selection self-test

## Refresher
- user repos endpoint: `/users/{username}/repos`
- org repos endpoint: `/orgs/{org}/repos`
- pagination stays the same through the `Link` header
- query parameters like `per_page`, `sort`, `direction`, and `type` remain applicable to repo listing

## Self-test
1. Which endpoint should a student use to summarize a lab or club organization?  
   `/orgs/{org}/repos`
2. Do we need a different pagination parser for org repos?  
   No. The same `Link` header parsing works.
3. Is this a good vertical slice for a portfolio CLI?  
   Yes. It broadens the problem space while staying compact and testable.
