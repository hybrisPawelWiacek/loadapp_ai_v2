Below are revised prompts incorporating a two-step pattern for each major feature or module: one prompt for the implementation and a subsequent prompt for testing that particular feature or module. The instructions still reference **`o1_mix_final_scope11.md`** in the `project_knowledge` folder as the primary source of truth. Each feature is introduced in a "feature prompt" followed by a "testing prompt." Prompts instruct the AI Dev Agent to create **or update** existing files as needed.

---

### Prompt 1a: Project Base Structure and Configuration (Feature)
**Goal:** Set up or update the project structure and basic configuration.

**Instruction to AI Dev Agent:**  
"First, refer to `o1_mix_final_scope11.md` in `project_knowledge`. If needed, consult other documents.  
- Create or update the following directories:  
  - `frontend/` (Streamlit UI)  
  - `backend/` (Flask services, domain logic)  
  - `backend/domain/entities` and `backend/domain/services`  
  - `backend/infrastructure/`  
  - `tests/`
- Create or update `config.py` for environment variables and `requirements.txt` for dependencies (Flask, Streamlit, SQLite, OpenAI client, etc.).
- Ensure the existing 'hello world' Flask endpoint and Streamlit app still function post-structure changes."

### Prompt 1b: Testing the Project Base Setup
**Goal:** Verify that the base structure and configuration work as intended.

**Instruction to AI Dev Agent:**  
"Check `o1_mix_final_scope11.md` for any testing guidelines. Create or update simple test scripts in `tests/` that:
- Verify that required directories and files are present.
- Confirm `requirements.txt` references correct dependencies.
- Optionally, write a test that runs the Flask 'hello world' endpoint and checks the response code.
  
Run these basic tests to ensure the initial setup aligns with the primary doc’s requirements."

---

### Prompt 2a: Database Setup and Schema Initialization (Feature)
**Goal:** Implement or update SQLite integration and create/update schema.

**Instruction to AI Dev Agent:**  
"Refer to `o1_mix_final_scope11.md` for database schema details:
- In `backend/infrastructure/`, create or update a database module (e.g., `db.py` or `repositories.py`) to:
  - Connect to SQLite.
  - Create or update `routes`, `offers`, `cost_settings` tables.
- After changes, ensure you can insert and retrieve a test record in each table."

### Prompt 2b: Testing the Database Setup
**Goal:** Ensure the database initialization and operations are correct.

**Instruction to AI Dev Agent:**  
"Create or update tests in `tests/` (e.g., `test_database.py`) to:
- Verify that tables (`routes`, `offers`, `cost_settings`) exist after initialization.
- Insert a sample record into each table and retrieve it to confirm correct read/write operations.
  
Run the tests and confirm they pass, reflecting `o1_mix_final_scope11.md` specifications."

---

### Prompt 3a: Defining Domain Entities (Feature)
**Goal:** Implement or update domain entity dataclasses.

**Instruction to AI Dev Agent:**  
"Check `o1_mix_final_scope11.md` for entity definitions. In `backend/domain/entities/`:
- Create or update Python files for `Route`, `Offer`, `Cargo`, `CostItem`, `TimelineEvent`, `Location`, `TransportType`, `EmptyDriving`, `MainRoute` as dataclasses.
- Ensure all fields match the doc’s requirements and no logic is included yet."

### Prompt 3b: Testing Domain Entities
**Goal:** Validate that domain entities align with the doc.

**Instruction to AI Dev Agent:**  
"In `tests/`, create or update a `test_entities.py`:
- Instantiate each entity with mock data.
- Check that required fields exist and can hold expected data types.
- No complex logic yet—just ensure no exceptions are raised and the entities align with `o1_mix_final_scope11.md`."

---

### Prompt 4a: Implementing the RoutePlanningService (Feature)
**Goal:** Create or update `RoutePlanningService` to produce a mock feasible route.

**Instruction to AI Dev Agent:**  
"Refer to `o1_mix_final_scope11.md`:
- In `backend/domain/services/`, create or update `route_planning_service.py`.
- Implement `calculate_route()` to:
  - Add empty driving scenario.
  - Provide a static main route.
  - Set `is_feasible = True`.
  - Return a `Route` object per the doc’s specs."

