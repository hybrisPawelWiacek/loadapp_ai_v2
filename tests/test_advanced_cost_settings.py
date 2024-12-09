import pytest
import streamlit as st
from unittest.mock import patch, MagicMock, ANY
import uuid
import json
from frontend.advanced_cost_settings import render_cost_settings

# Mock data
MOCK_COST_SETTINGS = [
    {
        "id": str(uuid.uuid4()),
        "type": "fuel",
        "is_enabled": True,
        "base_value": 2.5,
        "multiplier": 1.0
    },
    {
        "id": str(uuid.uuid4()),
        "type": "driver",
        "is_enabled": True,
        "base_value": 30.0,
        "multiplier": 1.2
    },
    {
        "id": str(uuid.uuid4()),
        "type": "maintenance",
        "is_enabled": False,
        "base_value": 0.5,
        "multiplier": 1.0
    }
]

@pytest.fixture
def mock_requests():
    """Fixture to mock requests for API calls"""
    with patch('frontend.advanced_cost_settings.requests') as mock_req:
        yield mock_req

@pytest.fixture
def mock_streamlit():
    """Fixture to mock Streamlit components"""
    with patch('frontend.advanced_cost_settings.st') as mock_st:
        yield mock_st

def test_fetch_cost_settings(mock_requests, mock_streamlit):
    """Test fetching cost settings from the API"""
    # Mock successful API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_COST_SETTINGS
    mock_requests.get.return_value = mock_response

    # Call the component
    render_cost_settings()

    # Verify API call
    mock_requests.get.assert_called_once_with(
        "http://127.0.0.1:5000/costs/settings",
        headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    )

    # Verify UI elements were created
    assert mock_streamlit.subheader.called
    assert mock_streamlit.form.called
    assert mock_streamlit.columns.called

def test_update_cost_settings(mock_requests, mock_streamlit):
    """Test updating cost settings through the UI"""
    # Mock GET response
    get_response = MagicMock()
    get_response.status_code = 200
    get_response.json.return_value = MOCK_COST_SETTINGS
    
    # Mock POST response
    post_response = MagicMock()
    post_response.status_code = 200
    
    # Set up requests mock to return different responses for GET and POST
    mock_requests.get.return_value = get_response
    mock_requests.post.return_value = post_response

    # Mock form inputs
    mock_form = MagicMock()
    mock_streamlit.form.return_value.__enter__.return_value = mock_form
    mock_form.form_submit_button.return_value = True  # Simulate form submission

    # Mock column structure
    mock_cols = [MagicMock(), MagicMock()]
    mock_streamlit.columns.return_value = mock_cols
    for col in mock_cols:
        col.__enter__.return_value = col

    # Mock container
    mock_container = MagicMock()
    mock_streamlit.container.return_value.__enter__.return_value = mock_container

    # Mock checkbox and number_input values
    def mock_checkbox(*args, **kwargs):
        return True if kwargs.get('value', False) else False

    def mock_number_input(*args, **kwargs):
        return kwargs.get('value', 0.0)

    mock_streamlit.checkbox.side_effect = mock_checkbox
    mock_streamlit.number_input.side_effect = mock_number_input

    # Call the component
    render_cost_settings()

    # Verify POST request was made with updated settings
    mock_requests.post.assert_called_once_with(
        "http://127.0.0.1:5000/costs/settings",
        json=ANY,  # We don't need to verify exact payload
        headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    )
    
    # Verify success message was shown
    mock_streamlit.success.assert_called_once()

def test_api_error_handling(mock_requests, mock_streamlit):
    """Test handling of API errors"""
    # Mock failed API response
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_requests.get.return_value = mock_response

    # Call the component
    render_cost_settings()

    # Verify error message was shown
    mock_streamlit.error.assert_called_once()

def test_validation(mock_requests, mock_streamlit):
    """Test input validation"""
    # Mock successful GET response
    get_response = MagicMock()
    get_response.status_code = 200
    get_response.json.return_value = MOCK_COST_SETTINGS
    mock_requests.get.return_value = get_response

    # Mock form with invalid inputs
    mock_form = MagicMock()
    mock_streamlit.form.return_value.__enter__.return_value = mock_form
    mock_form.form_submit_button.return_value = True

    # Mock negative value input
    def mock_number_input(*args, **kwargs):
        if 'base_value' in kwargs.get('key', ''):
            return -1.0  # Invalid negative value
        return 1.0

    mock_streamlit.number_input.side_effect = mock_number_input
    mock_streamlit.checkbox.return_value = True

    # Call the component
    render_cost_settings()

    # Verify that the number_input was called with min_value=0.0
    number_input_calls = mock_streamlit.number_input.call_args_list
    for call in number_input_calls:
        if 'base_value' in call[1].get('key', ''):
            assert call[1].get('min_value', None) == 0.0

def test_ui_layout(mock_requests, mock_streamlit):
    """Test UI layout structure"""
    # Mock successful API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = MOCK_COST_SETTINGS
    mock_requests.get.return_value = mock_response

    # Mock column structure
    mock_cols = [MagicMock(), MagicMock()]
    mock_streamlit.columns.return_value = mock_cols
    for col in mock_cols:
        col.__enter__.return_value = col

    # Mock container
    mock_container = MagicMock()
    mock_streamlit.container.return_value.__enter__.return_value = mock_container

    # Call the component
    render_cost_settings()

    # Verify UI structure
    assert mock_streamlit.subheader.called
    assert mock_streamlit.form.called
    assert mock_streamlit.columns.called
    assert mock_streamlit.container.called

    # Verify that we create two columns for layout
    mock_streamlit.columns.assert_called_with(2)
