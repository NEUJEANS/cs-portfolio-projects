# File Integrity Monitor — asymmetric signing slice

- [x] review the remaining gap in the checklist and confirm asymmetric signing is still the weakest missing feature
- [x] refresh `openssl dgst` sign/verify workflow and capture a short self-test note
- [x] add asymmetric manifest signing and verification with optional public-key rotation support
- [x] preserve existing HMAC signing and verification behavior
- [x] expand unit and CLI tests for RSA sign/verify, wrong-key failure, and rotation flow
- [x] update project README usage and future-improvement notes
- [x] run tests and compile checks
- [x] perform three review passes and fix issues found
- [x] run a secret scan before push