### Prompt 4b: Testing the RoutePlanningService
**Goal:** Ensure `RoutePlanningService` behaves as expected.

**Instruction to AI Dev Agent:**  
"In `tests/`, create or update `test_route_planning_service.py`:
- Call `calculate_route()` with mock input.
- Assert that returned `Route` has correct fields (empty driving, main route, `is_feasible=true`).
- Confirm it matches `o1_mix_final_scope11.md` guidelines."

---

### Prompt 5a: Implementing the CostCalculationService (Feature)
**Goal:** Create or update `CostCalculationService` to return a mock cost breakdown.

**Instruction to AI Dev Agent:**  
"Check `o1_mix_final_scope11.md`:
- In `backend/domain/services/`, create or update `cost_calculation_service.py`.
- Implement `calculate_total_cost()` with static or mocked values for fuel, tolls, driver costs, etc.
- Return a dictionary of cost items aligned with the doc."

### Prompt 5b: Testing the CostCalculationService
**Goal:** Validate cost calculations.

**Instruction to AI Dev Agent:**  
"In `tests/test_cost_calculation_service.py`:
- Call `calculate_total_cost()` with a mock `Route` and `Cargo`.
- Assert that returned dict contains expected cost items and amounts.
- Verify no exceptions and that output adheres to `o1_mix_final_scope11.md`."

---

### Prompt 6a: Implementing the OfferService and AI Integration (Feature)
**Goal:** Integrate margin and AI fun fact in offer generation.

**Instruction to AI Dev Agent:**  
"From `o1_mix_final_scope11.md`:
- In `backend/domain/services/offer_service.py`, implement `generate_offer()`:
  - Combine costs + margin = final price.
  - Call OpenAI API (in `backend/infrastructure/external/ai_integration.py`) for a fun fact.
  - Save the `Offer` to DB and return it."

### Prompt 6b: Testing the OfferService
**Goal:** Ensure offers are created correctly and include a fun fact.

**Instruction to AI Dev Agent:**  
"In `tests/test_offer_service.py`:
- Mock the OpenAI API call.
- Invoke `generate_offer()` with a mock route and costs.
- Assert that the returned `Offer` has a final price, a fun fact, and is stored in DB per `o1_mix_final_scope11.md`."

---

### Prompt 7a: Flask Endpoints for Route and Costs (Feature)
**Goal:** Add or update `/route` and `/costs` endpoints.

**Instruction to AI Dev Agent:**  
"Refer to `o1_mix_final_scope11.md`:
- In `backend/flask_app.py`, implement:
  - `/route` (POST): Accept JSON input, call `RoutePlanningService`, return JSON `Route`.
  - `/costs` (POST): Accept route data/ID, call `CostCalculationService`, return JSON costs."

### Prompt 7b: Testing the `/route` and `/costs` Endpoints
**Goal:** Ensure endpoints return expected JSON outputs.

**Instruction to AI Dev Agent:**  
"In `tests/test_flask_endpoints.py`:
- Use a Flask test client to POST to `/route` and `/costs`.
- Assert that response codes are 200 and returned JSON matches the doc specs.
- Check that routes and costs align with `o1_mix_final_scope11.md`."

---

### Prompt 8a: Flask Endpoints for Offer and Data Review (Feature)
**Goal:** Implement `/offer` and `/data/review` endpoints.

**Instruction to AI Dev Agent:**  
"From `o1_mix_final_scope11.md`:
- In `backend/flask_app.py`:
  - `/offer` (POST): Given route ID and margin, generate an offer using `OfferService`.
  - `/data/review` (GET): Return a list of past offers with their details."

### Prompt 8b: Testing the `/offer` and `/data/review` Endpoints
**Goal:** Verify correct offer creation and review data.

**Instruction to AI Dev Agent:**  
"In `tests/test_flask_endpoints.py` (update existing or create new methods):
- Test `/offer` by sending route ID + margin, check if the offer with fun fact is returned.
- Test `/data/review` by checking if previously created offers appear correctly.
- Confirm responses match `o1_mix_final_scope11.md` expectations."

---

### Prompt 9a: Flask Endpoints for Cost Settings Management (Feature)
**Goal:** Implement `/costs/settings` GET/POST endpoints.

