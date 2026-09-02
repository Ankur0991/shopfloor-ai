import pytest
import jwt
from datetime import timezone, timedelta
from app.config import settings

def machine_payload(**overrides):
    body = {"name": "Test Machine", "line": "Line A", "location": "Hall 1"}
    body.update(overrides)
    return body


# --- authentication ---------------------------------------------------------

def test_post_machine_without_token_is_401(client):
    response = client.post("/machines/", json=machine_payload())
    assert response.status_code == 401


def test_post_reading_without_token_is_401(client, test_machines):
    response = client.post("/readings/", json={
        "machine_id": test_machines[0].id,
        "metric": "vibration_rms",
        "value": 2.0,
        "unit": "mm/s",
    })
    assert response.status_code == 401


@pytest.mark.parametrize("bad_token", [
    "garbage",                                    # structurally invalid
    "Bearer.also.garbage",                        # three segments, not a JWT
    jwt.encode({"user_id": 1}, "wrong-secret-key", algorithm="HS256"),
])
def test_malformed_token_is_401_not_500(client, bad_token):
    """The one bug class no other test can see.

    Catching the wrong exception type in verify_access_token turns every
    bad token into a 500. Structurally-invalid and signed-with-wrong-key
    take different code paths, so both are needed.
    """
    response = client.post(
        "/machines/",
        json=machine_payload(),
        headers={"Authorization": f"Bearer {bad_token}"},
    )
    assert response.status_code == 401, response.text


def test_expired_token_is_401_not_500(client):
    """Signed with the CORRECT key, but past its exp claim.

    PyJWT raises ExpiredSignatureError, which is a sibling of DecodeError,
    not a subclass. `except jwt.DecodeError` catches the garbage cases above
    and lets this one through as a 500 — a bug that only appears once real
    tokens start ageing past their expiry in production.

    Catch jwt.PyJWTError (or jwt.InvalidTokenError) to cover both branches.
    """
    expired = jwt.encode(
        {
            "user_id": 1,
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        },
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    response = client.post(
        "/machines/",
        json=machine_payload(),
        headers={"Authorization": f"Bearer {expired}"},
    )
    assert response.status_code == 401, response.text


# --- created_by comes from the token, never the body ------------------------

def test_created_by_is_set_from_token(authorized_client, test_user):
    response = authorized_client.post("/machines/", json=machine_payload())
    assert response.status_code == 201, response.text
    assert response.json()["created_by"] == test_user["id"]


def test_created_by_cannot_be_forged(authorized_client, test_user):
    """A caller supplying created_by in the body must be ignored."""
    response = authorized_client.post(
        "/machines/", json=machine_payload(created_by=999)
    )
    assert response.status_code == 201, response.text
    assert response.json()["created_by"] == test_user["id"]


# --- PUT ownership ----------------------------------------------------------

def test_owner_can_update_own_machine(authorized_client, test_machines):
    machine = test_machines[0]
    response = authorized_client.put(
        f"/machines/{machine.id}", json=machine_payload(name="Renamed")
    )
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "Renamed"


def test_other_user_cannot_update_machine(second_client, test_machines):
    machine = test_machines[0]
    response = second_client.put(
        f"/machines/{machine.id}", json=machine_payload(name="Hijacked")
    )
    assert response.status_code == 403


def test_update_missing_machine_is_404_not_403(second_client):
    """404 before 403. Reversed, the API leaks which ids exist to users
    who have no access to them."""
    response = second_client.put("/machines/999", json=machine_payload())
    assert response.status_code == 404


# --- DELETE ownership -------------------------------------------------------

def test_owner_can_delete_own_machine(authorized_client, test_machines):
    machine = test_machines[0]
    response = authorized_client.delete(f"/machines/{machine.id}")
    assert response.status_code == 204


def test_other_user_cannot_delete_machine(second_client, authorized_client, test_machines):
    machine = test_machines[0]
    response = second_client.delete(f"/machines/{machine.id}")
    assert response.status_code == 403

    # and the machine still exists afterwards
    still_there = authorized_client.get(f"/machines/{machine.id}")
    assert still_there.status_code == 200


def test_delete_missing_machine_is_404_not_403(second_client):
    response = second_client.delete("/machines/999")
    assert response.status_code == 404


def test_other_user_cannot_delete_reading(second_client, test_readings):
    reading = test_readings[0]
    response = second_client.delete(f"/readings/{reading.id}")
    assert response.status_code == 403


# --- /machines/mine scoping -------------------------------------------------

def test_mine_returns_only_own_machines(authorized_client, test_machines):
    response = authorized_client.get("/machines/mine")
    assert response.status_code == 200
    assert len(response.json()) == len(test_machines)


def test_mine_is_empty_for_other_user(second_client, test_machines):
    """test_machines belong to test_user, so second_user sees none."""
    response = second_client.get("/machines/mine")
    assert response.status_code == 200
    assert response.json() == []


def test_mine_requires_a_token(client):
    response = client.get("/machines/mine")
    assert response.status_code == 401



