# Developer Guide

This guide provides instructions for setting up, running, and contributing to the LoadApp.AI project.

## Project Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Git

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd loadapp.ai
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

Key dependencies include:
- Flask >= 2.3.3 (backend framework)
- Flask-RESTful >= 0.3.10 (REST API support)
- Flask-CORS >= 4.0.0 (Cross-Origin Resource Sharing)
- Streamlit >= 1.28.0 (frontend framework)
- SQLAlchemy >= 2.0.20 (database ORM)
- Structlog >= 23.1.0 (logging)
- OpenAI >= 1.3.0 (AI integration)
- Pytest >= 7.4.0 (testing)
- Pytest-Flask >= 1.3.0 (Flask testing)
- Pytest-Mock >= 3.11.1 (mocking)
- Pytest-Cov >= 4.1.0 (test coverage)
- Python-dotenv >= 1.0.0 (environment variables)
- Pydantic >= 2.3.0 (data validation)
- Black >= 23.7.0 (code formatting)
- Pandas >= 2.1.0 (data manipulation)
- Plotly >= 5.16.0 (data visualization)

## Running the Application

### Database Setup
Initialize the database with default settings:
```bash
python init_db.py
```
This will create the SQLite database and set up the initial cost settings.

### Backend (Flask)
Start the Flask backend server:
```bash
cd backend
python app.py
```
The backend will be available at `http://localhost:5000`

### Frontend (Streamlit)
In a new terminal, start the Streamlit frontend:
```bash
cd frontend
streamlit run app.py
```
The frontend will automatically open in your default browser at `http://localhost:8501`

## Development

### Project Structure
```
loadapp.ai/
├── backend/
│   ├── domain/
│   │   ├── entities/      # Domain models
│   │   └── services/      # Business logic
│   ├── infrastructure/    # Database, external services
│   └── app.py            # Flask application
├── frontend/
│   └── app.py            # Streamlit application
├── tests/                # Test files
└── config.py            # Configuration settings
```

### Running Tests

1. Unit Tests:
```bash
python -m pytest tests/test_*.py -v
```

2. Integration Tests:
```bash
python -m pytest tests/integration/test_*.py -v
```

3. Documentation Tests:
```bash
python -m pytest tests/test_documentation.py -v
```

### Coding Standards

1. Python Code Style:
   - Follow PEP 8 guidelines
   - Use meaningful variable and function names
   - Add docstrings to all functions and classes
   - Maximum line length: 100 characters

2. Logging:
   - Use the Python logging module
   - Log levels:
     - ERROR: For errors that prevent normal operation
     - WARNING: For unexpected but handled situations
     - INFO: For significant events
     - DEBUG: For detailed debugging information

3. Error Handling:
   - Use custom exceptions for domain-specific errors
   - Always include meaningful error messages
   - Handle errors at appropriate levels

### Database Session Management

#### Best Practices

1. **Direct Session Creation**
   - Use `SessionLocal()` directly in endpoints or services that need database access
   - Always close sessions after use, preferably in a try-finally block
   - Example:
     ```python
     def get_db_session():
         try:
             session = SessionLocal()
             return session
         except Exception as e:
             logger.error("db_session_creation_failed", error=str(e))
             return None
     ```

2. **Session Scope**
   - Keep session scope as narrow as possible
   - Create sessions at the endpoint level
   - Close sessions as soon as they're no longer needed

#### Common Pitfalls

1. **App Context Issues**
   - Don't rely on Flask's app context for session management
   - Avoid storing session factory in app.config
   - Use direct session creation instead of context-dependent approaches

### Data Serialization

#### UUID Handling

1. **Database Storage**
   - Always convert UUIDs to strings before saving to database
   - Handle UUIDs in nested objects (timeline events, route segments)
   - Example:
     ```python
     route_dict = {
         "id": str(route.id),
         "cargo": {
             "id": str(cargo.id),
             ...
         }
     }
     ```

2. **JSON Serialization**
   - Convert UUIDs to strings before JSON serialization
   - Handle UUID conversion in repository layer
   - Maintain UUID objects in domain layer

#### Dataclass Handling

1. **Proper Initialization**
   - Always initialize all required fields
   - Use default factories for collections
   - Example:
     ```python
     @dataclass
     class TransportType:
         name: str
         capacity: Capacity = field(default_factory=lambda: Capacity())
         restrictions: List[str] = field(default_factory=list)
         id: UUID = field(default_factory=uuid4)
     ```

2. **Type Conversion**
   - Convert input data to proper types before creating dataclasses
   - Handle optional fields appropriately
   - Validate data before creating instances

### Working with the Database

### Setup and Configuration

1. **Database Location**
   - The SQLite database is located at `backend/data/loadapp.db`
   - The directory is automatically created if it doesn't exist
   - For development, you can safely delete the database file to start fresh

2. **Configuration Files**
   - Database configuration is in `backend/infrastructure/database/db_setup.py`
   - Models are defined in `backend/infrastructure/database/models.py`
   - Repository pattern implementation in `backend/infrastructure/database/repository.py`

### Development Workflow

1. **Working with Models**
   ```python
   # Import Base from the central configuration
   from backend.infrastructure.database.db_setup import Base
   
   class YourModel(Base):
       __tablename__ = "your_table"
       # Define your columns here
   ```

2. **Session Management**
   ```python
   from backend.infrastructure.database.db_setup import SessionLocal
   
   def your_function():
       db = SessionLocal()
       try:
           # Your database operations here
           db.commit()
       finally:
           db.close()
   ```

3. **Repository Pattern**
   ```python
   from backend.infrastructure.database.repository import Repository
   
   def your_service():
       db = SessionLocal()
       repo = Repository(db)
       try:
           # Use repository methods
           result = repo.get_route(route_id)
       finally:
           db.close()
   ```

### Common Tasks

1. **Creating New Models**
   - Define model in `models.py`
   - Add repository methods in `repository.py`
   - Update `init_db()` in `db_setup.py`
   - Add test cases in `test_db.py`

2. **Data Type Handling**
   - Convert UUIDs to strings: `str(uuid4())`
   - Use timezone-aware dates: `datetime.now(timezone.utc)`
   - JSON fields: Use SQLAlchemy JSON type

3. **Testing**
   - Use pytest fixtures for database setup
   - Clean database state between tests
   - Test both success and error cases
   - Verify data integrity after operations

### Troubleshooting

1. **Circular Imports**
   - Import Base from db_setup.py
   - Use relative imports within database package
   - Move type hints to typing.py if needed

2. **SQLite Limitations**
   - Convert UUIDs to strings
   - Use JSON for complex objects
   - Handle timezone-aware dates properly

3. **Common Errors**
   - "no such table": Run `init_db()`
   - "UUID not supported": Convert to string
   - "datetime not JSON serializable": Use proper serialization

### Contributing

1. Branching Strategy:
   - `main`: Production-ready code
   - `develop`: Integration branch
   - Feature branches: `feature/feature-name`
   - Bug fixes: `fix/bug-description`

2. Before Submitting Changes:
   - Run all tests
   - Update documentation if needed
   - Follow the coding standards
   - Add appropriate logging statements

3. Code Review Process:
   - Create a pull request
   - Address review comments
   - Ensure CI/CD checks pass

## Troubleshooting

Common issues and solutions:

1. Database Connection:
   - Verify SQLite file permissions
   - Check connection string in config

2. API Errors:
   - Confirm OpenAI API key is set
   - Verify endpoint URLs in config

3. Frontend Issues:
   - Clear browser cache
   - Check backend connectivity

For additional help, consult the project documentation or raise an issue in the repository.
