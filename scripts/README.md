# Test Database Setup Scripts

## PostgreSQL Test Database Setup

This directory contains scripts for setting up and managing the test PostgreSQL database used in our testing infrastructure.

### Prerequisites

1. PostgreSQL server installed and running
2. Python 3.8 or higher (Python 3.13+ requires psycopg3)
3. Required Python packages:
   ```bash
   pip install psycopg    # Modern PostgreSQL adapter for Python
   ```

### Setup Script

The `setup_test_db.py` script handles:
- Creating the test database
- Setting up test users
- Installing required extensions
- Managing database state

#### Usage

1. **Basic Setup**
   ```bash
   python scripts/setup_test_db.py
   ```
   This will:
   - Create test database if it doesn't exist
   - Create test user with appropriate permissions
   - Set up required PostgreSQL extensions

2. **Reset Database**
   ```bash
   python scripts/setup_test_db.py --reset
   ```
   This will:
   - Drop all tables in the test database
   - Reset to a clean state
   - Requires confirmation

3. **Custom Configuration**
   ```bash
   python scripts/setup_test_db.py --config path/to/config.json
   ```
   Use a custom configuration file instead of defaults.

### Default Configuration

```python
DEFAULT_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'test_db'
}
```

You can override these settings by:
1. Environment variables:
   ```bash
   export TEST_DATABASE_URL="postgresql+psycopg://user:pass@host:port/dbname"
   ```
2. Command-line config file:
   ```bash
   python scripts/setup_test_db.py --config custom_config.json
   ```

### PostgreSQL Extensions

The script sets up these extensions:
- `uuid-ossp`: For UUID generation
- `pg_trgm`: For text search functionality
- `btree_gin`: For GIN indexes

### Test User Permissions

The script creates a test user with:
- Username: `test_user`
- Password: `test_password`
- Full privileges on test database

### Common Issues

1. **PostgreSQL Not Running**
   ```bash
   # macOS
   brew services start postgresql
   
   # Linux
   sudo service postgresql start
   
   # Windows
   net start postgresql
   ```

2. **Permission Denied**
   - Ensure PostgreSQL user has appropriate permissions
   - Check PostgreSQL configuration (pg_hba.conf)

3. **Port Already in Use**
   - Check if another PostgreSQL instance is running
   - Modify port in configuration

4. **Python 3.13+ Compatibility**
   - Ensure using psycopg3 instead of psycopg2
   - Update connection string to use psycopg driver
   - Check for latest psycopg version

### Integration with Tests

The test database is used when running tests with the `@pytest.mark.db_type("postgres")` marker:

```python
@pytest.mark.db_type("postgres")
def test_complex_query(db_session):
    """Test PostgreSQL-specific features."""
    result = db_session.execute(
        text("SELECT * FROM routes WHERE origin_address @@ to_tsquery('english', 'berlin')")
    )
    assert result is not None
```

### Connection Pooling

The test infrastructure uses SQLAlchemy's connection pooling with psycopg3:
- Default pool size: 5 connections
- Maximum overflow: 10 connections
- Connection timeout: 30 seconds
- Connection recycling: 30 minutes
- Health checks enabled
- TCP keepalive enabled

### Maintenance

1. **Regular Cleanup**
   ```bash
   # Reset database to clean state
   python scripts/setup_test_db.py --reset
   ```

2. **Update Extensions**
   - Script automatically handles extension updates
   - New extensions can be added to the `extensions` list

3. **Backup Test Data**
   ```bash
   pg_dump -U postgres test_db > test_db_backup.sql
   ```

### Security Notes

1. This is for **testing only** - do not use in production
2. Default credentials should be changed in production
3. Test database should be isolated from production
4. Regular security updates should be applied

### Contributing

When adding new features to the database setup:
1. Update the setup script
2. Add appropriate tests
3. Update this documentation
4. Consider backward compatibility 