# Domain Services Documentation

This document describes the core domain services in the LoadApp.AI system, their responsibilities, methods, and integrations.

## Core Services

### RoutePlanningService

**Purpose:** Handles route planning, optimization, and feasibility validation for cargo transportation, with special focus on EU regulations compliance.

**Key Responsibilities:**
- Route generation and optimization
- Timeline event sequencing with EU regulation compliance
- Empty driving calculations
- Feasibility validation
- Capacity planning
- Rest period scheduling
- Loading window validation

**Key Constants:**
```python
MAX_DAILY_DRIVING_HOURS = 9  # EU regulation
REQUIRED_REST_AFTER_HOURS = 4.5  # EU regulation
MIN_REST_DURATION_HOURS = 0.75  # 45 minutes
LOADING_WINDOW_START = 6  # 6 AM
LOADING_WINDOW_END = 22  # 10 PM
```

**Methods:**
```python
def calculate_route(
    origin: Location,
    destination: Location,
    pickup_time: datetime,  # Must be timezone-aware
    delivery_time: datetime,  # Must be timezone-aware
    cargo: Optional[Cargo] = None,
    transport_type: Optional[TransportType] = None
) -> Route:
    """Generate an optimized route with timeline and EU regulation compliance."""

def _validate_basic_timeline(pickup_time: datetime, delivery_time: datetime) -> None:
    """Validate basic timeline constraints."""

def _validate_loading_window(pickup_time: datetime) -> None:
    """Validate that loading occurs within allowed time window."""

def _generate_timeline(
    origin: Location,
    destination: Location,
    pickup_time: datetime,
    delivery_time: datetime,
    empty_driving: EmptyDriving,
    main_route: MainRoute
) -> List[TimelineEvent]:
    """Create timeline of transport events with required rest periods."""
```

**Timeline Events:**
The service now uses a structured TimelineEvent class:
```python
@dataclass
class TimelineEvent:
    event_type: str  # start, pickup, rest, border_crossing, delivery
    time: datetime   # Timezone-aware
    location: Location
    duration: Optional[float] = None  # Duration in hours
    notes: Optional[str] = None
```

**Logging:**
- INFO: Route planning attempts, successful route generation, rest period calculations
- WARN: Feasibility issues, timeline conflicts, regulation violations
- ERROR: Route planning failures, validation errors, timezone issues
- DEBUG: Empty driving calculations, timeline generation details, rest stop planning

### CostCalculationService

**Purpose:** Manages all cost-related calculations and pricing logic.

**Key Features:**
- Calculates total costs based on route distance and duration
- Handles empty driving costs separately
- Uses fixed rates for initial implementation:
  - Base cost: €500.00
  - Distance rate: €0.50 per kilometer
  - Time rate: €50.00 per hour
  - Empty driving rate: €0.30 per kilometer

**Main Methods:**
```python
def calculate_total_cost(route: Route) -> Dict:
    """Calculate total transportation cost and cost breakdown."""
```

**Logging:**
- Extensive logging added throughout the calculation process:
  - Route distances (main route and empty driving)
  - Route duration
  - Cost calculation steps
  - Any errors that occur

**Future Enhancements:**
- Re-implement detailed cost breakdowns
- Add country-specific cost calculations
- Support for different cargo types and requirements
- Custom rate configurations

### OfferService

**Purpose:** Handles offer generation, management, and AI integration for transport offers.

**Key Responsibilities:**
- Offer creation and management
- Margin calculations
- AI-powered fun fact generation
- Offer status tracking
- Cost breakdown management
- Currency handling

**Methods:**
```python
def generate_offer(
    self,
    route: Route,
    cost_breakdown: Dict[str, float],
    margin_percentage: float = 10.0,
    currency: str = "EUR"
) -> Offer:
    """Generate an offer with fun fact and proper cost calculations."""

def get_offer(self, offer_id: str) -> Optional[Offer]:
    """Retrieve an offer by ID."""

def list_offers(
    self,
    limit: int = 10,
    offset: int = 0
) -> list[Offer]:
    """List offers with pagination support."""
```

