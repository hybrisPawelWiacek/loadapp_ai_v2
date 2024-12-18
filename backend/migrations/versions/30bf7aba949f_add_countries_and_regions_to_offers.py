"""Add countries and regions to offers

Revision ID: 30bf7aba949f
Revises: 
Create Date: 2024-12-10 01:38:21.056527

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '30bf7aba949f'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('alert_rules',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('metric_name', sa.String(), nullable=False),
    sa.Column('condition_type', sa.String(), nullable=False),
    sa.Column('threshold', sa.Float(), nullable=False),
    sa.Column('comparison', sa.String(), nullable=False),
    sa.Column('is_enabled', sa.Boolean(), nullable=False),
    sa.Column('severity', sa.String(), nullable=False),
    sa.Column('cooldown_minutes', sa.Integer(), nullable=False),
    sa.Column('aggregation_window', sa.Integer(), nullable=True),
    sa.Column('tags_filter', sa.JSON(), nullable=True),
    sa.Column('notification_channels', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('cost_settings',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('category', sa.String(), nullable=False),
    sa.Column('value', sa.Float(), nullable=False),
    sa.Column('multiplier', sa.Float(), nullable=False),
    sa.Column('currency', sa.String(), nullable=False),
    sa.Column('is_enabled', sa.Boolean(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('created_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('last_updated', sa.DateTime(), nullable=False),
    sa.Column('validation_rules', sa.JSON(), nullable=True),
    sa.Column('historical_data', sa.JSON(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('metric_aggregates',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('metric_name', sa.String(), nullable=False),
    sa.Column('aggregation_type', sa.String(), nullable=False),
    sa.Column('value', sa.Float(), nullable=False),
    sa.Column('start_time', sa.DateTime(), nullable=False),
    sa.Column('end_time', sa.DateTime(), nullable=False),
    sa.Column('tags', sa.JSON(), nullable=False),
    sa.Column('sample_size', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('metric_logs',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('metric_name', sa.String(), nullable=False),
    sa.Column('value', sa.Float(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=False),
    sa.Column('tags', sa.JSON(), nullable=False),
    sa.Column('source', sa.String(), nullable=True),
    sa.Column('context', sa.JSON(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('routes',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('origin_address', sa.String(), nullable=False),
    sa.Column('origin_latitude', sa.Float(), nullable=False),
    sa.Column('origin_longitude', sa.Float(), nullable=False),
    sa.Column('destination_address', sa.String(), nullable=False),
    sa.Column('destination_latitude', sa.Float(), nullable=False),
    sa.Column('destination_longitude', sa.Float(), nullable=False),
    sa.Column('pickup_time', sa.DateTime(), nullable=False),
    sa.Column('delivery_time', sa.DateTime(), nullable=False),
    sa.Column('last_calculated', sa.DateTime(), nullable=True),
    sa.Column('total_duration_hours', sa.Float(), nullable=True),
    sa.Column('total_cost', sa.Float(), nullable=True),
    sa.Column('currency', sa.String(), nullable=True),
    sa.Column('is_feasible', sa.Boolean(), nullable=True),
    sa.Column('duration_validation', sa.Boolean(), nullable=True),
    sa.Column('empty_driving', sa.JSON(), nullable=True),
    sa.Column('main_route', sa.JSON(), nullable=True),
    sa.Column('timeline', sa.JSON(), nullable=True),
    sa.Column('timeline_events', sa.JSON(), nullable=True),
    sa.Column('transport_type', sa.JSON(), nullable=True),
    sa.Column('cargo', sa.JSON(), nullable=True),
    sa.Column('cost_breakdown', sa.JSON(), nullable=True),
    sa.Column('optimization_insights', sa.JSON(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('alert_events',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('alert_rule_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('triggered_value', sa.Float(), nullable=False),
    sa.Column('triggered_at', sa.DateTime(), nullable=False),
    sa.Column('resolved_at', sa.DateTime(), nullable=True),
    sa.Column('context', sa.JSON(), nullable=False),
    sa.Column('notification_sent', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['alert_rule_id'], ['alert_rules.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('offers',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('route_id', sa.UUID(), nullable=False),
    sa.Column('client_id', sa.UUID(), nullable=True),
    sa.Column('countries', sa.JSON(), nullable=True),
    sa.Column('regions', sa.JSON(), nullable=True),
    sa.Column('cost_breakdown', sa.JSON(), nullable=False),
    sa.Column('margin_percentage', sa.Float(), nullable=False),
    sa.Column('final_price', sa.Float(), nullable=False),
    sa.Column('currency', sa.Enum('EUR', 'USD', 'GBP', name='currency'), nullable=False),
    sa.Column('status', sa.Enum('DRAFT', 'PENDING', 'SENT', 'ACCEPTED', 'REJECTED', 'EXPIRED', name='offerstatus'), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('expires_at', sa.DateTime(), nullable=True),
    sa.Column('offer_metadata', sa.JSON(), nullable=False),
    sa.ForeignKeyConstraint(['route_id'], ['routes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('offer_events',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('offer_id', sa.UUID(), nullable=False),
    sa.Column('event_type', sa.String(), nullable=False),
    sa.Column('event_data', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('event_metadata', sa.JSON(), nullable=False),
    sa.ForeignKeyConstraint(['offer_id'], ['offers.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('offer_versions',
    sa.Column('entity_id', sa.UUID(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('data', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('change_reason', sa.String(), nullable=True),
    sa.Column('version_metadata', sa.JSON(), nullable=False),
    sa.ForeignKeyConstraint(['entity_id'], ['offers.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('offer_versions')
    op.drop_table('offer_events')
    op.drop_table('offers')
    op.drop_table('alert_events')
    op.drop_table('routes')
    op.drop_table('metric_logs')
    op.drop_table('metric_aggregates')
    op.drop_table('cost_settings')
    op.drop_table('alert_rules')
    # ### end Alembic commands ###
