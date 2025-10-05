# Security Policy

## Supported Versions

Security updates will typically target the latest minor release.

| Version | Supported |
|---------|-----------|
| 1.x     | Yes      |

## Reporting a Vulnerability

Please report security vulnerabilities privately:

1. Email: security@llamasearch.ai and CC nikjois@llamasearch.ai
2. Provide:
   - Affected versions
   - Vulnerability description
   - Reproduction steps / proof of concept
   - Potential impact assessment
3. Allow up to 72 hours for initial acknowledgement.

Do NOT open a public issue for security vulnerabilities.

## Handling Process

1. Triage and reproduce
2. Assign CVSS score (internal)
3. Develop patch & tests
4. Coordinate release
5. Public disclosure after fix

## Security Best Practices Implemented

- Dependency scanning (Bandit, Safety, pip-audit)
- Linting & type checks in CI
- Rate limiting and request ID correlation
- Structured logging (JSON)
- JWT-based authentication
- Password hashing (bcrypt)
- Input validation with Pydantic
- CORS and security headers (to be extended in middleware)

## Responsible Disclosure
We support responsible disclosure and will credit researchers unless anonymity requested.
