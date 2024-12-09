# LoadApp.AI Frontend Guide

This guide describes how to use the LoadApp.AI Streamlit interface, including all available features and interactions with the backend system.

## Getting Started

### Launching the Application

1. Open a terminal and navigate to the project directory:
   ```bash
   cd /path/to/loadapp.ai
   ```

2. Start the Flask backend server:
   ```bash
   python3 app.py
   ```

3. In a new terminal, start the Streamlit frontend:
   ```bash
   streamlit run frontend/main.py
   ```

4. Your default browser will automatically open to `http://localhost:8501`

## Navigation

The application consists of three main pages:
- **Home**: Main route planning and offer generation
- **Offer Review**: Historical data and past offers
- **Cost Settings**: Advanced cost configuration

Use the sidebar navigation menu to switch between pages.

## Home Page

The main page for route planning and offer generation.

### Route Planning Form

**Location Section:**
- **Origin**: Enter pickup location (address or coordinates)
  - Supports autocomplete for faster input
  - Validates location exists and is reachable
- **Destination**: Enter delivery location (address or coordinates)
  - Supports autocomplete for faster input
  - Validates location exists and is reachable
- **Pickup Time**: Select date and time for cargo pickup
  - Must be in the future
  - Consider business hours
- **Delivery Time**: Select date and time for delivery
  - Must be after pickup time
  - Considers realistic transit times

**Cargo Details:**
- **Type**: Select cargo type (e.g., general, temperature-controlled)
  - Affects vehicle selection and costs
  - May require special permits
- **Weight (kg)**: Enter cargo weight
  - Must be within vehicle capacity limits
  - Affects fuel consumption calculation
- **Value (EUR)**: Enter cargo value
  - Used for insurance calculations
  - Affects security requirements
- **Special Requirements**: Select any special handling requirements

**Transport Type:**
- **Vehicle Selection**: Choose appropriate vehicle type
  - Based on cargo requirements
  - Considers weight limits
  - Shows available options only
- **Empty Driving**: Calculate potential empty return trips
  - Affects total cost calculation
  - Optimizes for efficiency

**Submit Button**: Sends data to `/route` endpoint to generate route plan

### Cost Calculation

After submitting the route planning form, the system performs several calculations:

**Route Analysis:**
1. Calculates optimal route including:
   - Main route from origin to destination
   - Empty driving segments (return trips)
   - Total distance and estimated time

**Cost Components:**
2. Displays detailed cost breakdown:
   - Fuel costs (based on distance and vehicle type)
   - Empty driving costs (return trips)
   - Driver wages (including overtime if applicable)
   - Toll charges
   - Additional fees (permits, special handling)

**Summary:**
3. Shows total estimated cost with:
   - Base cost components
   - Additional fees
   - Potential savings
4. Allows cost adjustments via settings

**Actions:**
- Review cost details
- Adjust individual components
- Save for comparison
- Proceed to offer generation

**Calculate Costs Button**: Sends route ID to `/costs` endpoint

### Offer Generation

Once costs are calculated:
1. Enter desired profit margin
2. System generates complete offer including:
   - All transport details
   - Cost breakdown
   - Final price
   - Unique offer ID
   - Fun fact about the route
3. Option to:
   - Save offer for later
   - Send to customer
   - Modify and recalculate

**Generate Offer Button**: Sends data to `/offer` endpoint

## Offer Review Page

View and analyze historical offers.

### Features

**Filtering and Navigation:**
- **Date Range Filter**: Select start and end dates to narrow down offers
  - Default range is last 30 days
  - Calendar picker for easy date selection
  - Quick filters (Last week, Last month, etc.)

**Offer List:**
- Displays all offers within selected period
- Sortable by date, price, status
- Quick search by offer ID or route
- Pagination for large result sets

**Offer Details:**
When clicking an offer, view:
- Route information
  - Origin and destination
  - Pickup and delivery times
  - Vehicle type used
- Cost breakdown
  - Base costs
  - Additional fees
  - Applied margin
- Timeline
  - Key milestones
  - Status updates
  - Activity log
- Fun fact about the route
- Current status

**Data Export:**
- Export filtered results to CSV
- Include/exclude specific columns
- Choose date format

**Actions:**
- Clone offer for new booking
- Update offer status
- Add notes/comments
- Share offer details

Data is fetched from `/data/review` endpoint with query parameters for filtering and pagination.

## Cost Settings Page

Configure and adjust cost calculation parameters.

### Available Settings:

**Cost Items:**
- **Fuel**: Cost per kilometer
- **Tolls**: Average toll charges
- **Driver Wages**: Hourly rate
- **Maintenance**: Per kilometer rate
- **Special Handling**: Additional charges

For each cost item:
- Enable/disable toggle
- Adjust base value
- Set multiplier
- Change currency (EUR only in PoC)

**Save Settings Button**: Sends updates to `/costs/settings` endpoint

## Component Standards

### Standardized Components

The application uses standardized frontend components for consistency and maintainability:

1. **Route Input Form** (`frontend/components/route_input_form.py`)
   - Standardized input validation
   - Consistent error handling
   - Integrated location autocomplete
   - Real-time validation feedback

2. **Route Display** (`frontend/components/route_display.py`)
   - Unified route visualization
   - Interactive map component
   - Consistent timeline display
   - Standardized status indicators

3. **Cost Settings** (`frontend/components/advanced_cost_settings.py`)
   - Standardized input controls
   - Unified validation rules
   - Consistent layout and styling
   - Real-time calculation updates

### Component Testing

All frontend components are thoroughly tested using the pytest framework:

1. **Test Coverage**
   - Component rendering
   - User interactions
   - State management
   - API integrations
   - Error scenarios

2. **Running Component Tests**
   ```bash
   # Run all frontend tests
   pytest tests/test_streamlit_ui.py
   
   # Run with coverage report
   pytest tests/test_streamlit_ui.py --cov=frontend
   ```

3. **Test Requirements**
   - All dependencies are managed in the root `requirements.txt`
   - No separate test requirements file needed
   - Includes all necessary testing utilities

## Tips for Users

1. **Route Planning**:
   - Always verify pickup/delivery times are realistic
   - Check cargo weight against vehicle capacity
   - Review timeline for any scheduling conflicts

2. **Cost Calculation**:
   - Review all cost components before proceeding
   - Use cost settings to adjust for special circumstances
   - Consider enabling/disabling cost items based on route

3. **Offer Generation**:
   - Adjust margin based on market conditions
   - Review final price before sending to customer
   - Save important offers for future reference

4. **Data Review**:
   - Regularly review historical data
   - Use filters to find specific offers
   - Export data for external analysis

## Loading States

The application shows loading indicators during:
- Route calculation
- Cost computation
- Offer generation
- Settings updates

During these operations, a fun fact about transportation is displayed to keep users engaged.

## Error Handling

The UI handles common errors:
- Invalid input validation with clear messages
- Network connectivity issues
- Backend service errors
- Missing or invalid data

Error messages are displayed prominently with suggested actions.

## Browser Compatibility

The Streamlit interface works best with:
- Chrome (recommended)
- Firefox
- Safari
- Edge

Ensure your browser is up to date for optimal performance.

## Support

For technical issues:
1. Check the console for error messages
2. Verify both backend and frontend are running
3. Ensure all required dependencies are installed
4. Contact technical support if issues persist
