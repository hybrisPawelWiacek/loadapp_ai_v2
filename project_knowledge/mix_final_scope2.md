# LoadApp.AI PoC System Specification (Final Version)

## 1. Overview

LoadApp.AI PoC is a simplified prototype enabling transport managers to quickly plan routes, calculate costs, and generate offers for cargo transportation requests. This specification maintains a focused approach while incorporating all essential features for the PoC phase.

## 2. Core Principles

### Domain-Driven Design (DDD)
- Domain logic encapsulated within domain models and services
- Clear separation from application and infrastructure layers
- Strong emphasis on domain model integrity

### Layered Architecture
```
Frontend (Streamlit)
    ↓ HTTP/JSON
Application Layer (Flask)
    ↓ Domain Objects
Domain Layer (Core Business Logic)
    ↓ Repository Interface
Infrastructure Layer (SQLite, External Services)
```

### Development Philosophy
- Clear separation between mocked and implemented features
- Simple, maintainable implementations
- Structured logging and basic performance metrics
- Clear upgrade paths for future enhancements

## 3. Domain Model

### Core Entities

```python
@dataclass
class TimelineEvent:
    """Represents any event in route timeline"""
    event_type: str  # 'start', 'pickup', 'rest', 'border', 'delivery', 'end'
    location: Location
    planned_time: datetime
    duration_minutes: int
    description: str
    is_required: bool

@dataclass
class User:
    """For PoC: Single static user (John Doe)"""
    id: UUID
    name: str
    role: str = "transport_manager"
    permissions: List[str] = field(default_factory=lambda: ["full_access"])

@dataclass
class BusinessEntity:
    """For PoC: Single static entity"""
    id: UUID
    name: str
    type: str
    operating_countries: List[str]

@dataclass
class TruckDriverPair:
    """For PoC: Static configuration data"""
    id: UUID
    truck_type: str
    driver_id: str
    capacity: float
    availability: bool = True

@dataclass
class TransportType:
    id: UUID
    name: str
    capacity: Capacity
    restrictions: List[str]

@dataclass
class Cargo:
    id: UUID
    type: str
    weight: float
    value: float
    special_requirements: List[str]

@dataclass
class Route:
    id: UUID
    origin: Location
    destination: Location
    pickup_time: datetime
    delivery_time: datetime
    empty_driving: EmptyDriving  # Fixed 200km/4h for PoC
    main_route: MainRoute
    timeline: List[TimelineEvent]
    total_duration_hours: float
    is_feasible: bool = True  # Always true for PoC
    duration_validation: bool

@dataclass
class CostItem:
    id: UUID
    type: str
    category: str  # For organizing in Advanced Cost Settings
    base_value: float
    multiplier: float = 1.0
    currency: str = "EUR"
    is_enabled: bool = True
    description: str

@dataclass
class Offer:
    id: UUID
    route_id: UUID
    total_cost: float
    margin: float
    final_price: float
    fun_fact: str
    status: str
    created_at: datetime
    cost_breakdown: Dict[str, float]
```

### Value Objects

```python
@dataclass
class Location:
    latitude: float
    longitude: str
    address: str

@dataclass
class EmptyDriving:
    """Fixed values for PoC"""
    distance_km: float = 200.0
    duration_hours: float = 4.0
    base_cost: float = 100.0

@dataclass
class MainRoute:
    distance_km: float
    duration_hours: float
    country_segments: List[CountrySegment]

@dataclass
class RouteStop:
    type: str  # 'rest', 'border', 'fuel'
    location: Location
    duration_minutes: int

@dataclass
class ServiceError:
    code: str
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    severity: ErrorSeverity

class ErrorResponse:
    error: ServiceError
    suggestions: List[str]
    retry_after: Optional[int]
```

### Domain Services

