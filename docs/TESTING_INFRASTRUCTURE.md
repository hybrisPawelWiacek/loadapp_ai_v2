# Testing Infrastructure

## Overview

Our testing infrastructure is designed to provide comprehensive test coverage across different layers of the application, using Flask-RESTful with PostgreSQL and psycopg3 as the database backend. The testing setup follows industry best practices and is organized to support both local development and CI/CD pipelines.

## Getting Started

### Installation

1. Install development dependencies:
```bash
pip install -r requirements.txt
```

2. Set up PostgreSQL:
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

3. Initialize test database:
```bash
python scripts/setup_test_db.py
```

### Running Tests

Basic test execution:
```bash
# Run all tests
./scripts/run_tests.sh

# Run specific test suites
./scripts/run_tests.sh -f "tests/unit/"          # Run unit tests
./scripts/run_tests.sh -f "tests/integration/"   # Run integration tests
./scripts/run_tests.sh -m "api"                  # Run API tests
```

## Test Database Configuration

### Database Engine Setup

The test database uses SQLAlchemy with psycopg3 and is configured for proper transaction management:

```python
from sqlalchemy import create_engine, text

# Create test database engine with proper isolation level
test_engine = create_engine(
    "postgresql+psycopg://user:pass@localhost:5432/test_db",
    isolation_level="AUTOCOMMIT"  # Required for database operations
)

# Session factory with explicit transaction management
TestSessionLocal = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )
)
```

### Database Fixtures

Key test database fixtures in `conftest.py`:

```python
@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create test database and tables"""
    # Create database engine for admin operations
    default_db_engine = create_engine(
        "postgresql+psycopg://user:pass@localhost:5432/postgres",
        isolation_level="AUTOCOMMIT"
    )
    
    with default_db_engine.connect() as conn:
        # Use SQLAlchemy text() for raw SQL
        conn.execute(text("DROP DATABASE IF EXISTS test_db"))
        conn.execute(text("CREATE DATABASE test_db"))
    
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()

@pytest.fixture
def test_db():
    """Provide test database session with transaction rollback"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()
```

### Important Database Testing Considerations

1. **Transaction Management**
   - Each test runs in its own transaction
   - Transactions are automatically rolled back after each test
   - Ensures test isolation and data cleanup
   - Prevents test interference

2. **Connection Handling**
   - Proper connection lifecycle management
   - Explicit connection binding to sessions
   - Automatic connection cleanup
   - Connection pooling for performance

3. **Database State**
   - Clean database state for each test
   - Automatic schema creation/cleanup
   - No persistent test data between runs
   - Proper cleanup of resources

4. **SQLAlchemy Best Practices**
   - Use `text()` for raw SQL operations
   - Proper session binding
   - Explicit transaction management
   - Connection pooling configuration

### Common Pitfalls and Solutions

1. **Transaction Issues**
   ```python
   # Wrong:
   conn.execute("commit")  # Don't execute raw commit
   
   # Correct:
   conn.execute(text("SELECT ..."))  # Use SQLAlchemy text()
   ```

2. **Session Management**
   ```python
   # Wrong:
   session = TestSessionLocal()  # Session without connection
   
   # Correct:
   session = TestSessionLocal(bind=connection)  # Explicitly bound session
   ```

3. **Database Operations**
   ```python
   # Wrong:
   conn.execute(f"DROP DATABASE {db_name}")  # SQL injection risk
   
   # Correct:
   conn.execute(text(f"DROP DATABASE {db_name}"))  # Safe SQL execution
   ```

## Test Organization

Our tests are organized by domain and functionality:

```
tests/
├── api/                    # API endpoint tests
│   ├── conftest.py        # API-specific fixtures
│   ├── base_test.py       # Base API test class
│   └── test_*.py         # API tests
├── frontend/              # Frontend tests
│   ├── components/        # Component tests
│   └── pages/            # Page tests
├── integration/           # Integration tests
│   └── database/         # Database integration tests
└── unit/                 # Unit tests
    ├── domain/           # Domain model tests
    ├── services/         # Service layer tests
    └── entities/         # Entity tests
```

### Mock Services

We use dedicated mock services for external integrations:

