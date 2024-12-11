import streamlit as st
import requests
import pandas as pd
from typing import Dict, List, Optional
from dataclasses import dataclass
import json
from datetime import datetime, timedelta

# Constants
API_URL = "http://127.0.0.1:5000/api/v1"
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

@dataclass
class CostSetting:
    """Data class for cost setting item."""
    id: str
    type: str
    category: str
    is_enabled: bool
    base_value: float
    multiplier: float
    currency: str
    description: Optional[str] = None

def validate_cost_setting(setting: Dict) -> List[str]:
    """Validate a cost setting before sending to the API."""
    errors = []
    
    # Validate base_value
    if setting['base_value'] <= 0:
        errors.append(f"Base value for {setting['type']} must be greater than 0")
    
    # Validate multiplier
    if setting['multiplier'] <= 0:
        errors.append(f"Multiplier for {setting['type']} must be greater than 0")
    elif setting['multiplier'] > 10:
        errors.append(f"Multiplier for {setting['type']} seems unusually high (>10)")
    
    return errors

def fetch_settings() -> List[CostSetting]:
    """Fetch current cost settings from the API."""
    try:
        response = requests.get(f"{API_URL}/costs/settings", headers=HEADERS)
        if response.status_code == 200:
            settings_data = response.json()
            return [
                CostSetting(
                    id=item['id'],
                    type=item['type'],
                    category=item['category'],
                    is_enabled=item['is_enabled'],
                    base_value=float(item['base_value']),
                    multiplier=float(item.get('multiplier', 1.0)),
                    currency=item.get('currency', 'EUR'),
                    description=item.get('description')
                )
                for item in settings_data
            ]
        st.error(f"Failed to fetch settings: {response.text}")
        return []
    except Exception as e:
        st.error(f"Error fetching settings: {str(e)}")
        return []

