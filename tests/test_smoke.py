
def test_machines_empty(client):
    response = client.get("/machines")
    assert response.status_code == 200
    assert response.json() == []


def test_machines_fixture_creates_three(client, test_machines):
    response = client.get("/machines")
    assert len(response.json()) == 3


def test_isolation_holds(client):
    """If this fails, the rollback isn't working and every later test lies."""
    response = client.get("/machines")
    assert response.json() == []


def test_auth_is_required(client):
    response = client.post("/machines/", json={
        "name": "X", "line": "L", "location": "Hall 1",
    })
    assert response.status_code == 401


def test_authorized_client_can_write(authorized_client, test_user):
    response = authorized_client.post("/machines/", json={
        "name": "X", "line": "L", "location": "Hall 1",
    })
    assert response.status_code == 201, response.text
    assert response.json()["created_by"] == test_user["id"]


def test_reading_counts(client, test_machines, test_readings):
    m = test_machines
    assert len(client.get(f"/machines/{m[0].id}/readings").json()) == 8
    assert len(client.get(f"/machines/{m[0].id}/readings?metric=vibration_rms").json()) == 5
    assert len(client.get(f"/machines/{m[1].id}/readings").json()) == 4
    assert client.get(f"/machines/{m[2].id}/readings").json() == []