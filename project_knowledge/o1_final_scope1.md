# LoadApp.AI Product Requirements Document

## 1. Basic Principles

**Goal:**  
LoadApp.AI aims to enable transport managers to quickly and efficiently determine the feasibility, cost, and optimal pricing of a given freight route request. It addresses complexities in long-distance trucking logistics, including cargo details, truck/driver availability, compliance requirements, margin constraints, and timing considerations (pickup/delivery schedule).

**Key Guiding Principles:**  
- **User-Centric & Time-Aware:** The app should make it easy for transport managers to input route details, cargo specifics, and pickup/delivery windows, and quickly produce an optimized cost and price offer.  
- **Data Aggregation & Automation:** Aggregate data from multiple sources (e.g., route planning, compliance rules, cost databases, fuel prices) to reduce manual calculations.  
- **Scalability & Extensibility:** Architect for future integration of advanced route optimization, dynamic compliance checks, real-time data updates, and AI-driven suggestions.  
- **Transparency & Trust:** Provide clear cost breakdowns, timing details (including empty driving to pickup point), and compliance validations so managers trust and understand the recommendations.

---

## 2. Target Vision Description

**Long-Term Vision:**  
In the fully developed LoadApp.AI:

- **Dynamic Route & Timing Management:** The system will automatically factor in pickup/delivery time windows, driver rest and working time compliance, border crossings, and other route constraints. It will consider repositioning the truck (empty driving) to the pickup location as part of the overall operation.
- **Advanced Compliance & Feasibility:** The system will dynamically validate route feasibility against all constraints (e.g., does the truck and driver arrive on time, are all compliance requirements met?). Compliance checks will be informed by AI and regulatory data sources.
- **Cost Optimization & Offer Generation:** The system will integrate with various APIs (fuel prices, toll data, weather conditions), apply complex cost optimization algorithms, and produce highly competitive, data-driven price offers.
- **Historical Analysis & Predictive Insights:** Over time, the platform will leverage stored historical data to improve route planning, predict costs, refine margins, and offer strategic insights.

**From PoC to Target App:**  
- **Proof of Concept (PoC):**  
  - Basic input of route (from/to), transport type, cargo details, pickup/delivery date/time.  
  - Simple route calculation using static and mocked data (e.g., Google Maps API base route plus fixed assumptions for empty driving, rest times, and border checks).  
  - Manual cost calculation with a predefined set of cost items.  
  - Feasibility check and compliance checks are mocked (always feasible, requirements met).  
  - Fun fact about AI and transport displayed during offer generation.
  
- **Target App:**  
  - Advanced AI-driven feasibility checks and compliance validation.  
  - Dynamic cost and route optimization based on real-time data.  
  - Multiple user roles, business entities, complex workflow steps, and integrated APIs for fuel, tolls, weather, and telematics.

---

## 3. PRD for the PoC Version

### 3.1 User Flow (Transport Manager)

**Scenario:** The transport manager receives a customer request with specific pickup and delivery time requirements. The manager inputs all details and quickly needs to verify feasibility, calculate cost, and produce an offer.

**High-Level Steps:**  
1. **Input Cargo, Route & Time Details:**  
   - Enter origin (From) and destination (To) locations.  
   - Select transport type (e.g., flatbed, container truck).  
   - Enter cargo details (weight, value, special requirements).  
   - **New:** Enter pickup date/time and delivery date/time.
   
2. **Generate Basic Route & Timing:**  
   - The system retrieves a base route (distance, estimated time) from a mocked route planning service (in future: actual Google Maps API).  
   - **Empty Driving:** Before starting the main route, assume a fixed 200 km (~4h working time) for the truck to reposition from its current location to the pickup location. This adds to cost and timing.
   - Add simple mocked data for rest stops, compliance, and border crossing times. For the PoC, these are minimal increments.
   - Display the route and stops on a map, showing total time and how it fits within pickup/delivery constraints.
   - Mock feasibility service always returns "feasible."

3. **Calculate Costs:**  
   - On clicking "Generate Costs," the system calculates costs based on:  
     - Fuel, tolls, maintenance, driver, compliance, and cargo-specific costs.  
     - Include empty driving costs (fuel, driver’s time).  
   - For PoC, data is static or mocked.  
   - User can go to "Advanced Cost Settings" to manually adjust cost items.