def save_settings(settings: List[Dict]) -> bool:
    """Save updated settings to the API."""
    try:
        response = requests.post(
            f"{API_URL}/costs/settings",
            headers=HEADERS,
            json=settings
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('warnings'):
                for warning in result['warnings']:
                    st.warning(warning)
            st.success("Settings saved successfully!")
            return True
            
        error_msg = response.json().get('error', 'Unknown error occurred')
        st.error(f"Failed to save settings: {error_msg}")
        if 'errors' in response.json():
            for error in response.json()['errors']:
                st.error(error)
        return False
        
    except Exception as e:
        st.error(f"Error saving settings: {str(e)}")
        return False

def render_cost_settings():
    """Render the cost settings page with editing capabilities."""
    st.header("Cost Settings")
    st.markdown("""
        Manage your transport cost settings here. Edit the base values and multipliers,
        then click 'Save Changes' to update the settings.
    """)
    
    # Initialize session state for settings if not exists
    if 'cost_settings' not in st.session_state:
        st.session_state.cost_settings = fetch_settings()
    
    # Refresh button
    if st.button("↻ Refresh Settings"):
        st.session_state.cost_settings = fetch_settings()
        st.experimental_rerun()
    
    if not st.session_state.cost_settings:
        st.warning("No cost settings found. Try refreshing the page.")
        return
    
    # Convert settings to DataFrame for display
    settings_data = []
    for setting in st.session_state.cost_settings:
        settings_data.append({
            'ID': setting.id,
            'Type': setting.type.title(),
            'Category': setting.category.title(),
            'Base Value': setting.base_value,
            'Multiplier': setting.multiplier,
            'Currency': setting.currency,
            'Enabled': setting.is_enabled,
            'Description': setting.description or ''
        })
    
    df = pd.DataFrame(settings_data)
    
    # Initialize session state for cost preview
    if 'preview_costs' not in st.session_state:
        st.session_state.preview_costs = None
    if 'original_settings' not in st.session_state:
        st.session_state.original_settings = df.copy()
    
    def get_cost_preview(updated_settings: pd.DataFrame) -> Dict:
        """Get cost preview for updated settings."""
        try:
            # Create a mock route for preview
            mock_route = {
                "id": "preview_route",
                "distance": 500,  # 500 km mock route
                "duration": 8,    # 8 hours
                "countries": ["DE", "FR"]  # Example countries
            }
            
            # Prepare settings diff for analysis
            settings_payload = []
            for _, row in updated_settings.iterrows():
                settings_payload.append({
                    'id': row['ID'],
                    'type': row['Type'].lower(),
                    'category': row['Category'].lower(),
                    'base_value': float(row['Base Value']),
                    'multiplier': float(row['Multiplier']),
                    'currency': row['Currency'],
                    'is_enabled': bool(row['Enabled'])
                })
            
            # Request cost analysis with updated settings
            response = requests.post(
                f"{API_URL}/costs/settings/analysis",
                json={
                    "route": mock_route,
                    "settings": settings_payload
                },
                headers=HEADERS
            )
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None
    
    # Create columns for layout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Display editable dataframe with callback
        edited_df = st.data_editor(
            df,
            column_config={
                'ID': st.column_config.TextColumn(
                    'ID',
                    disabled=True,
                    width='small'
                ),
                'Type': st.column_config.TextColumn(
                    'Type',
                    disabled=True,
                    width='small'
                ),
                'Category': st.column_config.TextColumn(
                    'Category',
                    disabled=True,
                    width='small'
                ),
                'Base Value': st.column_config.NumberColumn(
                    'Base Value',
                    help='Base cost value',
                    min_value=0,
                    format="%.2f",
                    width='small',
                    on_change=lambda: st.session_state.update({'preview_requested': True})
                ),
                'Multiplier': st.column_config.NumberColumn(
                    'Multiplier',
                    help='Cost multiplier',
                    min_value=0,
                    format="%.2f",
                    width='small',
                    on_change=lambda: st.session_state.update({'preview_requested': True})
                ),
                'Currency': st.column_config.TextColumn(
                    'Currency',
                    disabled=True,
                    width='small'
                ),
                'Enabled': st.column_config.CheckboxColumn(
                    'Enabled',
                    help='Enable/disable this cost setting',
                    width='small',
                    on_change=lambda: st.session_state.update({'preview_requested': True})
                ),
                'Description': st.column_config.TextColumn(
                    'Description',
                    width='medium'
                )
            },
            hide_index=True,
            key='settings_editor'
        )
        
        # Check if settings were changed
        settings_changed = not edited_df.equals(st.session_state.original_settings)
        
        # Get cost preview if settings changed
        if settings_changed or st.session_state.get('preview_requested', False):
            preview_data = get_cost_preview(edited_df)
            if preview_data:
                st.session_state.preview_costs = preview_data
            st.session_state.preview_requested = False
    
    with col2:
        st.markdown("### Cost Preview")
        
        # Display current vs projected costs
        if st.session_state.preview_costs:
            preview = st.session_state.preview_costs
            current_total = preview.get('current_total', 0)
            projected_total = preview.get('projected_total', 0)
            difference = projected_total - current_total
            percentage = (difference / current_total * 100) if current_total > 0 else 0
            
            st.metric(
                "Current Total Cost",
                f"€{current_total:.2f}",
                delta=None
            )
            
            st.metric(
                "Projected Total Cost",
                f"€{projected_total:.2f}",
                delta=f"{percentage:+.1f}%",
                delta_color="inverse"
            )
            
            # Show cost breakdown if available
            if 'breakdown' in preview:
                with st.expander("Cost Breakdown"):
                    for category, value in preview['breakdown'].items():
                        st.metric(
                            category.replace('_', ' ').title(),
                            f"€{value:.2f}"
                        )
            
            # Show impact warnings if any
            if 'warnings' in preview and preview['warnings']:
                st.warning(
                    "⚠️ Potential Impacts:\n" + 
                    "\n".join(f"- {w}" for w in preview['warnings'])
                )
        else:
            st.info("Make changes to see cost preview")
        
        # Show optimization score
        if st.session_state.preview_costs and 'optimization_score' in st.session_state.preview_costs:
            score = st.session_state.preview_costs['optimization_score']
            st.progress(score / 100, text=f"Optimization Score: {score}%")
    
    # Validation and save changes
    if settings_changed:
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("### Review Changes")
            st.markdown("The following settings have been modified:")
            
            # Show changed settings
            changes = []
            for idx, (orig, new) in enumerate(zip(st.session_state.original_settings.itertuples(), edited_df.itertuples())):
                if orig != new:
                    changes.append(f"- **{new.Type}**: Base Value: {orig.Base_Value:.2f} → {new.Base_Value:.2f}, "
                                f"Multiplier: {orig.Multiplier:.2f} → {new.Multiplier:.2f}")
            
            for change in changes:
                st.markdown(change)
        
        with col2:
            # Save changes button
            if st.button("Save Changes", type="primary", key="save_changes"):
                validation_errors = []
                updated_settings = []
                
                for _, row in edited_df.iterrows():
                    setting = {
                        'id': row['ID'],
                        'type': row['Type'].lower(),
                        'category': row['Category'].lower(),
                        'base_value': float(row['Base Value']),
                        'multiplier': float(row['Multiplier']),
                        'currency': row['Currency'],
                        'is_enabled': bool(row['Enabled']),
                        'description': row['Description']
                    }
                    
                    errors = validate_cost_setting(setting)
                    if errors:
                        validation_errors.extend(errors)
                    else:
                        updated_settings.append(setting)
                
                if validation_errors:
                    st.error("Please fix the following errors:")
                    for error in validation_errors:
                        st.error(error)
                else:
                    if save_settings(updated_settings):
                        st.session_state.original_settings = edited_df.copy()
                        st.session_state.preview_costs = None
                        st.rerun()
            
            # Reset button
            if st.button("Reset Changes", type="secondary", key="reset_changes"):
                st.session_state.preview_costs = None
                st.experimental_rerun()
    
    # Display optimization suggestions if available
    try:
        response = requests.get(f"{API_URL}/costs/settings/optimization", headers=HEADERS)
        if response.status_code == 200:
            suggestions = response.json()
            if suggestions:
                st.markdown("### Optimization Suggestions")
                for suggestion in suggestions:
                    st.info(suggestion)
    except Exception as e:
        st.error(f"Failed to fetch optimization suggestions: {str(e)}")
    
    # Add Historical Analysis section
    st.markdown("---")
    with st.expander("📈 Historical Analysis", expanded=False):
        st.markdown("""
            Analyze historical cost trends and their impact on your transport operations.
            Select a date range and view detailed cost analytics.
        """)
        
        # Date range selector
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=(datetime.now() - timedelta(days=30)).date(),
                max_value=datetime.now().date()
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=datetime.now().date(),
                min_value=start_date,
                max_value=datetime.now().date()
            )
        
        # Load data button
        if st.button("Load Historical Data", type="primary", key="load_historical"):
            try:
                analysis_response = requests.get(
                    f"{API_URL}/costs/settings/analysis",
                    params={
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    },
                    headers=HEADERS
                )
                
                if analysis_response.status_code == 200:
                    analysis_data = analysis_response.json()
                    
                    # Process and display the data
                    if analysis_data:
                        # Convert data for charting
                        df = pd.DataFrame(analysis_data['daily_costs'])
                        df['date'] = pd.to_datetime(df['date'])
                        df.set_index('date', inplace=True)
                        
                        # Display trend charts
                        st.subheader("Cost Trends")
                        tab1, tab2 = st.tabs(["Total Costs", "By Category"])
                        
                        with tab1:
                            st.line_chart(df[['total_cost']])
                            
                            # Calculate and display key metrics
                            avg_cost = df['total_cost'].mean()
                            cost_change = ((df['total_cost'].iloc[-1] - df['total_cost'].iloc[0]) 
                                         / df['total_cost'].iloc[0] * 100)
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Average Cost", f"€{avg_cost:.2f}")
                            with col2:
                                st.metric("Cost Change", f"{cost_change:+.1f}%")
                            with col3:
                                st.metric("Total Routes", str(analysis_data['total_routes']))
                        
                        with tab2:
                            # Display costs by category
                            category_cols = [col for col in df.columns if col != 'total_cost']
                            if category_cols:
                                st.line_chart(df[category_cols])
                                
                                # Show category breakdown
                                st.subheader("Category Analysis")
                                for category in category_cols:
                                    with st.expander(category.replace('_', ' ').title()):
                                        cat_avg = df[category].mean()
                                        cat_change = ((df[category].iloc[-1] - df[category].iloc[0]) 
                                                    / df[category].iloc[0] * 100)
                                        
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            st.metric("Average", f"€{cat_avg:.2f}")
                                        with col2:
                                            st.metric("Change", f"{cat_change:+.1f}%")
                        
                        # Display impact summary
                        st.subheader("Impact Summary")
                        if 'impact_summary' in analysis_data:
                            for impact in analysis_data['impact_summary']:
                                st.markdown(f"- {impact}")
                        
                        # Show cost-saving opportunities
                        if 'opportunities' in analysis_data:
                            st.subheader("Cost-Saving Opportunities")
                            for opportunity in analysis_data['opportunities']:
                                st.info(
                                    f"💡 {opportunity['description']}\n\n"
                                    f"Potential savings: €{opportunity['potential_savings']:.2f}"
                                )
                    
                    else:
                        st.info("No historical data available for the selected period.")
                
                else:
                    st.error("Failed to fetch historical analysis. Please try again.")
            
            except Exception as e:
                st.error(f"Error analyzing historical data: {str(e)}")

render_cost_settings()