**Instruction to AI Dev Agent:**  
"Refer to `o1_mix_final_scope11.md`:
- In `backend/flask_app.py`:
  - `/costs/settings` (GET): Return current cost items and their states.
  - `/costs/settings` (POST): Update cost items (enable/disable, value changes) and persist in DB."

### Prompt 9b: Testing the `/costs/settings` Endpoints
**Goal:** Ensure cost settings are retrievable and updatable.

**Instruction to AI Dev Agent:**  
"In `tests/test_flask_endpoints.py` (add more tests):
- GET `/costs/settings`, verify returned cost items match DB values.
- POST new settings, then GET again to ensure changes persisted.
- Confirm behavior matches `o1_mix_final_scope11.md`."

---

### Prompt 10a: Frontend Homepage Implementation (Feature)
**Goal:** Implement or update the Streamlit homepage UI.

**Instruction to AI Dev Agent:**  
"From `o1_mix_final_scope11.md`:
- In `frontend/streamlit_app.py` or a homepage file:
  - Add form fields for origin/destination, transport_type, cargo details, pickup/delivery times.
  - Buttons to generate route, costs, and offer.
  - Display route results, cost breakdown, and the offer’s fun fact."

### Prompt 10b: Testing the Frontend Homepage
**Goal:** Ensure the homepage UI integrates well with backend endpoints.

**Instruction to AI Dev Agent:**  
"UI tests can be more manual, but also consider:
- In `tests/`, create or update a test script that:
  - Mocks endpoint responses and checks if UI functions without errors using Streamlit’s testing utilities (if available).
- At minimum, verify that the homepage can call endpoints without exceptions and display the returned data aligned with `o1_mix_final_scope11.md`."

---

### Prompt 11a: Frontend Offer Review Page (Feature)
**Goal:** Implement or update the Offer Review page UI.

**Instruction to AI Dev Agent:**  
"According to `o1_mix_final_scope11.md`:
- In `frontend/`, create or update `offer_review_page.py`:
  - Fetch offers from `/data/review`.
  - Display selectable offers and show route, costs, offer details in tabs."

### Prompt 11b: Testing the Frontend Offer Review Page
**Goal:** Ensure the review page displays correct information.

**Instruction to AI Dev Agent:**  
"In `tests/`, add or update a test:
- Mock `/data/review` responses and confirm the page logic renders offers correctly.
- If possible, use Streamlit test patterns to ensure no exceptions are raised and that the data displayed matches `o1_mix_final_scope11.md`."

---

### Prompt 12a: Frontend Advanced Cost Settings Page (Feature)
**Goal:** Implement or update the Advanced Cost Settings UI.

**Instruction to AI Dev Agent:**  
"From `o1_mix_final_scope11.md`:
- In `frontend/advanced_cost_settings.py` or similar:
  - GET `/costs/settings` and display items with toggles/inputs.
  - POST updates back to `/costs/settings`.
  - Ensure UI flow matches the doc’s instructions."

### Prompt 12b: Testing the Frontend Advanced Cost Settings Page
**Goal:** Confirm that updating cost settings via UI works as expected.

**Instruction to AI Dev Agent:**  
"In `tests/`, write or update tests:
- Mock GET `/costs/settings` to return some cost items.
- Simulate toggling/enabling items and POST changes.
- Verify new GET shows updated states.
- Check behavior matches `o1_mix_final_scope11.md`."

---

### Prompt 13: Logging and Final Integration Tests
**Goal:** Implement or update structured logging and run final integration tests.

**Instruction to AI Dev Agent:**  
"Refer to `o1_mix_final_scope11.md` for logging and final checks:
- Add or update structured JSON logging in `backend/flask_app.py` and services.
- Perform final integration tests:
  - Check that the full workflow (from homepage input to offer generation and review) works as intended.
  - Run existing tests to confirm all pass.
- Fix any inconsistencies found during this final check."


---

These revised prompts follow a pattern: each major feature or module first gets a prompt for implementation (the "a" prompt) and then a prompt for testing that feature (the "b" prompt). This structure encourages incremental development and validation at each step, referencing `o1_mix_final_scope11.md` as the primary source of truth.


Below is a new set of prompts focused on creating comprehensive documentation for the project. These prompts assume that all features and tests have been implemented. They direct the AI Dev Agent to refer first to **`o1_mix_final_scope11.md`** in the `project_knowledge` folder for guidance on content and formatting standards. Additional supporting documents can be consulted as needed.

