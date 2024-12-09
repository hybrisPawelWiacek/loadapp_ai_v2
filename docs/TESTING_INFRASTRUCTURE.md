# Testing Infrastructure

This document outlines the testing infrastructure, methodology, and guidelines for the LoadApp.AI project.

## Testing Framework

The project uses pytest as its primary testing framework, offering:
- Rich fixture support
- Detailed assertion introspection
- Modular and scalable test organization
- Comprehensive test discovery
- Parameterized testing capabilities

## Test Directory Structure

```
tests/
├── __init__.py
├── conftest.py                    # Shared pytest fixtures and configuration
├── domain/                        # Domain layer tests
│   ├── services/                  # Domain service tests
│   │   ├── test_route_planning.py # Route planning service tests
│   │   ├── test_offer_generation.py # Offer generation service tests
│   │   └── test_cost_calculation.py # Cost calculation service tests
│   └── test_entities.py          # Entity validation and behavior tests
├── integration/                   # Integration tests
│   └── test_integration.py       # End-to-end workflow tests
├── documentation/                 # Documentation tests
│   ├── test_architecture.py      # Architecture documentation tests
│   ├── test_endpoints.py         # API documentation tests
│   ├── test_entities.py          # Entity documentation tests
│   └── test_services.py          # Service documentation tests
├── test_advanced_cost_settings.py # Cost settings feature tests
├── test_app.py                   # Main application tests
├── test_cost_calculation_service.py
├── test_database.py              # Database integration tests
├── test_entities.py              # Entity tests
├── test_flask_endpoints.py       # API endpoint tests
├── test_offer_service.py         # Offer service tests
├── test_project_structure.py     # Project structure validation
├── test_route_planning_service.py # Route planning tests
└── test_streamlit_ui.py          # UI component tests
```

## Running Tests

### Local Test Execution

1. **Run All Tests**
   ```bash
   python -m pytest
   ```

2. **Run Tests with Verbose Output**
   ```bash
   python -m pytest -v
   ```

3. **Run Specific Test Categories**
   ```bash
   # Run unit tests
   python -m pytest tests/domain/

   # Run integration tests
   python -m pytest tests/integration/

   # Run documentation tests
   python -m pytest tests/documentation/

   # Run specific test file
   python -m pytest tests/test_flask_endpoints.py
   ```

4. **Run Tests with Coverage Report**
   ```bash
   python -m pytest --cov=.
   ```

### Environment Variables

The following environment variables should be set for testing:
- `OPENAI_API_KEY`: Required for tests involving AI integration
- `FLASK_ENV=testing`: Ensures Flask runs in testing mode
- `SQLITE_DB_PATH`: Path to test database (defaults to in-memory database)

## Test Organization

### Naming Conventions

- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`
- Fixture files: `conftest.py`

### Test Categories

1. **Unit Tests**
   - Located in `tests/domain/`
   - Test individual components in isolation
   - Mock external dependencies
   - Focus on business logic validation

2. **Integration Tests**
   - Located in `tests/integration/`
   - Test component interactions
   - Use real database connections
   - Validate end-to-end workflows

3. **Documentation Tests**
   - Located in `tests/documentation/`
   - Ensure documentation accuracy
   - Validate API specifications
   - Check architectural compliance

4. **UI Tests**
   - Located in `test_streamlit_ui.py`
   - Test Streamlit component behavior
   - Validate user interactions
   - Check state management

### Dependency Injection

The Flask app uses dependency injection to facilitate testing:

```python
# In tests, you can replace the repository and services:
app.set_repository(mock_db)
app.set_offer_service(mock_offer_service)

# Get current repository and services:
repo = app.get_repository()
offer_service = app.get_offer_service()
```

This allows tests to:
- Replace the real database with an in-memory SQLite database
- Mock external services like AI integration
- Restore original services after tests complete

### Test Database

The test suite uses an in-memory SQLite database that is:
- Created fresh for each test
- Pre-populated with necessary fixtures
- Automatically cleaned up after each test

Example of setting up test data:
```python
@pytest.fixture
def default_cost_settings(mock_db):
    """Create default cost settings in the mock database."""
    settings_data = [
        {
            "type": "fuel",
            "category": "variable",
            "base_value": 1.5,
            "multiplier": 1.0,
            "currency": "EUR",
            "is_enabled": True
        }
    ]
    mock_db.save_cost_settings(settings_data)
    return settings_data
```

### Asynchronous Testing

The project uses `pytest-asyncio` for testing asynchronous components:

```python
import pytest

