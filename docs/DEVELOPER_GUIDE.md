# Developer Guide

## Development Setup

### Prerequisites
- Python 3.9+
- PostgreSQL 13+
- Node.js 16+ (for frontend development)
- Docker (optional, for containerized development)

### Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/loadapp.ai.git
cd loadapp.ai
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize database:
```bash
flask db upgrade
```

### Development Workflow

#### 1. Branch Management
- Main branches:
  - `main`: Production-ready code
  - `develop`: Integration branch
  - `feature/*`: New features
  - `bugfix/*`: Bug fixes
  - `release/*`: Release preparation

#### 2. Development Process
1. Create feature branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make changes and commit:
```bash
git add .
git commit -m "feat: your descriptive commit message"
```

3. Push changes:
```bash
git push origin feature/your-feature-name
```

4. Create pull request to `develop` branch

#### 3. Code Style
- Follow PEP 8 guidelines
- Use type hints
- Document functions and classes
- Keep functions focused and small
- Use meaningful variable names

#### 4. Pre-commit Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Development Tools

#### Code Formatting
```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8
```

#### Database Management
```bash
# Create migration
flask db migrate -m "description"

# Apply migration
flask db upgrade

# Rollback
flask db downgrade
```

#### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test
pytest tests/test_file.py::test_function
```

### Local Development

#### Running the Application

1. Start backend:
```bash
flask run --debug
```

2. Start frontend:
```bash
cd frontend
streamlit run Home.py
```

#### Docker Development
```bash
# Build containers
docker-compose build

# Start services
docker-compose up

# Stop services
docker-compose down
```

### Debugging

#### VSCode Configuration
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Flask",
            "type": "python",
            "request": "launch",
            "module": "flask",
            "env": {
                "FLASK_APP": "app.py",
                "FLASK_DEBUG": "1"
            },
            "args": [
                "run",
                "--no-debugger"
            ],
            "jinja": true
        }
    ]
}
```

#### Logging
```python
# Example logging configuration
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### API Development

#### Adding New Endpoint
1. Create route file in `app/api/routes/`
2. Define endpoint class
3. Add route to API blueprint
4. Document with OpenAPI/Swagger
5. Add tests

Example:
```python
from flask_restful import Resource

class NewEndpoint(Resource):
    def get(self):
        """Get resource."""
        pass

    def post(self):
        """Create resource."""
        pass
```

#### Error Handling
```python
from app.exceptions import APIError

def handle_error(error):
    if isinstance(error, APIError):
        return {"error": str(error)}, error.status_code
    return {"error": "Internal server error"}, 500
```

### Frontend Development

#### Component Development
1. Create component in `frontend/components/`
2. Follow Streamlit best practices
3. Add type hints
4. Include documentation
5. Add tests

Example:
```python
import streamlit as st
from typing import Dict

def custom_component(data: Dict) -> None:
    """Display custom component.
    
    Args:
        data: Component data
    """
    st.write("Custom Component")
    st.json(data)
```

#### State Management
```python
# Initialize session state
if "key" not in st.session_state:
    st.session_state.key = initial_value

# Update state
st.session_state.key = new_value
```

### Documentation

#### Code Documentation
```python
def function_name(param1: str, param2: int) -> bool:
    """Short description.

    Longer description with examples.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: Description of when this error occurs
    """
    pass
```

#### API Documentation
```python
@api.route("/resource")
class ResourceEndpoint(Resource):
    """Resource endpoint."""
    
    @api.doc(responses={200: "Success", 400: "Invalid input"})
    @api.expect(resource_model)
    def post(self):
        """Create new resource.
        
        Returns:
            dict: Created resource
        """
        pass
```

### Deployment

#### Production Configuration
1. Update environment variables
2. Configure WSGI server
3. Set up SSL certificates
4. Configure monitoring
5. Set up backups

#### Deployment Checklist
- [ ] Run tests
- [ ] Check dependencies
- [ ] Update documentation
- [ ] Review security settings
- [ ] Backup database
- [ ] Update environment variables
- [ ] Deploy code
- [ ] Verify deployment
- [ ] Monitor logs

### Monitoring

#### Application Monitoring
```python
from prometheus_client import Counter, Histogram

# Define metrics
requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)
```

#### Error Tracking
```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)
```

### Security

#### Security Best Practices
1. Use HTTPS
2. Implement authentication
3. Validate input
4. Use prepared statements
5. Keep dependencies updated
6. Enable CORS properly
7. Use secure headers
8. Implement rate limiting
9. Log security events
10. Regular security audits

#### Authentication Example
```python
from functools import wraps
from flask import request

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or not is_valid_api_key(api_key):
            return {'error': 'Invalid API key'}, 401
        return f(*args, **kwargs)
    return decorated
```

### Contributing

#### Pull Request Process
1. Create feature branch
2. Make changes
3. Update documentation
4. Add tests
5. Run linters
6. Create pull request
7. Address review comments
8. Merge when approved

#### Code Review Guidelines
1. Check code style
2. Verify tests
3. Review documentation
4. Check performance
5. Validate security
6. Test functionality
7. Review error handling
8. Check logging

## Testing

### Setup

1. Install test dependencies:
```bash
pip install -r requirements.txt
```

2. Configure test database:
```bash
python scripts/setup_test_db.py
```

### Running Tests

```bash
# Run all tests
./scripts/run_tests.sh

# Run specific test suites
./scripts/run_tests.sh -f "tests/unit/"          # Unit tests
./scripts/run_tests.sh -f "tests/integration/"   # Integration tests
./scripts/run_tests.sh -m "api"                  # API tests
```

### Test Organization

```
tests/
├── api/                    # API endpoint tests
│   ├── conftest.py        # API-specific fixtures
│   ├── base_test.py       # Base API test class
│   ├── test_app.py        # Core API tests
│   └── test_contracts.py  # Contract-related tests
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

