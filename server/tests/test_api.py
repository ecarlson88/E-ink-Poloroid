import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

import notify
from app import create_app, hash_password

TOKEN = "device-secret"
PASSWORD = "correct horse"
FRAME_BYTES = 172_800


@pytest.fixture
def alerts(monkeypatch):
    sent = []
    monkeypatch.setattr(notify, "notify_low_battery", lambda mv: sent.append(mv))
    return sent


@pytest.fixture
def client(tmp_path, monkeypatch, alerts):
    monkeypatch.setenv("DEVICE_TOKEN", TOKEN)
    monkeypatch.setenv("UPLOAD_PASSWORD_HASH", hash_password(PASSWORD))
    monkeypatch.setenv("SESSION_SECRET", "test-secret")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.delenv("LOW_BATTERY_WEBHOOK_URL", raising=False)
    with TestClient(create_app(), base_url="https://testserver") as c:
        yield c


@pytest.fixture
def logged_in(client):
    r = client.post("/login", data={"password": PASSWORD})
    assert r.status_code == 200
    return client


def _photo(color) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (600, 400), color).save(buf, format="JPEG")
    return buf.getvalue()


def _upload(c, color=(255, 0, 0)):
    return c.post("/api/photos", files={"file": ("p.jpg", _photo(color), "image/jpeg")})


def _next(c, token=TOKEN, bat_mv=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    params = {"bat_mv": bat_mv} if bat_mv is not None else {}
    return c.get("/api/device/next", headers=headers, params=params)


def test_device_next_requires_token(client):
    assert _next(client, token=None).status_code == 401
    assert _next(client, token="wrong").status_code == 401


def test_device_next_204_when_empty(client):
    assert _next(client).status_code == 204


def test_device_next_rotates_and_wraps(logged_in):
    a = _upload(logged_in, (255, 0, 0)).json()["id"]
    b = _upload(logged_in, (0, 0, 255)).json()["id"]
    ids = []
    for _ in range(3):
        r = _next(logged_in)
        assert r.status_code == 200
        assert len(r.content) == FRAME_BYTES
        ids.append(int(r.headers["X-Photo-Id"]))
    assert ids == [a, b, a]


def test_upload_requires_login(client):
    assert _upload(client).status_code == 401
    assert client.get("/api/photos").status_code == 401
    assert client.delete("/api/photos/1").status_code == 401


def test_login_wrong_password(client):
    assert client.post("/login", data={"password": "nope"}).status_code == 401


def test_upload_rejects_non_image(logged_in):
    r = logged_in.post("/api/photos", files={"file": ("p.jpg", b"hello", "image/jpeg")})
    assert r.status_code == 400
    assert logged_in.get("/api/photos").json() == []


def test_upload_rejects_over_15mb(logged_in):
    big = b"\0" * (15 * 1024 * 1024 + 1)
    r = logged_in.post("/api/photos", files={"file": ("p.jpg", big, "image/jpeg")})
    assert r.status_code == 413
    assert logged_in.get("/api/photos").json() == []


def test_delete_removes_photo(logged_in):
    pid = _upload(logged_in).json()["id"]
    assert logged_in.delete(f"/api/photos/{pid}").status_code == 200
    assert logged_in.get("/api/photos").json() == []
    assert _next(logged_in).status_code == 204


def test_low_battery_alerts_after_two_low_reports(logged_in, alerts):
    _upload(logged_in)
    _next(logged_in, bat_mv=3400)
    assert alerts == []
    _next(logged_in, bat_mv=3400)
    assert alerts == [3400]
    _next(logged_in, bat_mv=3390)
    assert alerts == [3400]  # still low: no repeat alert
    _next(logged_in, bat_mv=3900)
    _next(logged_in, bat_mv=3450)
    _next(logged_in, bat_mv=3440)
    assert alerts == [3400, 3440]


def test_index_page_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def _stripes() -> bytes:
    """A 480x720 PNG of 1-px vertical black/white stripes: its frame changes
    if the nibble order flips."""
    img = Image.new("RGB", (480, 720), (255, 255, 255))
    for x in range(0, 480, 2):
        for y in range(720):
            img.putpixel((x, y), (0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_upload_keeps_original(logged_in, tmp_path):
    data = _photo((0, 0, 255))
    pid = logged_in.post("/api/photos", files={"file": ("p.jpg", data, "image/jpeg")}).json()["id"]
    assert (tmp_path / "originals" / str(pid)).read_bytes() == data


def test_delete_removes_original(logged_in, tmp_path):
    pid = _upload(logged_in).json()["id"]
    assert (tmp_path / "originals" / str(pid)).exists()
    logged_in.delete(f"/api/photos/{pid}")
    assert not (tmp_path / "originals" / str(pid)).exists()
    assert not (tmp_path / "frames" / f"{pid}.bin").exists()


def test_frames_rerendered_when_render_settings_change(logged_in, tmp_path, monkeypatch):
    import imaging

    logged_in.post("/api/photos", files={"file": ("s.png", _stripes(), "image/png")})
    before = _next(logged_in).content

    monkeypatch.setattr(imaging, "HIGH_NIBBLE_IS_LEFT", not imaging.HIGH_NIBBLE_IS_LEFT)
    with TestClient(create_app(), base_url="https://testserver") as c2:  # restart
        after = _next(c2).content

    assert after != before
    assert after == imaging.render_frame(_stripes())


def test_frames_not_rerendered_when_settings_unchanged(logged_in, tmp_path):
    pid = _upload(logged_in).json()["id"]
    frame = tmp_path / "frames" / f"{pid}.bin"
    frame.write_bytes(b"\x11" * FRAME_BYTES)  # marker: would be overwritten by a re-render
    with TestClient(create_app(), base_url="https://testserver"):
        pass
    assert frame.read_bytes() == b"\x11" * FRAME_BYTES
