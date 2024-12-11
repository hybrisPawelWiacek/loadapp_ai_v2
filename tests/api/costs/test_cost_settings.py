import json

def test_get_cost_settings(client, test_cost_settings):
    """Test GET /costs/settings endpoint."""
    response = client.get('/costs/settings')
    
    assert response.status_code == 200
    settings_data = json.loads(response.data)
    
    assert isinstance(settings_data, list)
    assert len(settings_data) == len(test_cost_settings)
    
    for setting in settings_data:
        assert set(setting.keys()) == {
            'id', 'type', 'category', 'base_value', 'multiplier',
            'currency', 'is_enabled', 'description'
        }
        # Find corresponding test setting
        test_setting = next(
            s for s in test_cost_settings 
            if str(s.id) == setting['id']
        )
        assert setting['type'] == test_setting.type
        assert setting['category'] == test_setting.category
        assert setting['base_value'] == test_setting.base_value
        assert setting['multiplier'] == test_setting.multiplier
        assert setting['currency'] == test_setting.currency
        assert setting['is_enabled'] == test_setting.is_enabled
        assert setting['description'] == test_setting.description

def test_update_cost_settings(client, test_cost_settings):
    """Test POST /costs/settings endpoint."""
    updates = [
        {
            'id': str(test_cost_settings[0].id),
            'base_value': 2.0,
            'is_enabled': False
        },
        {
            'id': str(test_cost_settings[1].id),
            'multiplier': 1.5
        }
    ]
    
    response = client.post(
        '/costs/settings',
        data=json.dumps(updates),
        content_type='application/json'
    )
    
    assert response.status_code == 200
    updated_settings = json.loads(response.data)
    assert len(updated_settings) == len(updates)

def test_update_cost_settings_invalid_input(client, test_cost_settings):
    """Test POST /costs/settings endpoint with invalid input."""
    # Test with non-existent ID
    invalid_updates = [
        {
            'id': 'non-existent-id',
            'base_value': 2.0
        }
    ]
    
    response = client.post(
        '/costs/settings',
        data=json.dumps(invalid_updates),
        content_type='application/json'
    )
    
    assert response.status_code == 400

    # Test with invalid value type
    invalid_updates = [
        {
            'id': str(test_cost_settings[0].id),
            'base_value': 'not-a-number'
        }
    ]
    
    response = client.post(
        '/costs/settings',
        data=json.dumps(invalid_updates),
        content_type='application/json'
    )
    
    assert response.status_code == 400 