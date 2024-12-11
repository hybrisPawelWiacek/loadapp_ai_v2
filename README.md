# LoadApp.AI

## Overview

LoadApp.AI is a modern transport logistics platform that uses AI to optimize route planning and cost calculations.

## Prerequisites

- Python 3.11 or higher (Python 3.13+ requires psycopg3)
- PostgreSQL 12 or higher
- Node.js 16+ (for frontend development)

## Quick Start

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/loadapp.ai.git
cd loadapp.ai
```

2. **Set up Python environment:**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure PostgreSQL:**
```bash
# macOS
brew install postgresql
brew services start postgresql

# Linux
sudo apt install postgresql
sudo systemctl start postgresql

# Windows
# Download and install from https://www.postgresql.org/download/windows/
```

4. **Set up environment variables:**
```bash
cp .env.example .env.development
# Edit .env.development with your database credentials
```

5. **Initialize database:**
```bash
# Create and set up development database
python scripts/setup_db.py

# Create and set up test database
### Purpose
Streamline transport planning and offer generation through:
- Intelligent route optimization
- Accurate cost calculations
- AI-enhanced offer generation
- Automated compliance checks

### Core Stack
- Frontend: Streamlit
- Backend: Flask
- Database: PostgreSQL
- AI: OpenAI
See [Architecture Documentation](docs/ARCHITECTURE.md) for detailed technical architecture.

### Documentation
- [Architecture Documentation](docs/ARCHITECTURE.md) - System design and implementation
- [Developer Guide](docs/DEVELOPER_GUIDE.md) - Setup and development workflow
- [Frontend Guide](docs/FRONTEND_GUIDE.md) - UI development guide
- [Testing Guide](docs/TESTING_INFRASTRUCTURE.md) - Testing practices

### Status
- Version: 0.1.0 (PoC)
- Development Stage: Active Development
- Python Version: 3.8+

## Key Features

- **Route Planning:**
  - Intelligent route optimization
  - EU driving regulations compliance
  - Interactive map visualization

- **Cost Management:**
  - Dynamic cost calculations
  - Cost optimization suggestions
  - Historical pattern analysis

- **Market Intelligence:**
  - AI-powered insights
  - Regional demand analysis
  - Competitive pricing

- **System Features:**
  - Performance monitoring
  - Comprehensive logging
  - Multi-currency support

For detailed technical implementation, see [Architecture Documentation](docs/ARCHITECTURE.md).

## Quick Start

### Prerequisites
- Python 3.8+ (Python 3.13+ requires psycopg3)
- PostgreSQL 15+
- pip
- Git
- PostgreSQL client utilities

### Installation

1. Clone and setup:
```bash
git clone <repository-url>
cd loadapp.ai
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env.development
# Edit .env.development with required settings:
# - OPENAI_API_KEY
# - Database credentials (PostgreSQL)
# - Flask configuration
```

3. Set up the database:
```bash
# Install PostgreSQL (macOS)
brew install postgresql
brew services start postgresql

# Setup databases
./scripts/setup_db.sh
```

4. Start the application:
```bash
./start_backend.sh   # Terminal 1
./start_frontend.sh  # Terminal 2
```

Access at:
- Frontend: http://localhost:8501
- Backend API: http://localhost:5000

For detailed setup instructions, see [Developer Guide](docs/DEVELOPER_GUIDE.md).

## Project Structure

```
loadapp.ai/
├── backend/         # Flask backend application
├── frontend/        # Streamlit frontend
├── tests/           # Test suite
├── docs/           # Documentation
└── scripts/        # Utility scripts
```

For detailed architecture and implementation details, see [Architecture Documentation](docs/ARCHITECTURE.md).

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- [Architecture Documentation](docs/ARCHITECTURE.md) - System design and implementation details
- [Developer Guide](docs/DEVELOPER_GUIDE.md) - Development setup and workflow
- [Frontend Guide](docs/FRONTEND_GUIDE.md) - UI development guidelines
- [Testing Guide](docs/TESTING_INFRASTRUCTURE.md) - Testing practices

Start with the Developer Guide for setup instructions.

## License

LoadApp.AI is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2024 hybrisPawelWiacek

This means you are free to:
- Use the software commercially
- Modify the source code
- Distribute the software
- Use it privately

Subject to the following conditions:
- Include the original copyright notice
- Include the MIT License text

## Testing

Our application uses a comprehensive testing infrastructure that supports both SQLite and PostgreSQL databases. The test suite is designed to be fast, reliable, and maintainable.

### Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install psycopg2-binary  # For PostgreSQL tests
   ```

2. **Run Tests**
   ```bash
   # Run all tests with SQLite (fastest)
   ./scripts/run_tests.sh

   # Run with PostgreSQL
   ./scripts/run_tests.sh -d postgres

   # Run with coverage report
   ./scripts/run_tests.sh -c

   # Run specific test categories
   ./scripts/run_tests.sh -f "tests/unit/"     # Unit tests
   ./scripts/run_tests.sh -f "tests/api/"      # API tests
   ```

### Test Organization

Tests are organized by domain and type:
- `tests/unit/`: Unit tests for business logic
- `tests/api/`: API endpoint tests
- `tests/frontend/`: Frontend component tests
- `tests/integration/`: Integration tests
- `tests/performance/`: Performance tests

### Database Testing

We use PostgreSQL as our primary database with psycopg3 adapter:
1. **Development Setup**
   - Modern PostgreSQL adapter (psycopg3)
   - Connection pooling enabled
   - Health checks and keepalive
   - SSL support available

2. **Test Environment**
   - Automated setup with scripts
   - Isolated test database
   - Performance optimizations
   - Full PostgreSQL feature support

To set up PostgreSQL testing:
```bash
# Install PostgreSQL (macOS)
brew install postgresql
brew services start postgresql

# Setup test database
python scripts/setup_test_db.py
```

### Test Runner Options

The `run_tests.sh` script provides various options:
```bash
Options:
  -d, --database <type>    Choose database backend
  -c, --coverage           Generate coverage report
  -v, --verbose           Run tests in verbose mode
  -m, --markers           Specify pytest markers
  -p, --parallel          Run tests in parallel
  -f, --filter            Filter test files by pattern
```

### Continuous Integration

Tests automatically run on GitHub Actions for:
- Every push to main
- All pull requests
- Multiple Python versions (3.8 to 3.13)
- PostgreSQL database testing

### Documentation

For detailed information about our testing infrastructure, see:
- [Testing Infrastructure](docs/TESTING_INFRASTRUCTURE.md)
- [Test Improvement Plan](docs/TEST_IMPROVEMENT_PLAN.md)

### Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Ensure tests work with both databases
3. Maintain minimum 80% coverage
4. Follow existing patterns and organization
5. Update documentation as needed