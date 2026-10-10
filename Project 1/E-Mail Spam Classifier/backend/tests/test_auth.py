import pytest
import os
import sys

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, configure_database

def test_app_imports_cleanly():
    """Verify that importing app does not call sys.exit and initializes properly."""
    assert app is not None
    assert app.name == 'app'

def test_sqlite_strictly_forbidden():
    """Verify that SQLite connection strings are rejected with ValueError."""
    with pytest.raises(ValueError, match="SQLite is not supported. PostgreSQL is strictly required."):
        configure_database(app, 'sqlite:///test.db')

def test_postgresql_configuration():
    """Verify that a PostgreSQL URI is accepted and configured on the app."""
    test_pg_url = 'postgresql://user:password@localhost:5432/testdb'
    success = configure_database(app, test_pg_url)
    assert success is True
    assert app.config['SQLALCHEMY_DATABASE_URI'] == test_pg_url
    
    # Reset back to None for subsequent tests
    configure_database(app, None)

def test_unconfigured_database_returns_503_for_db_routes(monkeypatch):
    """Verify that database-dependent routes return HTTP 503 when DATABASE_URL is not set."""
    monkeypatch.delenv('DATABASE_URL', raising=False)
    app.config['SQLALCHEMY_DATABASE_URI'] = None
    with app.test_client() as client:
        res = client.post('/api/auth/sync', json={'email': 'test@example.com'})
        assert res.status_code == 503
        data = res.get_json()
        assert "Database not configured" in data.get("error", "")

def test_health_endpoint():
    """Verify the /api/health endpoint works without requiring a database."""
    with app.test_client() as client:
        res = client.get('/api/health')
        assert res.status_code == 200
        data = res.get_json()
        assert data['status'] == 'healthy'
