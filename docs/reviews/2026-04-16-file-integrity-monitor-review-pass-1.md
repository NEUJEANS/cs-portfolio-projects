# Review Pass 1 — file-integrity-monitor

## Focus
Code-path audit for asymmetric signing support and backward compatibility.

## Findings
- Initial asymmetric test used the private key file as a negative verification case; OpenSSL can derive the public component, so that check was invalid.

## Fixes
- Switched the negative case to a genuinely different RSA public key.
- Re-ran the unit suite after the change.

## Result
- HMAC and RSA signing paths both remain covered.