The prompts cover various documentation aspects, including architectural overviews, entity and component descriptions, endpoint references, developer setup instructions, user guides, and a comprehensive `README.md`.

---

### Prompt D1: High-Level Architectural Documentation (Feature)
**Goal:** Create or update a high-level architectural overview document.

**Instruction to AI Dev Agent:**  
"First, reference `o1_mix_final_scope11.md` in `project_knowledge` for architectural guidelines. Then, create or update a file named `ARCHITECTURE.md` at the project root that includes:  
- A clear diagram (in ASCII or link to an image) showing `frontend` (Streamlit), `backend` (Flask), `domain` (entities/services), `infrastructure` (database, external integrations) layers.  
- A description of each layer’s responsibility and how they interact.  
- Notes on how data flows from user input in Streamlit to the backend, through domain services, and eventually to the database.  
- References to key components (RoutePlanningService, CostCalculationService, OfferService) and how they fit into the architecture."

### Prompt D1b: Testing Architectural Documentation
**Goal:** Verify that the architectural documentation is clear and aligned with the project scope.

**Instruction to AI Dev Agent:**  
"In `tests/`, add or update a `test_documentation.py` script that:  
- Parses `ARCHITECTURE.md` and ensures key terms mentioned in `o1_mix_final_scope11.md` (e.g., service names, layers) appear in the doc.  
- While not a strict functional test, ensure that all core components (entities, services, endpoints) are mentioned.  
- Confirm that no major architectural element from `o1_mix_final_scope11.md` is omitted."

---

### Prompt D2: Domain Entities Documentation (Feature)
**Goal:** Create or update documentation describing each domain entity.

**Instruction to AI Dev Agent:**  
"Check `o1_mix_final_scope11.md` for entity details. Create or update `ENTITIES.md` at the project root:  
- For each entity (Route, Offer, Cargo, etc.), list:  
  - A short definition and purpose.  
  - Key fields and their data types.  
  - Any relationships (e.g., Route references Cargo, Offer references Route ID).
- Include notes on how these entities are used by services and endpoints."

### Prompt D2b: Testing Entity Documentation
**Goal:** Ensure entity documentation is accurate and complete.

**Instruction to AI Dev Agent:**  
"In `tests/test_documentation.py`, add checks that:  
- All entities mentioned in `o1_mix_final_scope11.md` appear in `ENTITIES.md`.  
- Each entity’s required fields as per the doc are mentioned.  
- If possible, just string match or keyword check to confirm completeness (not a strict functional test, but a consistency check)."

---

### Prompt D3: Service and Component Documentation (Feature)
**Goal:** Document all domain services and key backend components.

**Instruction to AI Dev Agent:**  
"Refer to `o1_mix_final_scope11.md` for service details. In a new file `SERVICES.md`:  
- Describe each service (RoutePlanningService, CostCalculationService, OfferService), their responsibilities, and methods.  
- Summarize AI integration (OfferService + AI call) and database integration (repositories).
- Include a brief mention of logging strategy and how services log operations."

### Prompt D3b: Testing Service Documentation
**Goal:** Validate that service documentation aligns with implementations and the main doc.

**Instruction to AI Dev Agent:**  
"In `tests/test_documentation.py`, add assertions to check:  
- All services listed in `o1_mix_final_scope11.md` appear in `SERVICES.md`.  
- Key methods (`calculate_route()`, `calculate_total_cost()`, `generate_offer()`) are documented.  
- Logging and AI integration are mentioned."

---

### Prompt D4: Endpoint Reference Documentation (Feature)
**Goal:** Create or update comprehensive API endpoint docs.

**Instruction to AI Dev Agent:**  
"From `o1_mix_final_scope11.md`, create or update `ENDPOINTS.md` at the project root:  
- List each endpoint (`/route`, `/costs`, `/offer`, `/data/review`, `/costs/settings`) with:  
  - HTTP method (GET/POST)  
  - Required and optional parameters (JSON fields)  
  - Example request and response payloads  
  - Any error conditions and expected status codes.
- This doc should help a new developer or client understand how to use the API."

### Prompt D4b: Testing Endpoint Documentation
**Goal:** Ensure endpoint documentation is complete and correct.

