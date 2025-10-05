import pytest
from fastapi.testclient import TestClient
from opengovpension.web.app import app

client = TestClient(app)

@pytest.fixture
def superuser():
    r = client.post('/api/v1/auth/register', json={'email': 'admin@example.com', 'password': 'pass123'})
    assert r.status_code == 201
    return r.json()['access_token']

@pytest.mark.dependency()
def test_assign_role(superuser):
    # First user auto superuser, assign 'admin' role to self to satisfy require_roles('admin') for endpoint usage
    headers = {'Authorization': f'Bearer {superuser}'}
    r = client.post('/api/v1/auth/roles/assign', json={'email': 'admin@example.com', 'role': 'admin'}, headers=headers)
    assert r.status_code == 200
    assert 'admin' in r.json()['roles']
