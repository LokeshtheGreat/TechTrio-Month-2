import pytest

@pytest.fixture(autouse=True)
def isolate_supabase_test_env(monkeypatch):
    """
    Ensure tests are isolated from developer's local .env SUPABASE_URL,
    preventing spurious 'Token is missing the iss claim' errors on mock test tokens
    unless explicitly configured in a specific test.
    """
    monkeypatch.delenv('SUPABASE_URL', raising=False)