1. **Maps API Mock**
```python
# mock_services/mock_maps_api.py
def get_route(origin: Location, destination: Location) -> Dict:
    """Mock route calculation"""
    return {
        "distance": 1000.0,
        "duration": 12.0,
        "segments": [
            {
                "country": "Germany",
                "distance": 400.0,
                "duration": 5.0
            },
            {
                "country": "France",
                "distance": 600.0,
                "duration": 7.0
            }
        ]
    }
```

2. **CrewAI Mock**
```python
# mock_services/mock_crewai_api.py
def analyze_route(route_data: Dict) -> Dict:
    """Mock AI analysis of route"""
    return {
        "insights": [
            "Optimal route found through major highways",
            "Expected traffic conditions are favorable"
        ],
        "recommendations": [
            "Consider early departure to avoid peak hours",
            "Alternative routes available if needed"
        ]
    }
```

### Test Types and Patterns

1. **API Tests**
```python
class TestRouteEndpoints(BaseAPITest):
    def test_route_creation(self, client, mock_location):
        response = self.client.post(f"{self.base_url}/routes", json=payload)
        assert response.status_code == 201
        data = response.get_json()
```

2. **Frontend Tests**
```python
class TestRouteComponents:
    def test_route_input_form(self, mock_api_client):
        form_data = render_route_input_form()
        assert form_data is None
        assert 'form_submitted' in st.session_state
```

3. **Database Tests**
```python
class TestDatabaseSchema:
    def test_route_creation(self, db_session):
        route = Route(...)
        db_session.add(route)
        db_session.commit()
```

## Database Testing Strategy

We use PostgreSQL with psycopg3 for all testing environments:

### Features
- Modern PostgreSQL adapter (psycopg3)
- Python 3.13+ compatibility
- Connection pooling
- Health checks
- SSL support
- TCP keepalive

### Configuration
- Connection pooling settings
  - Default pool size: 5
  - Max overflow: 10
  - Pool timeout: 30s
  - Connection recycling: 30m
- Health checks enabled
- SSL preferred
- Application name tracking

### Performance Optimizations
- Connection pooling
- Prepared statements
- Efficient data types
- Optimized queries
- Batch operations

## Test Execution

### Running Tests Locally

We provide a comprehensive test runner script (`scripts/run_tests.sh`) with various options:

```bash
# Basic usage
./scripts/run_tests.sh                          # Run all tests
./scripts/run_tests.sh -v                       # Run with verbose output
./scripts/run_tests.sh -f "tests/unit/"         # Run only unit tests
./scripts/run_tests.sh -p                       # Run tests in parallel
```

### Test Categories and Markers

We use pytest markers to categorize tests:

```python
@pytest.mark.unit          # Unit tests
@pytest.mark.integration   # Integration tests
@pytest.mark.api          # API tests
@pytest.mark.frontend     # Frontend tests
@pytest.mark.slow         # Slow tests
```

## Database Setup

### PostgreSQL Setup
1. Install PostgreSQL
2. Run setup script:
   ```bash
   python scripts/setup_test_db.py
   ```

The script handles:
- Database creation
- User setup
- Permission configuration
- Extension installation

### Environment Configuration

Required environment variables:
```bash
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=loadapp_test
```

## Best Practices

1. **Test Isolation**
   - Use database transactions
   - Clean up test data
   - Reset database state

2. **Test Data Management**
   - Use factories for test data generation
   - Avoid hard-coded test data
   - Clean up test data after use

3. **Performance Considerations**
   - Use connection pooling
   - Enable prepared statements
   - Batch operations where possible
   - Optimize database queries

4. **Coverage Requirements**
   - Minimum 80% code coverage
   - Critical paths require 100% coverage
   - Regular coverage reporting

## Contributing

When adding new tests:
1. Follow the existing directory structure
2. Add appropriate fixtures to `conftest.py`
3. Use relevant pytest markers
4. Update documentation for significant changes
5. Ensure Python 3.13+ compatibility

## Troubleshooting

Common issues and solutions:

1. **Database Connection Issues**
   - Check PostgreSQL service is running
   - Verify connection credentials
   - Ensure database exists
   - Verify psycopg3 installation and version

2. **Test Isolation Problems**
   - Check fixture cleanup
   - Verify transaction rollback
   - Review test dependencies

3. **Performance Issues**
   - Enable connection pooling
   - Use prepared statements
   - Batch operations
   - Optimize queries

4. **Python Version Compatibility**
   - Ensure using psycopg3 for Python 3.13+
   - Check package version compatibility
   - Update dependencies as needed