```python
class RoutePlanningService:
    def calculate_route(
        self,
        origin: Location,
        destination: Location,
        transport_type: TransportType,
        cargo: Cargo,
        pickup_time: datetime,
        delivery_time: datetime
    ) -> Route:
        """
        Calculates complete route including:
        - Empty driving segment
        - Main route from Google Maps
        - Timeline generation with all stops
        - Basic duration validation
        """
        
    def validate_timeline(
        self,
        timeline: List[TimelineEvent],
        pickup_time: datetime,
        delivery_time: datetime
    ) -> bool:
        """Validates if route timeline fits within constraints"""

class CostCalculationService:
    def calculate_total_cost(
        self,
        route: Route,
        transport_type: TransportType,
        cargo: Cargo,
        enabled_cost_items: List[str] = None
    ) -> Dict[str, float]:
        """
        Calculates costs including:
        - Selective cost item inclusion
        - Time-based costs
        - Detailed cost categorization
        """
        
    def get_available_cost_items(self) -> List[CostItem]:
        """Returns all possible cost items for settings page"""

class OfferService:
    def generate_offer(
        self,
        route: Route,
        costs: Dict[str, float],
        margin: float
    ) -> Offer:
        """
        Creates offer including:
        - Detailed cost breakdown
        - Fun fact generation
        - Creation timestamp
        """
        
    def get_historical_offers(
        self,
        limit: int = 50
    ) -> List[Offer]:
        """Retrieves historical offers for review page"""
```

## 4. User Interface Components

### Main Page Components
```python
class RouteInputForm:
    """Main input form"""
    components = {
        'locations': {
            'origin_input': TextField,
            'destination_input': TextField
        },
        'timing': {
            'pickup_datetime': DateTimePicker,
            'delivery_datetime': DateTimePicker
        },
        'cargo': {
            'type_selector': Dropdown,
            'weight_input': NumberField,
            'requirements': MultiSelect
        }
    }

class RouteDisplay:
    """Route visualization"""
    components = {
        'map_view': GoogleMapComponent,
        'timeline_view': {
            'events_list': TimelineList,
            'duration_validation': ValidationDisplay
        },
        'loading_state': {
            'spinner': StreamlitSpinner,
            'fun_fact_display': TextDisplay
        }
    }
```

### Offer Review Page
```python
class OfferReviewPage:
    """Historical offers review interface"""
    layout = {
        'left_sidebar': {
            'route_list': ScrollableList,
            'filters': FilterPanel
        },
        'main_content': {
            'tabs': {
                'route_tab': {
                    'map': GoogleMapComponent,
                    'timeline': TimelineDisplay,
                    'validation': ValidationResults
                },
                'costs_tab': {
                    'breakdown': CostBreakdown,
                    'charts': CostCharts
                },
                'offer_tab': {
                    'details': OfferDetails,
                    'fun_fact': FunFactDisplay
                }
            }
        }
    }
```

### Advanced Cost Settings Page
```python
class AdvancedCostSettings:
    """Cost management interface"""
    layout = {
        'left_panel': {
            'categories': CostCategoryList,
            'search': SearchBar
        },
        'right_panel': {
            'editor': {
                'cost_toggle': ToggleSwitch,
                'value_input': NumberInput,
                'multiplier_input': NumberInput
            },
            'description': MarkdownDisplay,
            'summary': CostSummary
        }
    }
```

## 5. Implementation Scope

### Real Implementations

1. **Route Planning**
   - Google Maps API integration
   - Basic distance/duration calculation
   - Timeline generation
   - Cost aggregation logic
   - Performance metrics logging

2. **Cost Calculation**
   - Component-based calculation
   - User-adjustable cost items
   - Margin application
   - Currency handling
   - Time-based cost factors

3. **Offer Generation**
   - OpenAI API integration for fun facts
   - Offer data persistence
   - Cost breakdown display
   - Basic error handling

4. **Data Management**
   - SQLite database
   - Basic CRUD operations
   - Historical data access
   - Data validation

### Mocked Components

1. **Empty Driving**
```python
MOCK_EMPTY_DRIVING = {
    "distance_km": 200,
    "duration_hours": 4,
    "base_cost": 100
}
```

