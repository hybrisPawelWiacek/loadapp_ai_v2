# LoadApp.AI PoC System Specification (Final Version)

## 1. Overview

LoadApp.AI PoC is a simplified prototype enabling transport managers to quickly plan routes, incorporate pickup/delivery times, calculate costs (including empty driving), and generate offers for cargo transportation requests. The PoC demonstrates core functionalities in a structured, domain-driven design while setting the stage for eventual expansion into a fully featured application.

This specification integrates both the Product Requirements Document (PRD) and the System Architecture and Implementation Plan, ensuring that business objectives and technical designs are aligned.

---

## 2. Core Principles

### Domain-Driven Design (DDD)
- Encapsulate domain logic within domain models and services.
- Maintain clear boundaries between domain, application, and infrastructure layers.
- Prioritize domain model integrity and clarity for future extensibility.

### Layered Architecture
```
Frontend (Streamlit)
    ↓ HTTP/JSON
Application Layer (Flask)
    ↓ Domain Services/Entities
Domain Layer (Core Business Logic)
    ↓ Repository Interfaces
Infrastructure Layer (SQLite DB, External Services)
```

### Development Philosophy
- Start simple with mocked data and basic logic; ensure paths to scalability.
- Use structured logging and basic test coverage to maintain code quality.
- Implement a flexible architecture that can accommodate advanced features (AI-driven route optimization, real-time data integration) in later iterations.
- Deploy locally during development, eventually host a preview on Replit from GitHub after PoC completion.
- Use SQLite as the primary database during PoC for simplicity.

### AI Integration
- Integrate AI features via direct calls to OpenAI API to generate a "fun fact" about AI and transport.
- No complex AI orchestration (like CrewAI) at this stage, just a mocked integration.

---

## 3. Product Requirements Document Highlights

### Key Business Needs

- **Quick Decision Making:** Transport managers need a simple interface to input cargo and route details (including pickup/delivery times) and quickly get cost and feasibility estimates.
- **Cost Calculation:** Aggregate multiple cost factors—fuel, tolls, driver wages, compliance, cargo-specific handling—into a transparent and adjustable cost breakdown.
- **Offer Generation:** Produce a final price based on total costs plus a margin, accompanied by a fun fact from the AI service.
- **Data Storage & Review:** Store route and offer data in SQLite for future reference and review. Provide a page to review previously generated offers and their associated routes/costs.

### PoC Scope

- **Input:** From/To location, cargo details, transport type, pickup/delivery date/time.
- **Route Planning (Mocked):** Assume a fixed empty driving scenario (200 km/4h) plus a main route from a mocked Google Maps data. Always feasible in PoC.
- **Cost Calculation:** Compute a total cost including empty driving and main route. Allow user to tweak cost items in advanced settings.
- **Offer Generation:** Add a user-defined margin, request fun fact from OpenAI, produce final offer.
- **Review & Visualization:** Show route details, costs, and offers. Include a fun fact displayed during loading and after generation.
- **Advanced Settings:** Let user enable/disable or adjust cost items.

### Future Evolution

- Introduce real compliance checks, dynamic feasibility validations, multiple user roles, historical data analysis, and AI-driven route optimization in future phases.

---

## 4. System Architecture and Implementation Plan (PoC)

### High-Level Architecture

```
 ┌─────────────────┐         ┌──────────────────┐
 │  Streamlit UI    │  HTTP   │  Flask API        │
 │ (Frontend)       ├─────────┤  (Backend)       │
 └───┬──────────────┘         └───────┬──────────┘
     │                                │
     │                                │
     │                                │
     ▼                                ▼
 ┌──────────┐                 ┌────────────────┐
 │OpenAI API │                 │Domain Services │
 │(Fun Fact) │                 │+ Repositories  │
 └─────┬─────┘                 └─────┬─────────┘
       │                              │
       ▼                              ▼
                             ┌────────────────┐
                             │   SQLite DB     │
                             └────────────────┘
```

### Domain Model

**Key Entities:**

