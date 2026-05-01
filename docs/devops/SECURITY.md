# Security Hardening & Governance

## Security Practices
1. **Dependency Audits**: Automated checks for vulnerable packages via `npm audit` and Dependabot.
2. **Secret Scanning**: GitHub Advanced Security scans for leaked credentials.
3. **Key Rotation**: Scripts and schedules in place for rotating JWT keys and sensitive tokens.
4. **Rate Limiting**: Enforced on all public APIs to prevent abuse.
5. **Headers**: Strict Content Security Policy (CSP) and hardened CORS settings.

## Branch Protection & Governance
- `main` and `develop` are protected branches.
- Direct pushes are blocked.
- Pull Requests require:
  - At least 1 approved review.
  - Passing status checks (CI/CD pipeline).
  - Clean security scan results.

## Incident Management
- Defined incident response runbooks.
- Templates for GitHub Issues and Pull Requests.
- `CODEOWNERS` file automatically assigns reviewers based on file paths.
