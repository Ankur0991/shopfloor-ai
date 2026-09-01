from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import config, models, database, main
import pytest
from datetime import timedelta, datetime, timezone
from fastapi.testclient import TestClient

engine = create_engine(config.settings.test_database_url)
test_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def login(client, email, password):
    response = client.post("/login", data={"username": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"] 


@pytest.fixture
def db():
    """Fresh, empty tables for every test."""
    database.Base.metadata.drop_all(bind=engine)
    database.Base.metadata.create_all(bind=engine)
    session = test_session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    main.app.dependency_overrides[database.get_db] = override_get_db
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


@pytest.fixture
def test_user(client):
    user_data = {"email" : "testuser@xyz.com", "password" : "password123", "full_name" :"Test User",}
    response = client.post("/users/", json = user_data)
    assert response.status_code == 201, response.text
    created = response.json()
    created["password"] = user_data["password"]
    return created


@pytest.fixture
def token(client, test_user):
    return login(client=client, email= test_user["email"], password= test_user["password"])


@pytest.fixture
def authorized_client(client, token):
    new_client = TestClient(main.app)
    new_client.headers = {**new_client.headers, "Authorization": f"Bearer {token}"}
    return new_client


@pytest.fixture
def second_user(client):
    another_user = {"email" : "seconduser@xyz.com", "password" : "qwertz123", "full_name" : "Second Test User"}
    response = client.post("/users/", json = another_user)
    assert response.status_code == 201, response.text
    created_user = response.json()
    created_user["password"] = another_user["password"]
    return created_user


@pytest.fixture
def second_client(client, second_user):
    token = login(client=client, email=second_user["email"], password= second_user["password"])
    new_client = TestClient(main.app)
    new_client.headers = {**new_client.headers, "Authorization": f"Bearer {token}"}
    return new_client


@pytest.fixture
def test_machines(db, test_user):
    machines = [
        models.Machine(name="Symphoni-Test-01", line="Line A",
                       location="Hall 1", created_by=test_user["id"]),
        models.Machine(name="Symphoni-Test-02", line="Line A",
                       location="Hall 1", created_by=test_user["id"]),
        models.Machine(name="Palletiser-Test", line="Line B",
                       location="Hall 2", created_by=test_user["id"]),
                ]
    db.add_all(machines)
    db.commit()
    for machine in machines:
        db.refresh(machine)
    return machines

@pytest.fixture
def test_readings(db, test_machines, test_user):
    now = datetime.now(timezone.utc)

    # (machine, metric, unit, how many rows to create)
    spec = [
        (test_machines[0], "vibration_rms", "mm/s", 5),
        (test_machines[0], "spindle_temp",  "C",    3),
        (test_machines[1], "air_pressure",  "bar",  4),
        # test_machines[2] deliberately gets none
    ]

    readings = []
    hours_ago = 0

    for machine, metric, unit, how_many in spec:
        for i in range(how_many):
            readings.append(
                models.SensorReading(
                    machine_id=machine.id,
                    metric=metric,
                    value=1.0 + i,
                    unit=unit,
                    recorded_at=now - timedelta(hours=hours_ago),
                    created_by=test_user["id"],
                )
            )
            hours_ago += 1
    db.add_all(readings)
    db.commit()
    return readings