4. **Set Margin & Generate Offer:**  
   - User inputs a desired profit margin.  
   - The system calculates final offer price = Total Costs + Margin.  
   - Clicking "Generate Offer" triggers offer finalization.

5. **Offer Display & Fun Fact:**  
   - While generating the offer, display a "loading" indicator and show a fun fact about AI and transport.  
   - After completion, the fun fact remains visible alongside the offer details.  
   - The final offer includes a summary of route time, costs, and proposed price.

6. **Review Past Routes & Offers:**  
   - "Offer Review Page" allows browsing previously planned routes and offers.  
   - Show route details, including timing and stops, cost breakdown, and final offers in read-only mode.

### 3.2 User Interface Pages, Components, and Actions

**Pages:**

1. **Homepage:**  
   - **Route Planning Form Component:**  
     - Inputs: From, To, Transport Type, Cargo Weight, Cargo Value, Cargo Special Requirements.  
     - **Pickup date/time and Delivery date/time fields.**  
     - "Generate Route" button.
   
   - **Route Details Component:**  
     - Shows route on a map with stops (including empty driving segment).  
     - Displays total estimated time and checks it against pickup/delivery constraints.  
     - "Generate Costs" button.

   - **Costs Calculation Component:**  
     - Displays an itemized cost breakdown: fuel, tolls, driver costs (including empty driving), compliance, cargo handling, etc.  
     - "Adjust Costs" → goes to Advanced Cost Settings Page.  
     - "Generate Offer" → margin input then generate final offer.

   - **Offer Generation Component:**  
     - Margin input field.  
     - "Generate Offer" button → triggers offer creation + shows fun fact during loading.  
     - After completion, display final offer details and keep fun fact on the page.

2. **Offer Review Page:**  
   - Lists previously generated routes/offers.  
   - Selecting a route displays three tabs:  
     - **Route Tab:** Map, route details, timing, empty driving segment info.  
     - **Costs Tab:** Itemized costs (read-only).  
     - **Offer Tab:** Final offer details (price, margin, timing info).
   - "Back to Homepage" button.

3. **Advanced Cost Settings Page:**  
   - Editable list of cost items (business costs, driver costs, fuel, tolls, compliance, cargo-specific, etc.).  
   - Includes empty driving costs as separate line items.  
   - Checkboxes to include or exclude certain costs.  
   - "Save & Return" applies changes and returns to the main cost calculation flow.

### 3.3 Core Functionality for Cost Calculation

**Cost Calculation Steps:**  
1. Calculate **Empty Driving Costs:**  
   - Fixed 200 km and 4h for PoC.  
   - Fuel cost = distance * consumption * price.  
   - Driver cost = hourly/daily rate * 4h + allowances if any.
   
2. Calculate **Main Route Costs:**  
   - Fuel, tolls, maintenance, driver cost (based on total route driving time + rest stops).  
   - Compliance costs (static from database).  
   - Cargo-specific costs (e.g., cleaning, hazmat, handling).
   
3. Sum all selected cost items = Total Cost.

4. Add user-defined margin to compute final offer price.

**Driver and Timing Considerations:**  
- For PoC, keep driver cost calculation simple: total working hours * hourly/daily rate.  
- Assume route timing from mocked data is always feasible.  
- In target app, driver rest and work-hour compliance will be dynamically calculated.

### 3.4 Core Services Definitions

**External (Mocked for PoC):**  
- **Route Planning Service (Google Maps mock):** Provides base route distance/time and minimal rest/border increments.
- **Fuel Price Service Mock:** Returns static fuel price per country.
- **Toll Price Service Mock:** Returns static toll costs.
- **CrewAI / Offer Generation AI Agent Mock:** Returns a static fun fact and final offer calculation.
- **Feasibility Check Service Mock:** Always returns "feasible."

**Internal Services:**  
- **Cost Calculation Service:** Integrates route data, cost items, and user inputs to compute total costs.
- **User Management Service (Mock):** Single user (John Doe) with full access.
- **Data Persistence Layer:** Stores route details, costs, and offers in a mock database.