**Instruction to AI Dev Agent:**  
"In `tests/test_documentation.py`:  
- Verify that every endpoint mentioned in `o1_mix_final_scope11.md` exists in `ENDPOINTS.md`.  
- Check that example requests/responses are present.  
- Confirm that status codes and parameters align with the doc’s definitions."

---

### Prompt D5: Frontend Usage Guide (Feature)
**Goal:** Document how the Streamlit UI is structured and how a user interacts with it.

**Instruction to AI Dev Agent:**  
"Using `o1_mix_final_scope11.md`, create or update `FRONTEND_GUIDE.md` describing:  
- The homepage components (forms, buttons) and what data they send to backend endpoints.  
- Offer Review and Advanced Cost Settings pages and how they interact with the backend.  
- Basic instructions for end-users: how to launch Streamlit, navigate pages, interpret results, and update cost settings."

### Prompt D5b: Testing Frontend Documentation
**Goal:** Confirm frontend docs mention all UI features and align with code.

**Instruction to AI Dev Agent:**  
"In `tests/test_documentation.py`:  
- Check that `FRONTEND_GUIDE.md` mentions homepage, offer review, cost settings pages.  
- Verify that all main actions (generate route, generate costs, create offer, review offers, change cost settings) appear in the guide."

---

### Prompt D6: Developer Setup and Contribution Guide (Feature)
**Goal:** Provide setup instructions, environment configuration, and contribution guidelines.

**Instruction to AI Dev Agent:**  
"Refer to `o1_mix_final_scope11.md` for any developer-related notes. Create or update `DEVELOPER_GUIDE.md`:  
- Instructions on installing dependencies from `requirements.txt`.  
- How to run Flask backend and Streamlit frontend.  
- Steps to run tests (unit, integration, documentation checks).  
- Guidelines for contributing code: coding standards, logging rules, branching strategy if any mentioned in docs."

### Prompt D6b: Testing Developer Documentation
**Goal:** Ensure that developer instructions are usable.

**Instruction to AI Dev Agent:**  
"In `tests/test_documentation.py`:
- Check that `DEVELOPER_GUIDE.md` references correct commands to start backend and frontend.  
- Verify that testing instructions mention unit, integration, and documentation tests.  
- Confirm that coding standards and contribution hints align with `o1_mix_final_scope11.md`."

---

### Prompt D7: Comprehensive README.md (Feature)
**Goal:** Create or update a top-level `README.md` providing a project overview.

**Instruction to AI Dev Agent:**  
"From `o1_mix_final_scope11.md`, create or update `README.md` that includes:  
- A brief project description and goals.  
- High-level architecture summary (link to `ARCHITECTURE.md` for details).  
- Quickstart instructions (setting up environment, running the app).  
- Links to all other documentation files (`ENTITIES.md`, `SERVICES.md`, `ENDPOINTS.md`, `FRONTEND_GUIDE.md`, `DEVELOPER_GUIDE.md`).  
- Highlight key features (AI integration, cost calculation, route planning)."

### Prompt D7b: Testing the README
**Goal:** Validate that `README.md` provides a proper project overview and links correctly.

**Instruction to AI Dev Agent:**  
"In `tests/test_documentation.py`:
- Check that `README.md` includes a general description, setup steps, and links to all other docs.  
- Confirm it matches the main guidelines in `o1_mix_final_scope11.md` (project overview is correct, main features are mentioned).  
- Ensure that no critical documentation file is missing from the README’s reference list."

---

By following this set of documentation-focused prompts, the project will gain comprehensive, consistent, and user-friendly documentation covering architecture, entities, services, endpoints, frontend usage, developer instructions, and a welcoming `README.md`. Each documentation prompt is paired with a testing prompt to encourage consistency and alignment with `o1_mix_final_scope11.md` and the rest of the project’s structure.

Below are prompts specifically focused on documenting the testing infrastructure implemented in the project. These prompts assume that tests have been created throughout the development process. The instructions direct the AI Dev Agent to first reference **`o1_mix_final_scope11.md`** in the `project_knowledge` folder for any guidelines on testing and quality assurance. Additional documents may be consulted if more context is needed. The final documentation will be placed in a dedicated `docs` folder.

---

