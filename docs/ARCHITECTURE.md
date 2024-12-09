# LoadApp.AI Architecture Overview

## System Architecture

```ascii
┌───────────────────────┐         ┌────────────────────────┐
│    Frontend Layer     │         │     Backend Layer      │
│    (Streamlit UI)     │◄───────►│      (Flask API)      │
└───────────┬───────────┘   HTTP  └──────────┬────────────┘
            │                                 │
            │                                 │
            ▼                                 ▼
┌───────────────────────┐         ┌────────────────────────┐
│    Domain Layer       │         │  Infrastructure Layer  │
│ Services & Entities   │◄───────►│   Database & External  │
└───────────────────────┘         └────────────────────────┘
```

## Architectural Principles

The system follows two main architectural principles:

### Layered Architecture
The application is structured in distinct layers with clear responsibilities:
- Each layer has a specific role and communicates only with adjacent layers
- Dependencies flow downward, reducing coupling
- Upper layers use abstractions defined by lower layers
- Clear separation enables independent testing and maintainability
- Focus on modularity and code reusability

### Domain-Driven Design (DDD)
The system implements DDD principles to ensure clear separation of concerns and maintainable codebase:
- Business logic is encapsulated within the domain layer
- Clear boundaries between layers maintain system modularity
- Rich domain models capture business rules and invariants
- Repository interfaces abstract data persistence
- Services implement specific business capabilities

## Layer Responsibilities

### Frontend Layer (Streamlit)
- Provides user interface for route planning and cost calculation
- Handles user input validation and form submission
- Displays route details, cost breakdowns, and offers
- Manages state for advanced settings and configurations
- Communicates with backend via HTTP/JSON

### Backend Layer (Flask)
- Exposes RESTful API endpoints for frontend communication
- Coordinates requests between frontend and domain services
- Handles request validation and error responses
- Manages API authentication and session handling
- Orchestrates domain service calls

### Domain Layer
- Contains core business logic and rules
- Implements key services:
  - **RoutePlanningService**: Handles route calculation and optimization
  - **CostCalculationService**: Computes transportation costs including empty driving
  - **OfferService**: Generates final offers with margins and AI-enhanced content
- Defines domain entities and value objects
- Maintains business invariants and validation rules

### Infrastructure Layer
- Manages data persistence through SQLite database
- Implements repository interfaces defined by domain layer
- Handles external service integration (OpenAI API)
- Provides data access patterns and caching mechanisms
- Manages database migrations and schema updates
- Implements structured logging with Structlog
- Provides metrics collection and monitoring capabilities

## API Layer

### Endpoint Implementation
- Route endpoints use Flask-RESTful for RESTful API implementation
- Cost calculation endpoint uses direct Flask routing for simplified debugging and maintenance
- All endpoints follow a consistent error handling pattern
- Structured logging is implemented throughout the request lifecycle

### Database Integration
- SQLAlchemy is used for database operations
- Database session management is handled at the Flask application level
- Repository pattern is used to abstract database operations
- Sessions are properly scoped to ensure thread safety

### Cost Calculation Flow
1. Client sends POST request to `/costs/<route_id>`
2. Flask route handler validates route ID format
3. Repository retrieves route from database
4. CostCalculationService performs calculations:
   - Calculates total distance and duration
   - Applies fixed rates for different cost components
   - Generates cost breakdown
5. Response is returned in JSON format

### Error Handling
- Invalid route IDs return 400 Bad Request
- Missing routes return 404 Not Found
- Calculation errors return 500 Internal Server Error
- All errors are logged with relevant context

## Database Architecture

### Configuration

The database configuration follows a centralized approach to prevent circular dependencies and maintain a single source of truth:

1. **Central Configuration**
   - All database configuration is centralized in `backend/infrastructure/database/db_setup.py`
   - This includes SQLAlchemy engine, session factory, and Base class
   - Proper handling of SQLite-specific settings

2. **Database Location**
   - Database file is stored in `backend/data/loadapp.db`
   - Path is determined dynamically based on project structure
   - Directory is created if it doesn't exist

3. **Session Management**
   - Session factory is provided through `SessionLocal`
   - Context manager pattern used for safe session handling
   - Automatic session cleanup

