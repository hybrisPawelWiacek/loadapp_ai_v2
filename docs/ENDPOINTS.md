# LoadApp.AI API Documentation

This document provides comprehensive documentation for the LoadApp.AI API endpoints. Each endpoint is documented with its HTTP method, required and optional parameters, example requests and responses, and possible error conditions.

## Base URL

For local development:
```
http://localhost:5000
```

## Authentication

Currently, authentication is not implemented in the PoC version. All endpoints are publicly accessible.

## Endpoints

### 1. Route Planning

#### POST /route

Calculates a route between two locations with cargo specifications.

#### Request Format

```json
{
  "origin": {
    "latitude": 52.52,
    "longitude": 13.405,
    "address": "Berlin, Germany"
  },
  "destination": {
    "latitude": 48.8566,
    "longitude": 2.3522,
    "address": "Paris, France"
  },
  "pickup_time": "2024-12-08T09:00:00",
  "delivery_time": "2024-12-09T17:00:00",
  "cargo": {
    "type": "Standard Truck",
    "weight": 1000,
    "value": 5000,
    "special_requirements": []
  }
}
```

#### Data Processing

1. **Location Objects**
   - Created from latitude, longitude, and address
   - All fields are required
   - Coordinates must be valid float values

2. **Transport Type**
   - Automatically created based on cargo type
   - Uses default capacity settings
   - Example:
     ```python
     TransportType(
         name="Standard Truck",
         capacity=Capacity(),  # Default values
         restrictions=[]
     )
     ```

3. **Cargo Processing**
   - Weight and value converted to float
   - Special requirements as optional list
   - Automatically assigned UUID

#### Response Format

```json
{
  "id": "31cae6e6-994c-4bf6-a1fe-a98a68faba37",
  "origin": {
    "latitude": 52.52,
    "longitude": 13.405,
    "address": "Berlin, Germany"
  },
  "destination": {
    "latitude": 48.8566,
    "longitude": 2.3522,
    "address": "Paris, France"
  },
  "total_duration_hours": 10.0,
  "is_feasible": true,
  "transport_type": {
    "name": "Standard Truck",
    "capacity": {
      "max_weight": 24000.0,
      "max_volume": 80.0,
      "unit": "metric"
    },
    "restrictions": []
  },
  "timeline": [
    {
      "time": "2024-12-08T09:00:00",
      "event_type": "pickup",
      "location": {
        "latitude": 52.52,
        "longitude": 13.405,
        "address": "Berlin, Germany"
      }
    },
    {
      "time": "2024-12-09T17:00:00",
      "event_type": "delivery",
      "location": {
        "latitude": 48.8566,
        "longitude": 2.3522,
        "address": "Paris, France"
      }
    }
  ]
}
```

#### Error Handling

1. **Database Errors**
   - 500 response if database connection fails
   - Includes error message and type

2. **Validation Errors**
   - 400 response for invalid input data
   - Specific error messages for each validation failure

3. **Processing Errors**
   - 500 response for internal processing errors
   - Detailed error information in development mode

### 2. Cost Calculation Endpoint

#### Route: `/costs/<route_id>`
- **Method**: POST
- **Description**: Calculates costs for a specific route
- **URL Parameters**:
  - `route_id`: UUID of the route (required)
- **Request Body:**
```json
{
    "include_empty_driving": true
}
```
- **Response Format**:
```json
{
    "total_cost": 1000.00,
    "currency": "EUR",
    "breakdown": {
        "base_cost": 500.00,
        "distance_cost": 250.00,      // €0.50 per km
        "time_cost": 500.00,          // €50 per hour
        "empty_driving_cost": 150.00   // €0.30 per km for empty driving
    }
}
```
- **Error Responses**:
  - 400: Invalid route ID format
  - 404: Route not found
  - 500: Internal server error

#### Implementation Notes
- The endpoint is implemented as a direct Flask route instead of using Flask-RESTful
- Cost calculations are performed using the simplified `CostCalculationService`
- The service calculates costs based on:
  - Total distance (main route + empty driving)
  - Total duration in hours
  - Empty driving distance
- All costs are currently returned in EUR

### 3. Cost Settings Management

#### GET /costs/settings

Retrieves all cost settings.

**Response (200 OK):**
```json
[
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "type": "fuel",
        "category": "variable",
        "base_value": 1.5,
        "multiplier": 1.0,
        "currency": "EUR",
        "is_enabled": true,
        "description": "Fuel cost per kilometer"
    },
    {
        "id": "660e8400-e29b-41d4-a716-446655440000",
        "type": "driver",
        "category": "fixed",
        "base_value": 200.0,
        "multiplier": 1.0,
        "currency": "EUR",
        "is_enabled": true,
        "description": "Driver daily rate"
    }
]
```

#### POST /costs/settings

Updates one or more cost settings.

**Request Body:**
```json
[
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "base_value": 1.8,
        "multiplier": 1.2,
        "is_enabled": true
    }
]
```

**Response (200 OK):**
```json
[
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "type": "fuel",
        "category": "variable",
        "base_value": 1.8,
        "multiplier": 1.2,
        "currency": "EUR",
        "is_enabled": true,
        "description": "Fuel cost per kilometer"
    }
]
```

**Error Responses:**
- `400 Bad Request`: Invalid request format or missing required fields
- `404 Not Found`: One or more cost settings not found
- `500 Internal Server Error`: Server-side error

### 4. Offer Generation

#### POST /offer

Generates an offer based on route and margin.

**Request Body:**
```json
{
    "route_id": "550e8400-e29b-41d4-a716-446655440000",
    "margin": 15.0
}
```

**Response (200 OK):**
```json
{
    "id": "750e8400-e29b-41d4-a716-446655440123",
    "route_id": "550e8400-e29b-41d4-a716-446655440000",
    "total_price": 1250.0,
    "margin_percentage": 15.0,
    "fun_fact": "This route crosses through 3 different countries!"
}
```

**Error Responses:**
- `400 Bad Request`: Missing required field or invalid data
- `404 Not Found`: Route not found
- `500 Internal Server Error`: Server-side error

### 5. Data Review

#### GET /data/review

Retrieves historical routes and offers.

**Query Parameters:**
- `start_date` (optional): ISO date string
- `end_date` (optional): ISO date string
- `limit` (optional): Number of records to return (default: 10)
- `offset` (optional): Number of records to skip (default: 0)

**Response (200 OK):**
```json
{
    "total_count": 100,
    "records": [
        {
            "offer_id": "660e8400-e29b-41d4-a716-446655440000",
            "route_id": "550e8400-e29b-41d4-a716-446655440000",
            "origin": "Berlin, Germany",
            "destination": "Paris, France",
            "created_at": "2024-01-14T12:00:00Z",
            "final_price": 1529.50,
            "status": "active"
        }
    ]
}
```

**Error Responses:**
- `400 Bad Request`: Invalid query parameters
- `500 Internal Server Error`: Server-side error

## Error Response Format

All error responses follow this format:
```json
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human readable error message",
        "details": {
            "field1": "Specific error detail",
            "field2": "Another error detail"
        },
        "timestamp": "2024-01-14T12:00:00Z"
    }
}
```

## Rate Limiting

The PoC version does not implement rate limiting. This will be added in future versions.

## Notes

1. All timestamps are in ISO 8601 format and UTC timezone
2. All monetary values are in EUR
3. Distances are in kilometers
4. Weights are in kilograms
5. The PoC uses mocked data for route planning and empty driving calculations