### Prompt T1a: Documenting the Testing Infrastructure (Feature)
**Goal:** Create or update a documentation file that describes the project's testing setup and methodology.

**Instruction to AI Dev Agent:**  
"First, review `o1_mix_final_scope11.md` in `project_knowledge` for testing guidelines. Then, in the `docs/` directory, create or update a file named `TESTING_INFRASTRUCTURE.md` that includes:  
- An overview of the testing framework(s) used (e.g., pytest).  
- The directory structure of tests (unit tests for entities and services, integration tests for Flask endpoints, documentation-related tests, UI tests if any).  
- Instructions on how to run tests locally (commands to execute tests, any environment variables needed).  
- A description of how tests are organized and named.  
- Guidelines on how to add new tests (e.g., where to place them, naming conventions, what scenarios to cover).  
- Any references to CI/CD integration or how tests fit into the development workflow, if mentioned in `o1_mix_final_scope11.md`."

### Prompt T1b: Testing the Testing Documentation
**Goal:** Ensure that the testing documentation accurately reflects the project's test infrastructure.

**Instruction to AI Dev Agent:**  
"In `tests/documentation/`, add file that checks that:  
- `TESTING_INFRASTRUCTURE.md` exists in `docs/`.  
- The file mentions each test category (unit, integration, documentation tests) as outlined in `o1_mix_final_scope11.md`.  
- Key instructions (e.g., how to run `pytest`, how to set environment variables) appear in the file.  
- Ensure the guidelines for adding new tests align with previously implemented tests and the overall project structure."

---

These prompts focus on creating a dedicated documentation file that thoroughly explains the project's testing strategy, tools, and best practices. The subsequent testing prompt ensures that this documentation accurately describes the implemented test infrastructure and meets the standards defined in `o1_mix_final_scope11.md`.


Below is a revised set of prompts that incorporate the best practices learned from previous interactions. Each prompt instructs the AI Dev Agent to reference **`o1_mix_final_scope11.md`** (the current scope) and **`mix_final_scope2.md`** (the new scope) in the `project_knowledge` folder. The prompts follow the established pattern: first a feature implementation prompt, then a testing prompt. They also remind the agent to create **or update** existing files and adhere to clean architecture principles and any new requirements introduced in `mix_final_scope2.md`. The prompts are detailed, outcome-focused, and encourage iterative development with testing after each major feature.

---

### Prompt Series 1: Performance Metrics Infrastructure

**Context:** We are introducing a PerformanceMetrics system that works across multiple components. The initial requirements come from `o1_mix_final_scope11.md`, while new enhancements and missing requirements are outlined in `mix_final_scope2.md`. The system should integrate with Flask endpoints, domain services, and database operations, and align with our clean architecture.

#### Prompt 1a: Feature Implementation  
**Goal:** Implement or update the PerformanceMetrics system.

**Instruction to AI Dev Agent:**  
"Refer first to `o1_mix_final_scope11.md` for initial performance metrics requirements, then consult `mix_final_scope2.md` for additional enhancements and missing requirements. In `backend/infrastructure/monitoring/performance_metrics.py`, create or update the PerformanceMetrics dataclass and associated logic. Integrate this system with:

- `backend/flask_app.py`: Measure API response times and log structured metrics.
- `backend/domain/services/`: Measure service operation times using decorators that time function calls.
- `backend/infrastructure/repositories/`: Measure database query durations and count.

**Key considerations:**
- Use `structlog` for consistent structured logging as per our established logging conventions.
- Ensure thread-safety and minimal overhead.
- Store metrics in memory and implement periodic persistence (if required by `mix_final_scope2.md`).
- Align with clean architecture principles described in `docs/ARCHITECTURE.md`.

After implementation, confirm that all new requirements from `mix_final_scope2.md` are addressed. If performance_metrics.py has TODO items, resolve them. Maintain backward compatibility and ensure that the system integrates seamlessly with existing components."

#### Prompt 1b: Testing the Performance Metrics  
**Goal:** Validate the PerformanceMetrics system.

**Instruction to AI Dev Agent:**  
"In `tests/test_performance_metrics.py`, create or update tests that verify the PerformanceMetrics functionality:

