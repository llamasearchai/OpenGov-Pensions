# OpenGov-Pension

**Comprehensive retirement benefits administration system for public employee pension funds operating under the County Employees' Retirement Law of 1937**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org/downloads/)
[![CI](https://github.com/llamasearchai/OpenPension/actions/workflows/ci.yml/badge.svg)](https://github.com/llamasearchai/OpenPension/actions/workflows/ci.yml)

OpenGov-Pension is a production-grade Python system designed to support comprehensive retirement benefits administration system for public employee pension funds operating under the county employees' retirement law of 1937. The system integrates AI/ML capabilities with regulatory compliance workflows to support government agencies and organizations.

## Key Features

- **Multi-State Support**: Comprehensive support for California, Indiana, and Ohio pension systems with state-specific rules, contribution limits, and compliance requirements
- **State-Specific Validation**: Automated eligibility checking and compliance validation for each supported state
- **Benefit Calculations**: Accurate pension benefit calculations based on state-specific formulas and multipliers
- **Regulatory Compliance**: Built-in compliance checking for state-specific requirements including vesting, contribution limits, and reporting

- **AI-Powered Analysis**: Integrated OpenAI and Ollama support for intelligent analysis
- **Regulatory Compliance**: Built-in compliance checking and reporting
- **Multi-Provider LLM Support**: Graceful fallback between OpenAI, Ollama, and local models
- **Async SQLAlchemy ORM**: Modern async DB layer with Alembic migrations
- **Role-Based Authentication**: JWT (OAuth2 password flow) with hashed passwords
- **Rate Limiting & Request IDs**: SlowAPI integration + correlation IDs
- **Structured Logging & Metrics**: Prometheus `/metrics` and JSON logs
- **Production-Ready CI**: Lint, type-check, tests, security scans

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Auth & Security](#auth--security)
- [Metrics & Observability](#metrics--observability)
- [Contributing](#contributing)
- [License](#license)

## Installation

### Prerequisites

- Python 3.11 or higher
- uv (recommended) or pip
- SQLite 3.8 or higher
- Optional: Ollama for local LLM support

### Install with uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/llamasearchai/OpenPension.git
cd OpenPension

# Create virtual environment and install dependencies
uv venv
uv sync

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

##  Quick Start

1. **Copy environment file & adjust secrets**
   ```bash
   cp .env.example .env
   ```
2. **Run database migrations (Alembic)**
   ```bash
   alembic upgrade head
   ```
3. **Start API**
   ```bash
   uvicorn opengovpension.web.app:app --reload
   ```
4. **Register a user & obtain token**
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/register -H 'Content-Type: application/json' -d '{"email":"user@example.com","password":"pass123"}'
   ```
5. **Use token to access protected route**
   ```bash
   curl -H 'Authorization: Bearer <token>' http://localhost:8000/api/v1/items
   ```

Legacy CLI commands (e.g. Datasette, agent analysis) remain available while new API evolves.

## State-Specific Operations

OpenPension provides comprehensive support for multiple state pension systems with state-specific rules, contribution limits, and compliance requirements.

### Supported States

- **California (CA)**: CalPERS-style pension system with 2.5% multiplier
- **Indiana (IN)**: Public employee retirement fund with 1.1% multiplier
- **Ohio (OH)**: State retirement systems with 2.2% multiplier

### CLI Commands

#### List Supported States
```bash
uv run python -m opengovpension state list
```

#### View State Configuration
```bash
uv run python -m opengovpension state config --state CA
```

#### Validate Member Eligibility
```bash
uv run python -m opengovpension state validate --state CA --age 65 --service-years 25 --contribution 8.0
```

#### Calculate Pension Benefits
```bash
uv run python -m opengovpension state calculate --state CA --final-salary 75000 --service-years 30 --retirement-age 65
```

### Interactive Menu

Access state operations through the interactive menu:
```
uv run python -m opengovpension menu
```
Choose option 4 for "State Operations" to access:
- List supported states
- View state configurations
- Validate member eligibility
- Calculate benefits

## API Reference

Base path: `/api/v1`

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| /api/v1/auth/register | POST | Register new user | No |
| /api/v1/auth/login | POST | Obtain JWT | No |
| /api/v1/items | GET | List items | Yes |
| /api/v1/items | POST | Create item | Yes |
| /api/v1/items/{id} | GET | Get item by ID | Yes |
| /metrics | GET | Prometheus metrics | Optional |

Interactive docs: `/docs` (Swagger) and `/redoc`.

## Auth & Security
- OAuth2 password flow (JWT Bearer)
- Bcrypt password hashing
- Token includes `sub` (user id) and `jti`
- Default access token expiry: 15 minutes
- Refresh tokens with rotation on each refresh (`/api/v1/auth/refresh`)
- Rate limiting enforced via SlowAPI decorators (e.g. 60/min list, 30/min create)

## Metrics & Observability
- Prometheus metrics at `/metrics`
- JSON structured logging via `structlog`
- Request IDs and processing time headers (`X-Request-ID`, `X-Process-Time-ms`)

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Fork and clone
git clone https://github.com/your-username/OpenPension.git
cd OpenPension

# Install development dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Run linters
uv run ruff check .
uv run mypy src/

# Format code
uv run black src/
uv run isort src/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/llamasearchai/OpenPension/issues)
- **Discussions**: [GitHub Discussions](https://github.com/llamasearchai/OpenPension/discussions)
- **Email**: nikjois@llamasearch.ai

---

**Built  by Nik Jois <nikjois@llamasearch.ai>**