### 3.5 Core Entities Definitions

**Entities:**

- **User:**  
  - For PoC: John Doe, Transport Manager role.
  
- **Business Entity:**  
  - Single entity representing the company.
  
- **Truck/Driver Pair:**  
  - For PoC: Statically defined in configuration.  
  - Includes basic data like fuel consumption, driver hourly rate.
  
- **Route:**  
  - Origin, destination, main route distance/time.  
  - Empty driving segment (distance/time).  
  - Stops (rest, border checks).  
  - Pickup/delivery time constraints.
  
- **Cargo:**  
  - Weight, value, special handling requirements.
  
- **Transport Type:**  
  - E.g., Flatbed, container truck.  
  - Influences compliance and cost items.
  
- **Cost Items:**  
  - Business costs, driver costs, fuel, tolls, maintenance, compliance, cargo-specific.
  
- **Offer:**  
  - Combines route (with timing) and total costs + margin.  
  - Stored in the database after generation.

### 3.6 Test Data for PoC Core Entities

**Example Route Data:**  
- Route: Warsaw, Poland → Berlin, Germany (~575 km)  
- Empty driving to Warsaw: 200 km, 4h.  
- Main route: ~8h driving + 1h rest/border = ~9h total.  
- Total working time: 4h (empty) + 9h (route) = 13h.  
- Pickup: 2023-10-01 08:00, Delivery: 2023-10-02 10:00 (plenty of buffer).
  
**Cost Data (Mock):**  
- Fuel: €1.50/L, consumption 30L/100km.  
- Toll: €100 fixed.  
- Driver cost: €200/day or simplified to hourly equivalent for PoC.  
- Cargo handling: €50 cleaning, etc.  
- Compliance: €30 flat.  
- Margin: User-defined (e.g., 15%).

### 3.7 Mocks of Services

- **Fuel Price API Mock:** Static €1.50/L.  
- **Toll API Mock:** €100 flat.  
- **CrewAI Mock:** Always returns a fun fact and final offer.  
- **Feasibility Mock:** Always true.

### 3.8 Documentation

- Include a README detailing setup, mock data loading, and how to run the PoC.  
- Inline documentation explaining calculation logic and data structures.

### 3.9 Current File Structure (PoC)

- **/src**:  
  - **/components**: UI components (Homepage, OfferReviewPage, AdvancedCostSettingsPage)  
  - **/services**: costCalculationService.js, routeServiceMock.js, feasibilityServiceMock.js, crewAIMock.js  
  - **/data**: JSON files for cost items, test routes, user mock, transport types  
  - **/utils**: helper functions for formatting distances/costs  
  - **/db**: mock database initialization scripts  
- **/public**: static files  
- **package.json** and related config files.

### 3.10 Technology Stack Requirements

- **Frontend:** React (or Vue) + basic UI library (Material UI or Bootstrap).  
- **Backend:** Node.js/Express.  
- **Database:** In-memory JSON or SQLite for PoC.  
- **APIs:** Mocked services for route, fuel, tolls, compliance, and CrewAI.  
- **CI/CD:** Basic CI script for linting and unit tests.

---

## 4. Evolution from PoC to Target App

**Short Term Enhancements:**  
- Integrate actual Google Maps API for real route data.  
- Add partial feasibility checks (if pickup/delivery windows are too tight, show warnings).

**Mid Term Enhancements:**  
- Dynamic compliance checks for driver rest times and work-hour restrictions.  
- Integrate external APIs for real-time fuel and toll costs, weather forecasts.  
- Introduce multiple user roles (CEO, Transport Manager) and multiple business entities.

**Long Term Enhancements:**  
- AI-driven route and timing optimization.  
- Real-time telematics integration for predictive maintenance and dynamic rerouting.  
- Comprehensive historical data analysis for predictive pricing and cost optimization.

# System Architecture and Implementation Plan (PoC)

## Overview

**Goal:**  
Implement a Proof of Concept (PoC) version of LoadApp.AI as described in the PRD. The PoC will focus on core functionalities:  
- Input route, cargo, timing details, generate a basic route and timing estimation (mocked).  
- Calculate costs (including empty driving and main route costs) from static/mocked data.  
- Generate offers with a margin and show a fun fact about AI.  
- Store route, cost, and offer data in a SQLite database.  
- Provide a simple user interface for input and review.