- Confirm accurate metric collection (timing correctness, counts).
- Test decorator functionality on services, endpoints, and repository operations.
- Validate thread-safety by simulating concurrent requests or operations.
- Check logging output to ensure metrics are logged as per our structured logging standards.
- Mock time operations if needed and test memory storage and any periodic persistence logic introduced in `mix_final_scope2.md`.

Ensure tests fully cover both initial and enhanced requirements from `o1_mix_final_scope11.md` and `mix_final_scope2.md`. Run tests and confirm all pass without regressions."

---

### Prompt Series 2: Metrics Logger System

**Context:** We are adding a MetricsLogger system that aggregates, persists, and queries performance metrics. Initial guidelines are in `o1_mix_final_scope11.md`, with additional specifications and enhancements in `mix_final_scope2.md`. The system should integrate with our PerformanceMetrics, use async operations if specified, and respect data retention or alert thresholds.

#### Prompt 2a: Feature Implementation  
**Goal:** Implement or update the MetricsLogger system.

**Instruction to AI Dev Agent:**  
"Refer first to `o1_mix_final_scope11.md`, then to `mix_final_scope2.md` for additional instructions. In `backend/infrastructure/monitoring/metrics_logger.py`, create or update the MetricsLogger class:

- Implement methods for periodic metrics aggregation, data buffering, and rotation of old metrics.
- Integrate with the PerformanceMetrics system for data sources.
- Implement persistence to the database or another storage layer (check `mix_final_scope2.md` for specifics).
- Add a query interface for retrieving aggregated metrics.
- Introduce alert thresholds as defined in `mix_final_scope2.md`.

Key considerations:
- Use async operations if recommended by `mix_final_scope2.md`.
- Maintain minimal performance overhead.
- Ensure logging and error handling align with existing standards.

After implementation, verify that all `mix_final_scope2.md` enhancements are met and that the system aligns with clean architecture principles."

#### Prompt 2b: Testing the Metrics Logger  
**Goal:** Validate the MetricsLogger functionality.

**Instruction to AI Dev Agent:**  
"In `tests/test_metrics_logger.py`, create or update tests that:

- Check logging accuracy and consistency.
- Verify correct metric aggregation and rotation logic.
- Confirm persistence operations (insert, read, rotate) match specifications.
- Test alert threshold behavior (simulate scenarios that trigger alerts).
- If async operations are used, test async logic thoroughly (mocking async calls as needed).

Ensure tests cover requirements from both scopes and confirm that all pass successfully."

---

### Prompt Series 3: Frontend Component Standardization

**Context:** We have a set of frontend components defined by `o1_mix_final_scope11.md`. The new `mix_final_scope2.md` scope introduces additional structure and standardization requirements. Our goal is to refactor and standardize these components while maintaining full functionality.

#### Prompt 3a: Feature Implementation  
**Goal:** Standardize and update frontend components.

**Instruction to AI Dev Agent:**  
"Check `o1_mix_final_scope11.md` for the current component setup and `mix_final_scope2.md` for the new standardization requirements. In `frontend/components/` and in `frontend/pages/` and in `frontend/streamlit_app.py`, update or reorganize:

- `RouteInputForm`
- `RouteDisplay`
- `OfferReviewPage`
- `AdvancedCostSettings`

**Key considerations:**
- Adopt the exact structure defined in `mix_final_scope2.md`.
- Update component interfaces to match the new standard.
- Preserve existing functionality and compatibility with the backend.
- Enhance type definitions, ensure consistent styling, and maintain code quality.
- Document changes as required by the scope documents.

After refactoring, confirm that the standardized components still work end-to-end."

#### Prompt 3b: Testing the Frontend Components  
**Goal:** Validate the standardized frontend components.

**Instruction to AI Dev Agent:**  
"In `tests/test_frontend_components.py` and `tests/test_streamlit_ui.py` or any other UI tests, create or update tests that:

- Verify that each component matches the new structure and interface defined in `mix_final_scope2.md`.
- Confirm that existing functionalities (inputs, outputs, events) remain unchanged.
- Check type safety (if applicable) and ensure all props and events align with updated specs.
- Test rendering and user interaction scenarios to ensure the UI remains responsive and correct.

Run the tests and confirm that all pass, ensuring no regressions and full compliance with the updated standards."

---

**Would you like to see additional prompts for other functionalities, documentation of these new features, or integration with other systems defined in `mix_final_scope2.md`?**