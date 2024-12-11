# Frontend Guide

## Overview

LoadApp.AI uses Streamlit for its frontend implementation, providing a modern, responsive interface for transport planning and offer generation. For detailed frontend architecture and design patterns, see [Architecture Documentation](../docs/ARCHITECTURE.md#frontend-layer-streamlit).

### Directory Structure
```
frontend/
├── 🏠_Home.py                    # Main application page
├── pages/
│   ├── 1_📊_Offer_Review.py     # Offer management
│   └── 2_⚙️_Cost_Settings.py    # Cost configuration
├── components/
│   ├── route_input_form.py      # Route planning form
│   ├── route_display.py         # Map visualization
│   └── advanced_cost_settings.py # Cost configuration UI
└── .streamlit/                  # Streamlit configuration
```

The frontend follows a modular structure with:
- Main page for route planning and offer generation
- Dedicated pages for offer review and cost settings
- Reusable components for common functionality
- Configuration for Streamlit customization

## Pages

### 1. Home Page (🏠_Home.py)
Main entry point for the application with:
```python
st.set_page_config(
    page_title="LoadApp.AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Core state initialization
if 'current_route' not in st.session_state:
    st.session_state.current_route = None
if 'current_costs' not in st.session_state:
    st.session_state.current_costs = None
if 'current_offer' not in st.session_state:
    st.session_state.current_offer = None
```

Features:
- Route planning with interactive form
- Real-time route visualization
- Dynamic cost calculation
- AI-enhanced offer generation
- Interactive map display

### 2. Offer Review (1_📊_Offer_Review.py)
Comprehensive offer management interface with:
- Advanced filtering system
- Analytics dashboard
- Interactive visualizations
- Detailed offer information:
  - Route details with maps
  - Cost breakdowns
  - Market analysis
  - Timeline tracking

### 3. Cost Settings (2_⚙️_Cost_Settings.py)
Advanced cost configuration interface featuring:
- Visual cost component analysis
- Component-based settings:
  - Variable costs (distance/time-based)
  - Fixed costs (per trip)
  - Special costs (conditional)
- Real-time rate calculations
- Settings persistence

For detailed state management and data flow, see [Architecture Documentation](../docs/ARCHITECTURE.md#frontend-layer-streamlit).

## Components

### Route Input Form (route_input_form.py)
```python
def render_route_input_form() -> Optional[Dict[str, Any]]:
    """Renders the route input form with validation."""
    with st.form("route_form"):
        # Location inputs (origin/destination)
        # Schedule inputs (pickup/delivery)
        # Cargo details
        # Submit button
```

Features:
- Location input with address and coordinates
- Schedule management with date/time pickers
- Cargo configuration:
  - Type and transport requirements
  - Weight, volume, and value
  - Special requirements selection

### Route Display (route_display.py)
```python
def render_route_display(route_data: Dict[str, Any]) -> None:
    """Displays route information and timeline."""
    # Route metrics
    # Timeline visualization
    # Detailed information
```

Features:
- Route metrics display
- Interactive timeline visualization
- Detailed route information
- Map integration (planned)

### Advanced Cost Settings (advanced_cost_settings.py)
```python
@dataclass
class CostSetting:
    """Cost setting configuration."""
    id: str
    type: str
    category: str
    is_enabled: bool
    base_value: float
    multiplier: float
    currency: str
    description: Optional[str] = None
```

Features:
- Cost component management
- Real-time cost preview
- Settings validation
- Cost analysis visualization

For detailed component architecture and state management, see [Architecture Documentation](../docs/ARCHITECTURE.md#frontend-layer-streamlit).

## State Management

### Session State
Core application state variables:
```python
# Route planning state
st.session_state.current_route    # Active route data
st.session_state.current_costs    # Cost calculations
st.session_state.current_offer    # Generated offer
st.session_state.step            # Current workflow step
st.session_state.margin          # Offer margin

# Settings state
st.session_state.cost_settings    # Cost configuration
st.session_state.settings_changed # Settings modification flag
st.session_state.preview_costs    # Cost preview data

# UI state
st.session_state.form_submitted   # Form submission status
st.session_state.page            # Current page number
```

### State Flow
1. Route Planning Flow:
   ```python
   # New route calculation
   st.session_state.current_route = route_response.json()
   st.session_state.current_costs = None  # Reset costs
   st.session_state.step = 'route_summary'
   
   # Cost calculation
   st.session_state.current_costs = cost_response.json()
   st.session_state.step = 'cost_summary'
   
   # Offer generation
   st.session_state.current_offer = offer_response.json()
   st.session_state.step = 'offer_summary'
   ```

2. Settings Management Flow:
   ```python
   # Load settings
   st.session_state.cost_settings = fetch_settings()
   
   # Update settings
   st.session_state.settings_changed = True
   st.session_state.preview_costs = preview_data
   ```

For detailed state management patterns and data flow architecture, see [Architecture Documentation](../docs/ARCHITECTURE.md#frontend-layer-streamlit).

## API Integration

### Configuration
```python
API_URL = "http://127.0.0.1:5000/api/v1"
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}
```

### Core Endpoints

1. Route Planning:
```python
# Calculate route
response = requests.post(
    f"{API_URL}/routes",
    json=route_data,
    headers=HEADERS
)

# Calculate costs
response = requests.post(
    f"{API_URL}/costs/{route_id}",
    json={"route_id": route_id},
    headers=HEADERS
)

# Generate offer
response = requests.post(
    f"{API_URL}/offers",
    json={
        "route_id": route_id,
        "margin": margin
    },
    headers=HEADERS
)
```

2. Settings Management:
```python
# Get settings
response = requests.get(
    f"{API_URL}/costs/settings",
    headers=HEADERS
)

# Update settings
response = requests.post(
    f"{API_URL}/costs/settings",
    json={"cost_items": settings},
    headers=HEADERS
)
```

### Error Handling
```python
try:
    response = requests.post(f"{API_URL}/route", json=route_data)
    if response.status_code == 200:
        data = response.json()
        # Handle success
    else:
        st.error(f"Error: {response.json().get('error', 'Unknown error')}")
except Exception as e:
    st.error(f"Connection error: {str(e)}")
```

For detailed API specifications and backend integration patterns, see [Architecture Documentation](../docs/ARCHITECTURE.md#api-layer-flask-restful).

## UI/UX Guidelines

### Theme Configuration
```toml
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#262730"
textColor = "#FAFAFA"
font = "sans serif"

[client]
toolbarMode = "minimal"
showSidebarNavigation = true
```

### Layout Patterns

1. Column-Based Layout:
```python
# Metrics display
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Base Cost", f"€{base_cost:.2f}")
with col2:
    st.metric("Variable Cost", f"€{variable_cost:.2f}")

# Form inputs
col1, col2 = st.columns(2)
with col1:
    st.text_input("Origin")
with col2:
    st.text_input("Destination")
```

2. Expandable Sections:
```python
with st.expander("Detailed Cost Breakdown"):
    # Detailed content
    st.subheader("Base Costs")
    # Cost components

with st.expander("Advanced Settings"):
    # Advanced options
    st.number_input("Multiplier")
```

### User Feedback

1. Loading States:
```python
with st.spinner("🔄 Calculating route..."):
    response = requests.post(f"{API_URL}/route", json=route_data)
```

2. Status Messages:
```python
# Success messages
st.success("Settings saved successfully!")

# Warnings
st.warning("Please fill in all required fields")

# Errors
st.error(f"Error: {response.json().get('error', 'Unknown error')}")

# Information
st.info("🎯 Fun Fact: Modern AI-powered logistics...")
```

### Form Organization
1. Group related inputs
2. Use clear labels and help text
3. Provide immediate validation feedback
4. Include progress indicators

For detailed UI component patterns and styling guidelines, see [Architecture Documentation](../docs/ARCHITECTURE.md#frontend-layer-streamlit).

## Styling and Configuration

### Streamlit Configuration
```toml
# .streamlit/config.toml

[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#262730"
textColor = "#FAFAFA"
font = "sans serif"

[browser]
gatherUsageStats = false

[server]
enableStaticServing = true

[client]
toolbarMode = "minimal"
showSidebarNavigation = true
```

### Page Configuration
```python
st.set_page_config(
    page_title="LoadApp.AI",
    layout="wide",
    initial_sidebar_state="expanded"
)
```

### Component Styling
1. Use consistent spacing and alignment
2. Follow Streamlit's native component styling
3. Maintain visual hierarchy in layouts
4. Apply consistent color scheme from theme

For detailed styling patterns and theme customization, see [Architecture Documentation](../docs/ARCHITECTURE.md#frontend-layer-streamlit).

## Development Workflow

### Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Development dependencies
- streamlit>=1.28.0      # Frontend framework
- plotly>=5.16.0        # Data visualization
- folium>=0.14.0        # Map visualization
- black>=23.7.0         # Code formatting
- isort>=5.12.0        # Import sorting
- mypy>=1.5.1          # Type checking
```

### Starting Development Server
```bash
# Start backend first
./start_backend.sh

# Start frontend in new terminal
./start_frontend.sh
```

The frontend startup script:
1. Checks backend connectivity
2. Loads environment configuration
3. Starts Streamlit development server

### Development Features
1. Hot Reloading:
   - Automatic page refresh on file changes
   - State preservation during development
   - Real-time error feedback

2. Debug Mode:
   - Enable through environment variables
   - Detailed error messages
   - State inspection tools

For detailed development practices and workflow patterns, see [Architecture Documentation](../docs/ARCHITECTURE.md#frontend-layer-streamlit).

## Testing

The frontend testing suite is implemented using pytest and includes comprehensive tests for components, pages, and API integrations. The tests are located in the `tests/` directory.

### Test Structure
- `test_frontend_components.py`: Tests for individual UI components
- `test_streamlit_ui.py`: Integration tests for Streamlit UI and API interactions
- `conftest.py`: Common test fixtures and configurations

### Key Testing Areas
1. **Component Testing**
   - Form validation and submission
   - Component rendering and state management
   - Error handling and edge cases
   - Type safety checks

2. **Integration Testing**
   - API endpoint integration
   - State management across components
   - Data flow between components
   - Error handling for API responses

3. **UI/UX Testing**
   - Route input form functionality
   - Route display and map rendering
   - Cost settings interface
   - Offer review page functionality

### Running Tests
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_frontend_components.py

# Run tests with coverage report
pytest --cov=frontend tests/
```

### Test Fixtures
Common test fixtures are available in `conftest.py`:
- `mock_streamlit`: Mocks Streamlit session state and functions
- `mock_api`: Mocks API responses for testing
- `mock_requests`: Mocks HTTP requests for API calls

### Best Practices
1. Use mocking for external dependencies (API calls, Streamlit functions)
2. Test both success and error scenarios
3. Maintain type safety in test implementations
4. Use descriptive test names and documentation
5. Keep test data separate from test logic

## Best Practices

### Code Organization
1. Separate components by functionality
2. Use consistent naming conventions
3. Keep components focused and reusable
4. Document component interfaces

### Performance
1. Lazy loading for heavy components
2. Efficient state management
3. Optimized API calls
4. Proper cache usage

### Error Handling
1. Validate inputs before submission
2. Provide clear error messages
3. Handle network errors gracefully
4. Maintain user context during errors

### Component Design
1. Single responsibility principle
2. Clear prop interfaces
3. Consistent state management
4. Proper error propagation

## Deployment

### Environment Configuration
```python
# Load environment-specific settings
API_URL = os.getenv("API_URL", "http://127.0.0.1:5000")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
```

### Production Considerations
1. Environment-specific configurations
2. Error tracking setup
3. Performance monitoring
4. Security headers

## Troubleshooting

### Common Issues
1. API Connection Errors
   - Check API_URL configuration
   - Verify network connectivity
   - Check backend server status

2. State Management Issues
   - Clear browser cache
   - Reset session state
   - Check state initialization

3. Component Rendering Problems
   - Verify data structure
   - Check component dependencies
   - Validate prop types

### Debugging Tips
1. Enable debug mode:
```python
if DEBUG:
    st.write("Debug info:", st.session_state)
```

2. Use logging:
```python
import logging
logging.info("Route data:", route_data)
```

3. Component isolation:
```python
# Test component in isolation
if st.checkbox("Test component"):
    with st.container():
        render_test_component()
```