2. **User & Business Entity**
```python
MOCK_USER = {
    "id": "user1",
    "name": "John Doe",
    "role": "transport_manager"
}

MOCK_BUSINESS = {
    "id": "business1",
    "name": "Sample Transport Co."
}
```

3. **Static Data**
```python
# Loaded from JSON files
MOCK_FUEL_PRICES = {...}
MOCK_TOLL_COSTS = {...}
MOCK_BUSINESS_COSTS = {...}
```

4. **Feasibility Checks**
```python
def check_feasibility(route: Route) -> bool:
    return True  # Always feasible in PoC
```

5. **Timeline Validation**
```python
def validate_route_timeline(route: Route) -> bool:
    logger.info(f"Timeline validation for route {route.id}")
    return True
```

6. **Time-based Costs**
```python
MOCK_TIME_COSTS = {
    "overnight": 50.0,
    "weekend": 100.0,
    "holiday": 150.0
}
```

## 6. Database Schema

```sql
CREATE TABLE routes (
    id TEXT PRIMARY KEY,
    origin_location TEXT,
    destination_location TEXT,
    pickup_time TIMESTAMP,
    delivery_time TIMESTAMP,
    timeline_json TEXT,
    status TEXT,
    created_at TIMESTAMP
);

CREATE TABLE offers (
    id TEXT PRIMARY KEY,
    route_id TEXT,
    total_cost REAL,
    margin REAL,
    final_price REAL,
    fun_fact TEXT,
    cost_breakdown_json TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY (route_id) REFERENCES routes(id)
);

CREATE TABLE cost_settings (
    id TEXT PRIMARY KEY,
    category TEXT,
    type TEXT,
    base_value REAL,
    multiplier REAL,
    is_enabled BOOLEAN,
    last_modified TIMESTAMP
);
```

## 7. Technical Implementation

### Project Structure
```
loadapp/
├── app.py                  # Main entry point
├── frontend/              
│   └── streamlit_app.py    # Streamlit UI
├── backend/
│   ├── flask_app.py        # Flask API
│   ├── domain/            
│   │   ├── entities/       # Domain classes
│   │   └── services/       # Domain services
│   └── infrastructure/
│       ├── repositories/   # SQLite repos
│       └── external/       # API clients
└── tests/
```

### Performance Monitoring
```python
@dataclass
class PerformanceMetrics:
    route_calculation_ms: int
    cost_calculation_ms: int
    offer_generation_ms: int
    api_response_ms: int
    timeline_calculation_ms: int
    historical_data_retrieval_ms: int
    cost_settings_update_ms: int
    database_operation_ms: int

class MetricsLogger:
    """Logging for all operations"""
    def log_operation_metrics(
        self,
        operation_type: str,
        duration_ms: int,
        success: bool,
        details: Dict[str, Any]
    ):
        """Logs operational metrics with structured data"""
```

## 8. Development & Deployment

### Local Development
- Run Flask backend locally
- Run Streamlit UI locally
- SQLite database file in project directory
- Environment variables for API keys

### Testing Strategy
```python
def test_route_calculation():
    service = RoutePlanningService(use_mock=True)
    route = service.calculate_route(...)
    assert route.empty_driving.distance_km == 200
    assert route.is_feasible == True

def test_cost_calculation():
    service = CostCalculationService(use_mock=True)
    costs = service.calculate_total_cost(...)
    assert "fuel" in costs
    assert "tolls" in costs
```

### Post-PoC Deployment
- Code hosted on GitHub
- Replit deployment for preview environment
- Basic monitoring of performance metrics
- Structured logging in JSON format

## 9. Future Evolution Path

### Near-term Enhancements
- Replace fixed empty driving with dynamic calculation
- Implement actual feasibility checks
- Add more sophisticated cost calculations
- Enhanced timeline validation

### Long-term Vision
- Full route optimization
- Real-time data integration
- Advanced AI capabilities
- Multi-user support
- Dynamic cost optimization
