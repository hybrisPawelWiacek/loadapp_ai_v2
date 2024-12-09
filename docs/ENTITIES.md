# Domain Entities Documentation

This document describes the core domain entities in the LoadApp.AI system, their relationships, and how they are used throughout the application.

## Core Entities

### Route
**Purpose:** Represents a complete transportation route including empty driving, main route, and timeline of events.

**Fields:**
- `id` (UUID): Unique identifier
- `origin` (Location): Starting point
- `destination` (Location): End point
- `pickup_time` (datetime): Scheduled cargo pickup time
- `delivery_time` (datetime): Scheduled cargo delivery time
- `empty_driving` (EmptyDriving): Empty driving details
- `main_route` (MainRoute): Main transportation route details
- `timeline` (List[TimelineEvent]): Sequence of events during transport
- `total_duration_hours` (float): Total route duration
- `is_feasible` (bool): Route feasibility flag
- `duration_validation` (bool): Timeline validation status

**Relationships:**
- Contains Location objects for origin and destination
- Contains EmptyDriving and MainRoute objects
- Referenced by Offer entity
- References TruckDriverPair and TransportType for capacity planning

### Offer
**Purpose:** Represents a price quote for cargo transportation, including cost breakdown and fun facts.

**Fields:**
- `id` (UUID): Unique identifier
- `route_id` (UUID): Reference to associated route
- `total_cost` (float): Calculated transportation cost
- `margin` (float): Applied profit margin
- `final_price` (float): Total price including margin
- `fun_fact` (str): AI-generated transport-related fun fact
- `status` (str): Current offer status
- `created_at` (datetime): Offer creation timestamp
- `cost_breakdown` (Dict[str, float]): Detailed cost components

**Relationships:**
- References Route through route_id
- Associated with multiple CostItems through cost_breakdown
- Links offers to BusinessEntity for organizational context

### Cargo
**Purpose:** Describes the goods being transported.

**Fields:**
- `id` (UUID): Unique identifier
- `type` (str): Type of cargo
- `weight` (float): Cargo weight
- `value` (float): Cargo value
- `special_requirements` (List[str]): Special handling requirements

**Relationships:**
- Referenced by Route for transportation planning
- Influences cost calculations through special requirements

### TimelineEvent
**Purpose:** Represents significant events during transport.

**Fields:**
- `type` (str): Type of event ('start', 'pickup', 'rest', 'border', 'delivery', 'end')
- `location` (Location): Event location
- `time` (datetime): Scheduled event time
- `duration_minutes` (int): Event duration
- `description` (str): Event details
- `is_required` (bool): Mandatory event flag

**Relationships:**
- Contains Location object
- Part of Route's timeline

### CostItem
**Purpose:** Represents individual cost components in transportation pricing.

**Fields:**
- `id` (UUID): Unique identifier
- `type` (str): Cost type
- `category` (str): Cost category
- `base_value` (float): Base cost amount
- `multiplier` (float): Cost adjustment factor
- `currency` (str): Cost currency (default: "EUR")
- `is_enabled` (bool): Cost item activation status
- `description` (str): Cost item description

**Relationships:**
- Aggregated in Offer's cost_breakdown
- Used by CostCalculationService for pricing

### Location
**Purpose:** Represents a geographical location with address.

**Fields:**
- `latitude` (float): Geographic latitude
- `longitude` (float): Geographic longitude
- `address` (str): Human-readable address

**Relationships:**
- Used by Route for origin/destination
- Used by TimelineEvent for event locations

### User
**Purpose:** Represents a system user with associated permissions.

**Fields:**
- `id` (UUID): Unique identifier
- `name` (str): User's name
- `role` (str): User role (default: "transport_manager")
- `permissions` (List[str]): List of user permissions

**Relationships:**
- Associated with BusinessEntity for organization context
- Referenced by audit logs and activity tracking

### BusinessEntity
**Purpose:** Represents a business organization in the system.

**Fields:**
- `id` (UUID): Unique identifier
- `name` (str): Business name
- `type` (str): Organization type
- `operating_countries` (List[str]): Countries of operation

**Relationships:**
- Associated with Users for organizational context
- Referenced in transport operations and offers
- Applies business-specific pricing rules in CostCalculationService

### TruckDriverPair
**Purpose:** Represents a truck and driver combination for transport.

**Fields:**
- `id` (UUID): Unique identifier
- `truck_type` (str): Type of truck
- `driver_id` (str): Driver identifier
- `capacity` (float): Cargo capacity
- `availability` (bool): Current availability status

**Relationships:**
- Referenced by Route for transport planning
- Associated with transport operations

