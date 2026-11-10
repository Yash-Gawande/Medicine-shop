async def test_liveness(client):
    r = await client.get("/api/v1/health/live")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
    assert r.headers["x-request-id"]
    assert r.headers["x-content-type-options"] == "nosniff"


async def test_readiness_checks_db_and_redis(client):
    r = await client.get("/api/v1/health/ready")
    assert r.status_code == 200, r.text
    assert r.json()["checks"] == {"database": "ok", "redis": "ok"}


async def test_unknown_route_uses_error_envelope(client):
    r = await client.get("/api/v1/does-not-exist")
    assert r.status_code == 404
    body = r.json()["error"]
    assert body["code"] == "http_404"
    assert body["request_id"]