**Key Requirements:**  
- **Frontend:** Streamlit-based Python UI.  
- **Backend:** Flask-based REST API providing business logic, calculations, and data persistence.  
- **Domain Driven Design (DDD):** Organize code into logical domains reflecting the business model (e.g., Domain Entities: Route, Offer, Cargo; Domain Services: CostCalculationService, FeasibilityService). Keep simplicity but ensure extensibility.
- **Logging & Testing:** Structured logging for monitoring, basic test coverage.  
- **Database:** SQLite for PoC to store route, cost, and offer records.  
- **AI Agent Integration:** Mocked AI Agent calls to OpenAI API for generating the fun fact and simulating offer confirmation logic.  
- **Deployment:** Local development environment initially; after PoC, deploy on Replit from GitHub repo for preview.  
- **Development Process:** Implemented by prompting an AI Dev Agent that can read the PRD and System Architecture documents.

---

## High-Level Architecture

```
 ┌─────────────────┐         ┌──────────────────┐
 │  Streamlit UI    │  HTTP   │  Flask API        │
 │ (Frontend)       ├─────────┤  (Backend)       │
 └───┬──────────────┘         └───────┬──────────┘
     │                                │
     │                                │
     │                                │
     ▼                                ▼
 ┌─────────┐                    ┌───────────────┐
 │ AI Agent │                    │ Services/     │
 │ (Mocked) │                    │ Domain Layers │
 └──┬───────┘                    └─────┬────────┘
     │                                │
     ▼                                ▼
   OpenAI API                     SQLite DB
   (Real call)
```

**Key Components:**

1. **Frontend (Streamlit):**  
   - Presents forms for inputting route details, cargo details, pickup/delivery times, and margin.  
   - Displays route results on a map (static representation), costs breakdown, and final offers.  
   - Provides navigation to Offer Review and Advanced Cost Settings pages.
   
2. **Backend (Flask API):**  
   - Endpoints:
     - `/route`: Compute route details (mocking empty driving, rest stops, etc.).  
     - `/costs`: Calculate cost breakdown.  
     - `/offer`: Generate final offer (includes margin calculation, calls AI Agent for fun fact).  
     - `/data/review`: Retrieve past offers and routes from DB.  
     - `/costs/settings`: Retrieve/update advanced cost settings.
   - Interacts with domain services and the SQLite DB.

3. **Domain Services (Python Modules):**
   - **RouteService:** Mock route and timing calculations (include empty driving segment, rest stops).  
   - **CostCalculationService:** Compute base costs (fuel, tolls, driver, maintenance, compliance, cargo-specific), integrate empty driving costs.  
   - **OfferService:** Aggregate costs, add margin, and request fun fact from AI Agent.
   - **FeasibilityService (Mock):** Always returns feasible for PoC.
   - **AIIntegrationService:** Calls OpenAI API with a prompt to generate fun fact text. Mock simplified logic in PoC.

4. **Domain Model Entities:**
   - **User**: For PoC, static (John Doe).  
   - **BusinessEntity**: Single entity.  
   - **TruckDriverPair**: Static configuration data.  
   - **Route**: Fields for origin, destination, distance, empty driving distance/time, route time, pickup/delivery times.  
   - **Cargo**: Weight, value, special requirements.  
   - **Offer**: Includes route reference, total cost, margin, final price, and fun fact.  
   - **CostItems**: Represent various costs (fuel, tolls, driver, etc.), referenced by Route/Offer calculation.

5. **Database (SQLite):**
   - Tables:  
     - `users` (mocked single user for PoC)  
     - `routes` (store from/to, timing, costs references)  
     - `offers` (store final offer details and reference route ID)  
     - `cost_items` (initial static data)  
   - On app start: load mock data (costs, a sample route, etc.) into DB.

6. **Testing:**
   - Unit tests for services (CostCalculationService, RouteService, OfferService).  
   - Simple integration tests for Flask API endpoints.  
   - Run tests locally, ensure coverage for main logic paths.