**Offer Structure:**
```python
@dataclass
class Offer:
    id: UUID
    route_id: UUID
    total_cost: float
    margin: float
    final_price: float
    cost_breakdown: Dict[str, float]
    fun_fact: Optional[str]
    status: str = "active"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
```

**Error Handling:**
- Graceful handling of AI service failures
- Proper database error management
- Input validation for costs and margins
- Timezone-aware datetime handling

**Logging:**
- INFO: Offer generation, retrieval, and listing operations
- WARN: AI service issues, margin anomalies
- ERROR: Database errors, validation failures
- DEBUG: Cost calculations, fun fact generation details

### MetricsLogger

**Purpose:** Handles system-wide metrics collection, aggregation, and alert management.

**Key Responsibilities:**
- Metrics collection and buffering
- Metric aggregation over time windows
- Alert rule management and evaluation
- Active alert tracking and resolution

**Methods:**
```python
def log_metric(metric_name: str, value: float, tags: Dict[str, str]) -> None:
    """Log a metric value with associated tags."""

def flush_metrics() -> None:
    """Flush buffered metrics to storage."""

def create_alert_rule(name: str, metric_name: str, condition: str,
                     threshold: float, window_minutes: int) -> AlertRule:
    """Create a new alert rule."""

def get_active_alerts() -> List[Alert]:
    """Retrieve currently active alerts."""
```

**Logging:**
- INFO: Metric logging, alert creation/resolution
- WARN: Alert triggers, metric anomalies
- ERROR: Metric logging failures, alert evaluation errors
- DEBUG: Metric aggregation details, alert evaluation conditions

## Infrastructure Integration

### Database Integration

The services interact with the database through repository interfaces:

```python
class RouteRepository:
    """Handles Route entity persistence."""
    def save(self, route: Route) -> Route
    def find_by_id(self, route_id: UUID) -> Optional[Route]
    def find_all() -> List[Route]

class OfferRepository:
    """Handles Offer entity persistence."""
    def save(self, offer: Offer) -> Offer
    def find_by_id(self, offer_id: UUID) -> Optional[Offer]
    def find_by_route_id(self, route_id: UUID) -> List[Offer]

class CostItemRepository:
    """Handles CostItem entity persistence."""
    def save(self, cost_item: CostItem) -> CostItem
    def find_all() -> List[CostItem]
    def find_by_category(self, category: str) -> List[CostItem]
```

### AI Integration

The OfferService integrates with OpenAI for fun fact generation:

```python
class AIService:
    """Handles AI service integration."""
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def generate_fun_fact(self) -> str:
        """Generate transport-related fun fact."""
        prompt = "Generate a fun fact about transportation or logistics"
        response = self.client.completions.create(
            model="gpt-3.5-turbo",
            prompt=prompt,
            max_tokens=100
        )
        return response.choices[0].text.strip()
```

### Logging Strategy

The system uses a structured logging approach:

1. **Log Levels:**
   - DEBUG: Detailed information for debugging
   - INFO: General operational information
   - WARN: Warning messages for potential issues
   - ERROR: Error conditions requiring attention

2. **Log Structure:**
   ```python
   {
       "timestamp": "ISO-8601 timestamp",
       "level": "INFO|WARN|ERROR|DEBUG",
       "service": "ServiceName",
       "method": "MethodName",
       "message": "Log message",
       "data": {
           "relevant": "contextual data",
           "entity_id": "associated entity ID"
       }
   }
   ```

3. **Logging Practices:**
   - Each service method logs entry and exit points
   - All exceptions are logged with stack traces
   - Business rule violations are logged as WARN
   - Performance metrics are logged as INFO
   - Sensitive data is never logged

4. **Log Storage:**
   - Development: Console output
   - Production: File-based logging (future)
