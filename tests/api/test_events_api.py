import pytest

VALID_EVENT = {
    "source": "webhook",
    "service": "payment-service",
    "error_code": 503,
    "error_message": "Upstream timeout after 30s",
    "payload": {"endpoint": "/charge"},
    "metadata": {"environment": "test"},
}


@pytest.mark.asyncio
async def test_post_ingest_happy_path(client):
    response = await client.post("/api/v1/events/ingest", json=VALID_EVENT)

    assert response.status_code == 202

    data = response.json()
    assert "event_id" in data
    assert data["status"] == "processing"
    assert data["message"] == "Event accepted. Crew triage started asynchronously."


@pytest.mark.asyncio
async def test_post_ingest_missing_fields_returns_422(client):
    response = await client.post(
        "/api/v1/events/ingest",
        json={
            "source": "webhook",
            "service": "",
            "error_message": "",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_events_list(client):
    await client.post("/api/v1/events/ingest", json=VALID_EVENT)

    response = await client.get("/api/v1/events")

    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    assert data["limit"] == 20
    assert data["offset"] == 0
    assert len(data["items"]) == 1
    assert data["items"][0]["service"] == "payment-service"
    assert data["items"][0]["source"] == "webhook"


@pytest.mark.asyncio
async def test_get_event_by_id(client):
    create_response = await client.post("/api/v1/events/ingest", json=VALID_EVENT)
    event_id = create_response.json()["event_id"]

    response = await client.get(f"/api/v1/events/{event_id}")

    assert response.status_code == 200

    data = response.json()
    assert data["event_id"] == event_id
    assert data["service"] == "payment-service"
    assert data["source"] == "webhook"
    assert data["error_code"] == 503


@pytest.mark.asyncio
async def test_get_event_by_id_not_found(client):
    response = await client.get("/api/v1/events/not-a-real-id")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_event(client):
    create_response = await client.post("/api/v1/events/ingest", json=VALID_EVENT)
    event_id = create_response.json()["event_id"]

    delete_response = await client.delete(f"/api/v1/events/{event_id}")

    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/v1/events/{event_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_event_not_found(client):
    response = await client.delete("/api/v1/events/not-a-real-id")

    assert response.status_code == 404