@pytest.mark.asyncio
async def test_async_component():
    """Test an asynchronous operation."""
    # Arrange
    service = AsyncService()
    
    # Act
    result = await service.async_operation()
    
    # Assert
    assert result is not None
```

Key points for async testing:
- Use `@pytest.mark.asyncio` decorator for async test functions
- Write tests using async/await syntax
- Handle both successful and error cases
- Test timeouts and cancellation scenarios

## Test Coverage Areas

### 1. Route Planning Service Tests
Located in `tests/domain/services/test_route_planning.py`:
- Timeline validation tests
  - Basic timeline constraints
  - EU regulation compliance
  - Loading window validation
  - Rest period requirements
- Route segment calculations
  - Empty driving validation
  - Main route validation
  - Country segment handling
- Timeline event structure
  - Event sequence validation
  - Event timing accuracy
  - Location data validation

Example of EU regulation test:
```python
def test_calculate_route_timeline_validation(mock_location):
    """Test comprehensive route calculation timeline validation."""
    service = RoutePlanningService()
    tz = pytz.timezone('Europe/Berlin')
    base_time = datetime.now(tz)
    
    # Test case: Exceeding maximum daily driving time
    with pytest.raises(ValueError, match="Exceeds maximum daily driving time"):
        service.calculate_route(
            origin=mock_location,
            destination=Location(latitude=41.9028, longitude=12.4964, address="Rome"),
            pickup_time=base_time,
            delivery_time=base_time + timedelta(hours=10)
        )
```

### 2. Offer Generation Service Tests
Located in `tests/domain/services/test_offer_generation.py`:
- Basic offer generation
  - Default margin calculations
  - Custom margin handling
  - Currency support
- Error handling
  - AI service failures
  - Database errors
  - Input validation
- Offer retrieval and listing
  - Single offer retrieval
  - Paginated listing
  - Empty results handling

Example of offer generation test:
```python
def test_generate_offer_basic(service, mock_route):
    """Test basic offer generation with default margin."""
    cost_breakdown = {
        "total": 1000.0,
        "fuel": 500.0,
        "driver": 300.0,
        "toll": 200.0
    }
    
    offer = service.generate_offer(
        route=mock_route,
        cost_breakdown=cost_breakdown
    )
    
    assert offer.total_cost == cost_breakdown["total"]
    assert offer.margin == 10.0  # Default margin
    assert offer.final_price == 1100.0  # 1000 + 10%
```

### 3. Mock Fixtures
The test suite now includes comprehensive mock fixtures:
- Route fixtures with realistic data
- Repository mocks for database operations
- AI service mocks for fun fact generation
- Cost calculation fixtures

## Database Testing

The database testing infrastructure has been significantly improved to ensure data integrity and proper handling of domain models. Key features include:

### Test Database Setup

- Database configuration is centralized in `db_setup.py`
- Test database is automatically initialized with correct schema
- Each test gets a clean database state
- Proper handling of SQLite-specific configurations

### Entity Testing

The test suite includes comprehensive tests for all major entities:

1. **Cost Settings**
   - Creation and retrieval
   - Type and value validation
   - Proper UUID handling

2. **Routes**
   - Complex nested object handling (Location, TransportType, Cargo)
   - Proper conversion between domain and database models
   - Validation of geographical data
   - Timeline and segment management

3. **Offers**
   - Relationship with routes
   - Cost breakdown storage and retrieval
   - Status management
   - Proper UUID and datetime handling

### Best Practices

When writing database tests:

1. **Data Conversion**
   - Always convert UUIDs to strings when storing in SQLite
   - Use proper datetime objects with timezone awareness
   - Handle JSON serialization for complex objects

2. **Domain Model Access**
   - Access nested attributes through proper object hierarchy
   - Example: `route.origin.latitude` instead of `route.origin_latitude`
   - Maintain separation between domain and database models

3. **Test Data Creation**
   - Use realistic test data that matches production scenarios
   - Include all required fields and relationships
   - Test both happy path and edge cases

### Example Test Case

```python
def test_database_setup():
    # Initialize database
    init_db()
    db = SessionLocal()
    repo = Repository(db)

    try:
        # Create and test cost setting
        cost_setting = CostSetting(
            id=str(uuid4()),
            type="fuel",
            category="variable",
            base_value=1.5,
            multiplier=1.0,
            description="Fuel cost per kilometer",
            is_enabled=True
        )
        db_cost_setting = repo.create_cost_setting(cost_setting.__dict__)

        # Create and test route
        route = Route(
            origin=Location(latitude=52.52, longitude=13.405, address="Berlin"),
            destination=Location(latitude=48.8566, longitude=2.3522, address="Paris"),
            pickup_time=current_time,
            delivery_time=current_time + timedelta(days=1),
            transport_type=transport_type,
            cargo=cargo,
            empty_driving=empty_driving,
            main_route=main_route
        )
        db_route = repo.save_route(route)

        # Create and test offer
        offer = Offer(
            id=str(uuid4()),
            route_id=str(db_route.id),
            total_cost=1500.0,
            margin=0.15,
            final_price=1725.0
        )
        db_offer = repo.create_offer(offer.__dict__)

        # Verify data integrity
        retrieved_route = repo.get_route(db_route.id)
        assert retrieved_route.origin.latitude == 52.52
        assert retrieved_route.destination.address == "Paris"

    finally:
        db.close()