```python
@dataclass
class TimelineEvent:
    event_type: str  # 'start', 'pickup', 'rest', 'border', 'delivery', 'end'
    location: 'Location'
    planned_time: datetime
    duration_minutes: int
    description: str
    is_required: bool

@dataclass
class User:
    id: UUID
    name: str
    role: str = "transport_manager"
    permissions: List[str] = field(default_factory=lambda: ["full_access"])

@dataclass
class BusinessEntity:
    id: UUID
    name: str
    type: str
    operating_countries: List[str]

@dataclass
class TruckDriverPair:
    id: UUID
    truck_type: str
    driver_id: str
    capacity: float
    availability: bool = True

@dataclass
class TransportType:
    id: UUID
    name: str
    capacity: 'Capacity'
    restrictions: List[str]

@dataclass
class Cargo:
    id: UUID
    type: str
    weight: float
    value: float
    special_requirements: List[str]

@dataclass
class EmptyDriving:
    distance_km: float = 200.0
    duration_hours: float = 4.0
    base_cost: float = 100.0

@dataclass
class MainRoute:
    distance_km: float
    duration_hours: float
    country_segments: List['CountrySegment']

@dataclass
class Route:
    id: UUID
    origin: 'Location'
    destination: 'Location'
    pickup_time: datetime
    delivery_time: datetime
    empty_driving: EmptyDriving
    main_route: MainRoute
    timeline: List[TimelineEvent]
    total_duration_hours: float
    is_feasible: bool = True
    duration_validation: bool = True

@dataclass
class CostItem:
    id: UUID
    type: str
    category: str
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

@dataclass
class Location:
    latitude: float
    longitude: float
    address: str

@dataclass
class ServiceError:
    code: str
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    severity: str
```

**Domain Services:**

```python
class RoutePlanningService:
    def calculate_route(...):
        # Returns a Route object with timeline and durations
        pass

    def validate_timeline(...):
        # Returns boolean feasibility
        pass

class CostCalculationService:
    def calculate_total_cost(...):
        # Computes and returns a dict of cost items
        pass

    def get_available_cost_items(...):
        # Returns all configurable cost items
        pass

class OfferService:
    def generate_offer(...):
        # Uses AI service for fun fact, stores offer in DB
        pass

    def get_historical_offers(...):
        # Fetches past offers from DB
        pass
```

### UI Components

- **Homepage (Streamlit):** Input route/cargo/time, generate route, show costs, generate offer (with fun fact).
- **Offer Review Page:** Browse historical offers and routes.
- **Advanced Cost Settings Page:** Enable/disable and edit cost items before final cost calculation.

### Mocked Components

- Empty driving fixed to 200 km / 4h.
- Feasibility always returns true.
- Fuel prices, tolls, compliance costs are static data loaded from JSON.
- Fun fact generated by directly calling OpenAI API (with a simple prompt).

### Database (SQLite)

**Schema:**

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

---

## 5. Implementation Plan

**Phase 1: Setup & Infrastructure**  
- Initialize GitHub repo, define Python environment (Streamlit, Flask).
- Implement domain classes and skeleton services.
- Set up SQLite DB and migrations.

**Phase 2: Mock Data & Basic Logic**  
- Hardcode empty driving and route feasibility.  
- Implement cost calculation service with static cost items.  
- Offer service to integrate margin and fun fact via OpenAI API.

**Phase 3: Frontend Integration**  
- Streamlit pages for input, route display, cost calculation, offer generation.  
- Offer review and advanced cost settings pages.

**Phase 4: Testing & Logging**  
- Unit tests for services and integration tests for Flask endpoints.  
- Structured logging for each API request and major operation.

**Phase 5: Deployment**  
- Run locally during development.  
- After PoC completion, deploy to Replit from GitHub for preview.

---

## 6. Additional Requirements Consideration

1. **Local Deployment & Replit:**  
   - During PoC dev: run `flask_app.py` locally, run `streamlit_app.py` locally.
   - After completion: push to GitHub, configure Replit to run both backend and frontend for a preview environment.

2. **SQLite Database:**  
   - Use SQLite for simplicity.  
   - Store routes, offers, and cost settings.  
   - Seed mock data at startup.

3. **Development with AI Dev Agent:**  
   - The PoC will be developed by prompting an AI Dev Agent that can read both this System Specification and the PRD (combined in this document).  
   - The agent will implement backend or frontend features step by step, ensuring consistency with the domain model, architecture, and requirements described here.  
   - By providing a unified, comprehensive specification, the AI Dev Agent can maintain full context and alignment with the outlined architecture at every prompt, minimizing misinterpretation and rework.