4. **Model Organization**
   - All SQLAlchemy models defined in `models.py`
   - Clear separation between domain entities and database models
   - Proper type handling for SQLite limitations (UUIDs, JSON)

### Example Configuration

```python
# db_setup.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path

# Database path setup
DB_PATH = Path(__file__).parent.parent.parent / 'data' / 'loadapp.db'
DB_PATH.parent.mkdir(exist_ok=True)
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# SQLAlchemy setup
Base = declarative_base()
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get database session with context management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Best Practices

1. **Imports**
   - Import Base from db_setup.py in all model files
   - Avoid circular imports by proper module organization
   - Use relative imports within the database package

2. **Session Handling**
   - Always use context managers or dependency injection for sessions
   - Clean up sessions in finally blocks
   - Use session factories instead of global sessions

3. **Type Handling**
   - Convert UUIDs to strings for SQLite compatibility
   - Use proper JSON serialization for complex objects
   - Handle timezone-aware datetime objects correctly

## Data Flow

1. **User Input → Backend Processing**
   ```
   Streamlit UI → HTTP Request → Flask Endpoint → Domain Service
   ```
   - User enters route/cargo details in Streamlit
   - Data is validated and sent to Flask backend
   - Backend routes request to appropriate domain service

2. **Domain Processing → Data Storage**
   ```
   Domain Service → Repository Interface → SQLite Database
   ```
   - Domain services process business logic
   - Data is persisted through repository interfaces
   - Database handles storage and retrieval

3. **Response Flow**
   ```
   Database → Repository → Domain Service → Flask → Streamlit
   ```
   - Results are transformed into DTOs
   - Response is sent back through layers
   - UI updates with calculated results

## Key Components

### RoutePlanningService
- Calculates optimal routes between pickup and delivery points
- Handles empty driving scenarios (fixed at 200km/4h in PoC)
- Integrates with mocked Google Maps data
- Validates route feasibility
- Optimized for performance with caching

### CostCalculationService
- Aggregates multiple cost factors:
  - Fuel consumption
  - Toll charges
  - Driver wages
  - Empty driving costs
  - Cargo-specific handling
- Provides transparent cost breakdown
- Supports cost factor customization
- Efficient computation for real-time updates

### OfferService
- Calculates final pricing with configurable margins
- Integrates with OpenAI for transport-related fun facts
- Generates comprehensive offer documents
- Stores offer history for future reference

## Performance Monitoring

The system includes two complementary monitoring systems:

### PerformanceMetrics System
- Real-time performance monitoring with minimal overhead
- Decorators for measuring API response times, service operations, and database queries
- In-memory metric aggregation with thread-safe operations
- Support for labeled metrics to track specific components and operations
- Convenient decorators:
  - `@measure_api_response_time`: Track API endpoint latency
  - `@measure_service_operation_time`: Monitor service operation duration
  - `@measure_db_query_time`: Track database query performance

### MetricsLogger System
- Long-term metrics storage and analysis
- Buffered metric collection to reduce database load
- Configurable metric aggregation periods (1min, 5min, 1hour, 1day)
- Alert rules for monitoring metric thresholds
- Active alert tracking and resolution

Both systems work together to provide comprehensive monitoring:
- PerformanceMetrics handles real-time performance tracking
- MetricsLogger manages long-term storage and alerting
- Efficient buffering and aggregation minimize system overhead
- Thread-safe operations ensure data consistency

## Performance Considerations

- Caching mechanisms improve performance by reducing database queries
- Efficient computation in CostCalculationService enables real-time updates
- Optimized RoutePlanningService reduces computational overhead
- Database indexing and query optimization improve data retrieval performance
- Performance monitoring systems provide insights with minimal overhead

## Maintainability Considerations

- Code organization and modularity enable easy maintenance and updates
- Clear separation of concerns reduces coupling and improves testability
- Domain-driven design ensures business logic is encapsulated and maintainable
- Automated testing and continuous integration ensure code quality

## Future Considerations

- Integration with real-time route optimization for enhanced performance
- Advanced compliance checking
- Multiple user roles and permissions
- Historical data analysis
- AI-driven decision support
- Migration to production-grade database