### TransportType
**Purpose:** Defines a type of transport with its capabilities.

**Fields:**
- `id` (UUID): Unique identifier
- `name` (str): Transport type name
- `capacity` (Capacity): Cargo capacity details
- `restrictions` (List[str]): Transport restrictions

**Relationships:**
- Referenced by Route for transport planning
- Used in cost calculations

### ServiceError
**Purpose:** Represents an error condition in the system.

**Fields:**
- `code` (str): Error code
- `message` (str): Error message
- `details` (Dict[str, Any]): Additional error details
- `timestamp` (datetime): Error occurrence time

**Relationships:**
- Used across all services for error handling
- Associated with audit logging

## Database Models

### CostSettings
**Purpose:** Stores configuration for cost calculations and pricing.

**Fields:**
- `id` (Integer): Primary key
- `cost_per_token` (Float): Cost per token for calculations
- `base_cost` (Float): Base cost for operations
- `currency` (String): Currency code (e.g., 'USD')
- `created_at` (DateTime): Record creation timestamp
- `updated_at` (DateTime): Last update timestamp

### LoadTest
**Purpose:** Represents a load testing session configuration.

**Fields:**
- `id` (Integer): Primary key
- `name` (String): Test name
- `description` (String): Test description
- `status` (String): Test status (pending, running, completed, failed)
- `created_at` (DateTime): Test creation timestamp
- `updated_at` (DateTime): Last update timestamp

**Relationships:**
- Has many LoadTestResults

### LoadTestResult
**Purpose:** Stores individual load test results.

**Fields:**
- `id` (Integer): Primary key
- `load_test_id` (Integer): Foreign key to LoadTest
- `response_time` (Float): Request response time
- `status_code` (Integer): HTTP status code
- `error_message` (String): Error message if any
- `timestamp` (DateTime): Result timestamp

**Relationships:**
- Belongs to LoadTest

## Service Entities

### RoutePlanningService
**Purpose:** Handles route planning and optimization.

**Relationships:**
- Uses Route entities for transportation planning
- Manages TimelineEvent sequences
- Integrates with Location services
- Coordinates with TruckDriverPair allocation
- Validates routes against BusinessEntity operating countries
- Ensures TransportType compatibility

### CostCalculationService
**Purpose:** Manages cost calculations and pricing.

**Relationships:**
- Processes CostItem configurations
- Integrates with Route planning
- Applies BusinessEntity pricing rules
- Handles TransportType-specific costs
- Calculates empty driving costs
- Validates cost items against business rules

### OfferService
**Purpose:** Generates and manages transportation offers.

**Relationships:**
- Creates and maintains Offer entities
- Coordinates with Route planning
- Integrates with cost calculations
- Manages business relationships
- Tracks offer lifecycle states
- Handles AI integration for fun facts

## Usage in Services

### RoutePlanningService
- Uses Route, Location, and TimelineEvent entities to plan transportation routes
- Validates route feasibility and timeline consistency
- Handles empty driving calculations
- References TruckDriverPair and TransportType for capacity planning
- Considers BusinessEntity operating countries for route validation
- Ensures all timeline events are properly sequenced
- Validates pickup and delivery times
- Manages route optimization constraints

### CostCalculationService
- Uses CostItem entities to calculate transportation costs
- Considers cargo special requirements and route characteristics
- Aggregates costs for final offer generation
- Applies business-specific pricing rules based on BusinessEntity
- Factors in TransportType-specific costs
- Handles currency conversions and regional pricing
- Manages cost breakdowns and summaries
- Validates cost calculations against business rules

### OfferService
- Creates Offer entities with calculated prices and margins
- Associates offers with routes and cost breakdowns
- Integrates AI-generated fun facts
- Links offers to BusinessEntity for organizational context
- Tracks offer status and history
- Manages offer versions and updates
- Handles offer expiration and renewal
- Coordinates with external pricing services

## Usage in Endpoints

### Route Planning Endpoints
- Accept Location and Cargo details for route planning
- Return Route objects with complete timeline and feasibility assessment

### Cost Calculation Endpoints
- Accept Route details and return CostItem breakdowns
- Allow modification of cost parameters through CostItem updates

### Offer Generation Endpoints
- Accept Route and cost details to generate Offer objects
- Return complete offers with pricing and fun facts

## Data Flow Example

1. User inputs cargo details (Cargo entity) and locations (Location entities)
2. System creates Route with TimelineEvents
3. CostItems are calculated based on route and cargo details
4. Final Offer is generated with cost breakdown and fun fact
5. All entities are persisted in the database for future reference