### Test Patterns

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
    def test_route_form(self, mock_api_client):
        form_data = render_route_input_form()
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

### Test Configuration

1. Database Setup:
```python
# tests/conftest.py
@pytest.fixture
def db_session():
    from backend.flask_app import db
    connection = db.engine.connect()
    transaction = connection.begin()
    session = db.create_scoped_session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()
```

2. API Client Setup:
```python
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
```

### Test Fixtures

1. **Location Fixtures**
```python
@pytest.fixture
def mock_location():
    return Location(
        latitude=52.5200,
        longitude=13.4050,
        address="Berlin, Germany"
    )
```

2. **Route Fixtures**
```python
@pytest.fixture
def sample_route(mock_location):
    return Route(
        id=uuid4(),
        origin=mock_location,
        destination=Location(
            latitude=48.8566,
            longitude=2.3522,
            address="Paris, France"
        ),
        pickup_time=datetime.now(),
        delivery_time=datetime.now() + timedelta(days=1),
        empty_driving=EmptyDriving(),
        main_route=MainRoute(...)
    )
```

### Mocking External Services

1. **API Mocking**
```python
@pytest.fixture
def mock_api_client(monkeypatch):
    def mock_get(*args, **kwargs):
        return {"data": "test"}
    monkeypatch.setattr("requests.get", mock_get)
```

2. **Database Mocking**
```python
@pytest.fixture
def mock_db():
    """Create a test database."""
    SQLALCHEMY_DATABASE_URL = "postgresql+psycopg://postgres@localhost:5432/loadapp_test"
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield Repository(db)
    finally:
        db.close()
```

### Test Coverage

Running coverage reports:
```bash
# Generate coverage report
pytest --cov=backend --cov=frontend tests/

# Generate HTML report
pytest --cov=backend --cov=frontend --cov-report=html tests/
```

Coverage requirements:
- Minimum 80% overall coverage
- Critical paths require 100% coverage
- New features must include tests

### Test Best Practices

1. **Test Isolation**
- Use fixtures for test data
- Clean up after tests
- Don't rely on test order
- Mock external dependencies

2. **Test Organization**
- Group related tests in classes
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)
- Keep tests focused and small

3. **Error Testing**
```python
def test_error_handling(self):
    with pytest.raises(ValueError):
        Route(
            origin=None,  # Invalid: missing origin
            destination=None  # Invalid: missing destination
        )
```

### Test Environment Setup

1. **Configure Mock Services**
```python
# tests/conftest.py
@pytest.fixture
def mock_maps_service(monkeypatch):
    def mock_get_route(*args, **kwargs):
        return {
            "distance": 1000.0,
            "duration": 12.0,
            "segments": [
                {"country": "Germany", "distance": 400.0, "duration": 5.0},
                {"country": "France", "distance": 600.0, "duration": 7.0}
            ]
        }
    monkeypatch.setattr("mock_services.mock_maps_api.get_route", mock_get_route)

@pytest.fixture
def mock_crewai_service(monkeypatch):
    def mock_analyze(*args, **kwargs):
        return {
            "insights": ["Optimal route found"],
            "recommendations": ["Consider early departure"]
        }
    monkeypatch.setattr("mock_services.mock_crewai_api.analyze", mock_analyze)
```

2. **Configure Frontend Testing**
```python
@pytest.fixture(autouse=True)
def setup_streamlit():
    # Reset Streamlit session state before each test
    for key in list(st.session_state.keys()):
        del st.session_state[key]
```

### Test Patterns

1. **Entity Testing**
```python
# tests/unit/domain/test_entities.py
class TestRouteEntity:
    def test_route_creation(self, mock_location):
        route = Route(
            origin=mock_location,
            destination=Location(
                latitude=48.8566,
                longitude=2.3522,
                address="Paris, France"
            ),
            pickup_time=datetime.now(),
            delivery_time=datetime.now() + timedelta(days=1),
            empty_driving=EmptyDriving(),
            main_route=MainRoute(...)
        )
        assert route.is_feasible is True
```

2. **Frontend Component Testing**
```python
# tests/frontend/components/test_route_components.py
class TestRouteComponents:
    def test_route_input_form(self, mock_api_client):
        form_data = render_route_input_form()
        assert form_data is None
        assert 'form_submitted' in st.session_state

    def test_route_display(self, mock_route):
        route_data = {
            "id": str(mock_route.id),
            "origin": {"address": mock_route.origin.address},
            "destination": {"address": mock_route.destination.address},
            "distance_km": 1000.0
        }
        render_route_display(route_data)
```

3. **Service Testing**
```python
# tests/unit/services/test_cost_calculation_service.py
class TestCostCalculationService:
    def test_calculate_route_cost(self, cost_service, sample_route, cost_settings):
        result = cost_service.calculate_route_cost(sample_route, cost_settings)
        assert result["total_cost"] > 0
        assert "cost_breakdown" in result
```

### Test Data Management

1. **Using Fixtures**
```python
@pytest.fixture
def mock_location():
    return Location(
        latitude=52.5200,
        longitude=13.4050,
        address="Berlin, Germany"
    )

@pytest.fixture
def sample_route(mock_location):
    return Route(
        origin=mock_location,
        destination=Location(...),
        main_route=MainRoute(...)
    )
```

2. **Database Fixtures**
```python
@pytest.fixture
def db_session():
    from backend.flask_app import db
    connection = db.engine.connect()
    transaction = connection.begin()
    session = db.create_scoped_session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()
```