7. **Logging:**
   - Use Python’s `logging` module with structured JSON logging where possible.  
   - Log each request to the Flask API and main actions in services.

---

## Domain Model (Conceptual)

**Entities & Value Objects:**

- **Route**  
  - `route_id`  
  - `origin`, `destination`  
  - `pickup_datetime`, `delivery_datetime`  
  - `distance_main_route`, `distance_empty`  
  - `time_main_route`, `time_empty`  
  - `total_time`, `stops` (list of Stop objects)  
  - Associations: One route -> Many cost items (evaluated at runtime)

- **Cargo**  
  - `cargo_id`  
  - `weight`, `value`, `special_requirements`

- **Offer**  
  - `offer_id`  
  - `route_id` (FK)  
  - `total_cost` (sum of cost items)  
  - `margin` (provided by user)  
  - `final_price` = `total_cost + margin`  
  - `fun_fact_text`

- **CostItem**  
  - `cost_item_id`  
  - `type` (fuel, toll, driver, compliance, cargo_handling, etc.)  
  - `amount` (modifiable by user in Advanced Settings)  
  - Linked at runtime to a specific route scenario.

---

## Implementation Plan (Phases)

**Phase 1: Project Setup & Basic Infrastructure**  
- Initialize GitHub repository.  
- Set up Python environment with Streamlit (frontend), Flask (backend), SQLite integration.  
- Create basic file structure:
  - `/frontend` for Streamlit scripts.
  - `/backend` for Flask app, domain services, and data models.
  - `/tests` for test modules.
  - `/data` for mock seed data (JSON or CSV).

**Phase 2: Domain Entities & DB Schema**  
- Define SQLite schema (using SQLAlchemy or direct SQLite queries).  
- Migrate initial data (cost items, one route scenario).  
- Create Python domain model classes (Route, Cargo, Offer) and connect them to DB models.

**Phase 3: Backend Endpoints & Services**  
- Implement `RouteService` mock logic for distance/time calculation including empty driving and stops.  
- Implement `CostCalculationService` to aggregate costs from DB and runtime logic.  
- Implement `OfferService` to add margin and call AIIntegrationService for fun fact.  
- Implement Flask endpoints (`/route`, `/costs`, `/offer`, `/data/review`, `/costs/settings`) and integrate services.
- Ensure structured logging in each endpoint and service.

**Phase 4: Frontend (Streamlit) Integration**  
- Build a simple homepage with input fields: from, to, transport type, cargo details, pickup/delivery times.  
- Buttons: Generate Route, Generate Costs, Generate Offer, View Offers.  
- Create Offer Review and Advanced Cost Settings pages.  
- Display map (static image or minimal representation) for route.  
- Show loading indicator and fun fact text after offer generation.

**Phase 5: Testing & Quality**  
- Write unit tests for domain services.  
- Integration tests for Flask endpoints.  
- Basic UI tests if feasible (optional).  
- Validate structured logging and ensure logs are readable.

**Phase 6: Deployment Setup**  
- Local deployment instructions (run Streamlit & Flask API together).  
- Prepare a simple Dockerfile if needed (optional for PoC).  
- After PoC completion, push to GitHub, configure Replit integration for live preview.

---

## Additional Requirements Consideration

1. **Deployment - Local & Replit:**  
   - Initially run backend (Flask) and frontend (Streamlit) locally.  
   - After PoC completion, push code to GitHub.  
   - On Replit, set up environment so that frontend and backend can run, providing a preview environment.

2. **Database is SQLite:**  
   - Use SQLite as a simple file-based DB.  
   - On application start, run schema migrations or create tables if not present.  
   - Load mock data into DB for cost items and initial test route.

3. **Development with AI Dev Agent:**  
   - The developer will prompt an AI Dev Agent with access to this PRD and System Architecture document.  
   - The Dev Agent will assist in implementing either backend or frontend functionality upon request.  
   - By structuring the architecture and domain model, we’ve ensured a clear and consistent reference point for the AI Dev Agent. The agent can refer back to this document to understand entities, endpoints, and data flows at every prompt.
   - This approach ensures that the AI Dev Agent can maintain consistency with the outlined domain model, services, and architecture as features are implemented incrementally.
