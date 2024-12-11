import pytest
import time
from typing import Dict, Any
from sqlalchemy import text

from backend.infrastructure.database.models import Route, Offer
from tests.fixtures.performance import optimize_query_for_route_listing

@pytest.mark.performance
class TestDatabasePerformance:
    """Test suite for database performance optimization."""

    def test_bulk_insert_performance(self, db_session, performance_dataset, cleanup_performance_data):
        """Test performance of bulk insert operations."""
        start_time = time.time()
        
        # Create 1000 routes with 5 offers each
        routes = []
        for i in range(1000):
            route = Route(
                origin_latitude=52.5200,
                origin_longitude=13.4050,
                origin_address=f"Origin {i}",
                destination_latitude=48.8566,
                destination_longitude=2.3522,
                destination_address=f"Destination {i}",
                total_cost=1000.0 + i
            )
            routes.append(route)
        
        db_session.bulk_save_objects(routes)
        db_session.commit()
        
        route_ids = [route.id for route in routes]
        offers = []
        for route_id in route_ids:
            for i in range(5):
                offer = Offer(
                    route_id=route_id,
                    total_cost=1000.0 + (i * 100),
                    margin=0.15 + (i * 0.01),
                    final_price=1200.0 + (i * 100),
                    status="pending"
                )
                offers.append(offer)
        
        db_session.bulk_save_objects(offers)
        db_session.commit()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Assert performance targets
        assert duration < 5.0, f"Bulk insert took too long: {duration} seconds"
        assert len(routes) == 1000
        assert len(offers) == 5000

    def test_query_optimization(self, db_session, performance_dataset, cleanup_performance_data):
        """Test query optimization strategies."""
        # Test different query patterns
        queries = [
            {
                "name": "simple_listing",
                "filters": {"limit": 100}
            },
            {
                "name": "filtered_listing",
                "filters": {
                    "min_cost": 1500.0,
                    "max_cost": 2000.0,
                    "limit": 100
                }
            },
            {
                "name": "complex_listing",
                "filters": {
                    "with_offers": True,
                    "min_cost": 1500.0,
                    "limit": 100
                }
            },
            {
                "name": "minimal_listing",
                "filters": {
                    "minimal": True,
                    "limit": 100
                }
            }
        ]
        
        results = {}
        for query in queries:
            start_time = time.time()
            routes = optimize_query_for_route_listing(db_session, query["filters"])
            duration = time.time() - start_time
            results[query["name"]] = {
                "duration": duration,
                "count": len(routes)
            }
            
            # Assert performance targets for each query type
            assert duration < 1.0, f"Query {query['name']} took too long: {duration} seconds"

    def test_connection_pool_performance(self, db_engine):
        """Test database connection pool performance."""
        def execute_query() -> float:
            """Execute a simple query and return duration."""
            start_time = time.time()
            with db_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return time.time() - start_time
        
        # Test sequential connections
        sequential_times = [execute_query() for _ in range(100)]
        avg_sequential = sum(sequential_times) / len(sequential_times)
        
        # Assert connection pool performance
        assert avg_sequential < 0.01, f"Average connection time too high: {avg_sequential} seconds"
        assert max(sequential_times) < 0.05, f"Max connection time too high: {max(sequential_times)} seconds"

    def test_memory_usage(self, db_session, performance_dataset, cleanup_performance_data):
        """Test memory usage optimization."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform memory-intensive operations
        routes = optimize_query_for_route_listing(
            db_session,
            {
                "with_offers": True,
                "limit": 1000
            }
        )
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Assert memory usage targets
        assert memory_increase < 50, f"Memory usage increased by {memory_increase}MB"
        assert len(routes) > 0

    def test_transaction_performance(self, db_session):
        """Test transaction performance and isolation."""
        start_time = time.time()
        
        # Perform multiple transactions
        for i in range(100):
            try:
                # Start transaction
                route = Route(
                    origin_latitude=52.5200,
                    origin_longitude=13.4050,
                    origin_address=f"Origin {i}",
                    destination_latitude=48.8566,
                    destination_longitude=2.3522,
                    destination_address=f"Destination {i}",
                    total_cost=1000.0 + i
                )
                db_session.add(route)
                db_session.flush()
                
                # Create associated offer
                offer = Offer(
                    route_id=route.id,
                    total_cost=1000.0,
                    margin=0.15,
                    final_price=1150.0,
                    status="pending"
                )
                db_session.add(offer)
                
                # Commit transaction
                db_session.commit()
            except Exception:
                db_session.rollback()
                raise
        
        duration = time.time() - start_time
        
        # Assert transaction performance
        assert duration < 2.0, f"Transactions took too long: {duration} seconds"
        
        # Verify data consistency
        route_count = db_session.query(Route).count()
        offer_count = db_session.query(Offer).count()
        assert route_count == 100
        assert offer_count == 100

    @pytest.mark.parametrize("batch_size", [100, 500, 1000])
    def test_batch_processing_performance(self, db_session, batch_size):
        """Test performance of batch processing with different sizes."""
        start_time = time.time()
        
        # Process data in batches
        total_records = 5000
        processed = 0
        
        while processed < total_records:
            batch = []
            for i in range(batch_size):
                if processed + i >= total_records:
                    break
                    
                route = Route(
                    origin_latitude=52.5200,
                    origin_longitude=13.4050,
                    origin_address=f"Origin {processed + i}",
                    destination_latitude=48.8566,
                    destination_longitude=2.3522,
                    destination_address=f"Destination {processed + i}",
                    total_cost=1000.0 + i
                )
                batch.append(route)
            
            db_session.bulk_save_objects(batch)
            db_session.commit()
            processed += len(batch)
        
        duration = time.time() - start_time
        
        # Assert batch processing performance
        assert duration < 10.0, f"Batch processing took too long: {duration} seconds"
        assert db_session.query(Route).count() == total_records