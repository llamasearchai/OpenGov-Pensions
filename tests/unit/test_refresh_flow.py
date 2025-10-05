import pytest
from fastapi.testclient import TestClient
from opengovpension.web.app import app

client = TestClient(app)

@pytest.mark.parametrize("email", ["user1@example.com"])  # simple param
def test_refresh_flow(email):
    r = client.post('/api/v1/auth/register', json={'email': email, 'password': 'pass123'})
    assert r.status_code == 201
    data = r.json()
    assert 'access_token' in data and 'refresh_token' in data

    refresh = data['refresh_token']
    r2 = client.post('/api/v1/auth/refresh', json={'refresh_token': refresh})
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2['access_token'] != data['access_token']  # rotation
    assert data2['refresh_token'] != refresh
