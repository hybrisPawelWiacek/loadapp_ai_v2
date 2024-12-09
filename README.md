# LoadApp.AI

A smart transport management system that enables quick route planning, cost calculation, and offer generation for cargo transportation requests. This PoC demonstrates core functionalities in a structured, domain-driven design while setting the stage for eventual expansion into a fully featured application.

## Key Features

- **Route Planning:**
  - Input origin/destination and cargo details
  - Automatic empty driving calculation
  - Timeline visualization with pickup/delivery times
  - Mocked route data for PoC phase

- **Cost Calculation:**
  - Comprehensive cost breakdown (fuel, tolls, driver wages)
  - Empty driving cost integration
  - Adjustable cost components via settings
  - Transparent pricing model

- **Offer Generation:**
  - AI-powered fun facts about transport
  - User-defined margin settings
  - Complete cost breakdown
  - Historical offer review

- **Advanced Settings:**
  - Customizable cost components
  - Enable/disable specific cost items
  - Adjust multipliers for different scenarios

## Architecture

The application follows a layered architecture with clear separation of concerns:

```
Frontend (Streamlit)
    ↓ HTTP/JSON
Application Layer (Flask)
    ↓ Domain Services/Entities
Domain Layer (Core Business Logic)
    ↓ Repository Interfaces
Infrastructure Layer (SQLite DB, OpenAI)
```

For detailed architecture information, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Technology Stack

- **Frontend**: Streamlit
- **Backend**: Flask with RESTful API
- **Database**: SQLite
- **AI Integration**: OpenAI API
- **Testing**: Pytest suite
- **Logging**: Structlog

## Documentation

Detailed documentation is available in the `docs/` directory:

- [Architecture Overview](docs/ARCHITECTURE.md)
- [Project Scope](docs/SCOPE.md) - Defines project boundaries, core features, and POC limitations
- [Entity Definitions](docs/ENTITIES.md)
- [Service Documentation](docs/SERVICES.md)
- [API Endpoints](docs/ENDPOINTS.md)
- [Frontend Guide](docs/FRONTEND_GUIDE.md)
- [Developer Guide](docs/DEVELOPER_GUIDE.md)
- [Testing Infrastructure](docs/TESTING_INFRASTRUCTURE.md) - Comprehensive testing setup, methodologies, and guidelines

## Quick Start

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

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your OpenAI API key
```

### Running the Application

1. Start the backend server:
```bash
cd backend
python app.py
```

2. Start the Streamlit frontend:
```bash
cd frontend
streamlit run app.py
```

Access the application:
- Frontend: http://localhost:8501
- Backend API: http://localhost:5000

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_entities.py -v
python -m pytest tests/test_services.py -v
python -m pytest tests/test_documentation.py -v
```

## Project Structure

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
├── docs/                 # Documentation
└── requirements.txt      # Python dependencies
```

## Contributing

Please refer to our [Developer Guide](docs/DEVELOPER_GUIDE.md) for:
- Coding standards
- Testing requirements
- Contribution workflow
- Pull request process

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