```

## Dependencies Management

All project dependencies, including those required for testing, are now consolidated in a single `requirements.txt` file at the project root. This includes:

- Core dependencies for running the application
- Testing frameworks and utilities
- Frontend component dependencies
- Development tools

Key testing-related dependencies:
```
pytest==7.4.4
pytest-flask==1.3.0
pytest-mock==3.12.0
pytest-cov==4.1.0
requests-mock==1.11.0
```

### Frontend Testing Dependencies

The frontend testing suite requires specific packages:
```
streamlit==1.29.0
pandas>=2.2.0
plotly==5.18.0
```

These dependencies enable comprehensive testing of:
- Streamlit components and pages
- Data visualization elements
- User input handling
- State management
- API integrations

## Frontend Component Testing

### Component Test Structure

Frontend components are tested in `tests/test_streamlit_ui.py`, which includes:

1. **Mock Setup**
   - Streamlit session state mocking
   - API response mocking
   - Component rendering simulation

2. **Test Categories**
   - Route input form validation
   - Cost calculation integration
   - Offer generation workflow
   - Error handling scenarios
   - Page navigation and state management

3. **Mock Data**
   - Predefined route responses
   - Sample cost calculations
   - Example offer data
   - Review page data

Example of a component test:
```python
def test_route_api_integration(mock_streamlit, mock_api):
    """Test route calculation API integration with frontend components."""
    # Test implementation
```

### Testing Best Practices

1. **Component Isolation**
   - Test each component independently
   - Mock dependencies and external services
   - Validate component-specific behavior

2. **State Management**
   - Verify correct state updates
   - Test state persistence
   - Validate state transitions

3. **API Integration**
   - Mock API responses
   - Test success and error scenarios
   - Validate data transformation

4. **User Interaction**
   - Test input validation
   - Verify event handling
   - Check UI updates

## Adding New Tests

### Guidelines

1. **Test Location**
   - Place unit tests in appropriate domain directory
   - Add integration tests to `tests/integration/`
   - Put documentation tests in `tests/documentation/`

2. **Test Structure**
   - Use pytest fixtures for setup/teardown
   - Follow Arrange-Act-Assert pattern
   - Include docstrings explaining test purpose

3. **Coverage Requirements**
   - Aim for 80%+ code coverage
   - Cover both success and error paths
   - Test edge cases and boundary conditions

### Example Test Structure

```python
import pytest
from loadapp.domain.services import RoutePlanningService

class TestRoutePlanningService:
    @pytest.fixture
    def service(self):
        return RoutePlanningService()

    def test_calculate_route_success(self, service):
        """Test successful route calculation with valid inputs."""
        # Arrange
        origin = {"latitude": 52.5200, "longitude": 13.4050}
        destination = {"latitude": 48.8566, "longitude": 2.3522}
        
        # Act
        route = service.calculate_route(origin, destination)
        
        # Assert
        assert route.is_feasible
        assert route.total_duration_hours > 0
```

## CI/CD Integration

Tests are integrated into the development workflow:

1. **Pre-commit Hooks**
   - Run unit tests
   - Check code formatting
   - Validate documentation

2. **Pull Request Checks**
   - Run full test suite
   - Generate coverage report
   - Validate documentation tests

3. **Deployment Checks**
   - Run integration tests
   - Validate environment configurations
   - Check database migrations

## Best Practices

1. **Test Independence**
   - Each test should be independent
   - Use fixtures for common setup
   - Clean up after tests

2. **Mock External Services**
   - Use pytest-mock for external services
   - Mock OpenAI API calls
   - Mock database connections when appropriate

3. **Maintain Test Quality**
   - Keep tests focused and concise
   - Use meaningful assertions
   - Document complex test scenarios

4. **Regular Maintenance**
   - Update tests when requirements change
   - Remove obsolete tests
   - Keep documentation in sync
