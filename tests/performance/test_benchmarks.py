import pytest
import time
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

from tests.fixtures.factories import (
    RouteFactory, OfferFactory, UserFactory,
    create_complex_scenario
)
from backend.domain.services.route_service import RouteService
from backend.domain.services.offer_service import OfferService
from backend.domain.services.cost_calculation_service import CostCalculationService

# Performance thresholds
THRESHOLDS = {
    'database': {
        'bulk_insert': 5.0,  # seconds
        'complex_query': 1.0,
        'transaction': 0.5
    },
    'api': {
        'response_time': 0.5,
        'concurrent_users': 100
    },
    'services': {
        'route_calculation': 2.0,
        'offer_generation': 1.0,
        'cost_calculation': 0.5
    }
}

@pytest.mark.performance
class TestDatabasePerformance:
    """Database performance test suite."""

    def test_bulk_insert_performance(self, db_session: Session):
        """Test bulk insert performance."""
        start_time = time.time()
        
        # Create complex test scenario
        scenario = create_complex_scenario(
            num_users=10,
            routes_per_user=5,
            offers_per_route=3
        )
        
        duration = time.time() - start_time
        assert duration < THRESHOLDS['database']['bulk_insert'], \
            f"Bulk insert took too long: {duration:.2f}s"
        
        # Verify data integrity
        total_users = len(scenario['users'])
        total_routes = len(scenario['routes'])
        total_offers = len(scenario['offers'])
        
        assert total_users == 10
        assert total_routes == 50
        assert total_offers == 150

    def test_complex_query_performance(self, db_session: Session):
        """Test complex query performance."""
        # Create test data
        create_complex_scenario(num_users=5, routes_per_user=10)
        
        start_time = time.time()
        
        # Execute complex query
        result = db_session.execute(text("""
            SELECT 
                r.id,
                COUNT(DISTINCT o.id) as offer_count,
                AVG(o.final_price) as avg_price,
                MAX(o.margin_percentage) as max_margin
            FROM routes r
            LEFT JOIN offers o ON r.id = o.route_id
            GROUP BY r.id
            HAVING COUNT(DISTINCT o.id) > 2
            ORDER BY avg_price DESC
            LIMIT 10
        """))
        
        duration = time.time() - start_time
        assert duration < THRESHOLDS['database']['complex_query'], \
            f"Complex query took too long: {duration:.2f}s"

    def test_concurrent_transactions(self, db_session: Session):
        """Test concurrent transaction performance."""
        import threading
        import queue
        
        def worker(q: queue.Queue, route_id: str):
            try:
                with db_session.begin():
                    # Update route status
                    db_session.execute(
                        text("UPDATE routes SET status = 'COMPLETED' WHERE id = :id"),
                        {'id': route_id}
                    )
                    time.sleep(0.1)  # Simulate some work
            except Exception as e:
                q.put(e)
            else:
                q.put(None)

        # Create test route
        route = RouteFactory.create()
        
        # Start multiple threads
        threads = []
        results = queue.Queue()
        
        start_time = time.time()
        
        for _ in range(10):
            t = threading.Thread(
                target=worker,
                args=(results, route.id)
            )
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        duration = time.time() - start_time
        assert duration < THRESHOLDS['database']['transaction'], \
            f"Concurrent transactions took too long: {duration:.2f}s"
        
        # Check for errors
        errors = []
        while not results.empty():
            result = results.get()
            if result is not None:
                errors.append(result)
        
        assert not errors, f"Concurrent transactions had errors: {errors}"

@pytest.mark.performance
class TestServicePerformance:
    """Service layer performance test suite."""

    def test_route_calculation_performance(self, route_service: RouteService):
        """Test route calculation performance."""
        routes = [RouteFactory.build() for _ in range(100)]
        
        start_time = time.time()
        
        for route in routes:
            route_service.calculate_route_metrics(route)
        
        duration = time.time() - start_time
        assert duration < THRESHOLDS['services']['route_calculation'], \
            f"Route calculations took too long: {duration:.2f}s"

    def test_offer_generation_performance(
        self,
        offer_service: OfferService,
        cost_service: CostCalculationService
    ):
        """Test offer generation performance."""
        routes = [RouteFactory.create() for _ in range(50)]
        
        start_time = time.time()
        
        for route in routes:
            cost = cost_service.calculate_cost(route)
            offer_service.generate_offer(route, cost, margin_percentage=15.0)
        
        duration = time.time() - start_time
        assert duration < THRESHOLDS['services']['offer_generation'], \
            f"Offer generation took too long: {duration:.2f}s"

@pytest.mark.performance
class TestAPIPerformance:
    """API endpoint performance test suite."""

    async def test_api_response_time(self, test_client, auth_headers):
        """Test API endpoint response times."""
        # Create test data
        route = RouteFactory.create()
        
        endpoints = [
            ('GET', f'/api/routes/{route.id}'),
            ('GET', '/api/routes/'),
            ('POST', '/api/routes/', {'origin': 'Berlin', 'destination': 'Munich'}),
            ('GET', '/api/offers/'),
            ('POST', '/api/offers/', {'route_id': route.id, 'margin': 15.0})
        ]
        
        for method, url, data in endpoints:
            start_time = time.time()
            
            if method == 'GET':
                response = await test_client.get(url, headers=auth_headers)
            else:
                response = await test_client.post(url, json=data, headers=auth_headers)
            
            duration = time.time() - start_time
            assert duration < THRESHOLDS['api']['response_time'], \
                f"{method} {url} took too long: {duration:.2f}s"
            assert response.status_code in (200, 201)

    async def test_api_concurrent_users(self, test_client, auth_headers):
        """Test API performance under concurrent load."""
        import asyncio
        import aiohttp
        
        async def concurrent_request(session, url: str) -> float:
            start_time = time.time()
            async with session.get(url, headers=auth_headers) as response:
                await response.json()
                return time.time() - start_time

        # Create test data
        routes = [RouteFactory.create() for _ in range(10)]
        url = '/api/routes/'
        
        async with aiohttp.ClientSession() as session:
            tasks = [
                concurrent_request(session, url)
                for _ in range(THRESHOLDS['api']['concurrent_users'])
            ]
            
            durations = await asyncio.gather(*tasks)
            
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            
            assert avg_duration < THRESHOLDS['api']['response_time'], \
                f"Average response time too high: {avg_duration:.2f}s"
            assert max_duration < THRESHOLDS['api']['response_time'] * 2, \
                f"Maximum response time too high: {max_duration:.2f}s"

def run_performance_profile():
    """Run performance profiling session."""
    import cProfile
    import pstats
    
    profiler = cProfile.Profile()
    scenario = create_complex_scenario(
        num_users=5,
        routes_per_user=10,
        offers_per_route=3
    )
    
    profiler.enable()
    
    # Perform various operations
    for route in scenario['routes']:
        route.calculate_metrics()
    
    for offer in scenario['offers']:
        offer.calculate_final_price()
    
    profiler.disable()
    
    # Save profiling results
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.dump_stats('reports/performance_profile.prof')
    
    # Print summary
    stats.print_stats(20)  # Show top 20 time-consuming operations

if __name__ == '__main__':
    run_performance_profile() 