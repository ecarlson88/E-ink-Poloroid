import io
import json

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


def test_device_next_alternates_two_photos(logged_in):
    a = _upload(logged_in, (255, 0, 0)).json()["id"]
    b = _upload(logged_in, (0, 0, 255)).json()["id"]
    ids = []
    for _ in range(4):
        r = _next(logged_in)
        assert r.status_code == 200
        assert len(r.content) == FRAME_BYTES
        ids.append(int(r.headers["X-Photo-Id"]))
    assert set(ids) == {a, b}
    assert all(x != y for x, y in zip(ids, ids[1:]))


def test_upload_requires_login(client):
    assert _upload(client).status_code == 401
    assert client.get("/api/photos").status_code == 401
    assert client.delete("/api/photos/1").status_code == 401


def test_login_wrong_password(client):
    assert client.post("/login", data={"password": "nope"}).status_code == 401


def test_upload_rejects_non_image(logged_in):
    r = logged_in.post("/api/photos", files={"file": ("p.jpg", b"hello", "image/jpeg")})
    assert r.status_code == 400
    assert r.json()["detail"] == "not a photo the server can read (use JPEG, PNG or WebP)"
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


# --- Shuffle rotation, "show next", status and images (Erik's page features) ---

def _ids(c, n):
    return [int(_next(c).headers["X-Photo-Id"]) for _ in range(n)]


def test_each_photo_once_per_round(logged_in):
    ids = {_upload(logged_in).json()["id"] for _ in range(5)}
    assert set(_ids(logged_in, 5)) == ids
    assert set(_ids(logged_in, 5)) == ids


def test_never_same_photo_twice_in_a_row(logged_in):
    for _ in range(3):
        _upload(logged_in)
    seen = _ids(logged_in, 60)
    assert all(x != y for x, y in zip(seen, seen[1:]))


def test_rounds_are_shuffled(logged_in):
    for _ in range(6):
        _upload(logged_in)
    rounds = {tuple(_ids(logged_in, 6)) for _ in range(10)}
    assert len(rounds) > 1


def test_new_upload_shows_in_current_round(logged_in):
    for _ in range(4):
        _upload(logged_in)
    _ids(logged_in, 1)
    new = _upload(logged_in).json()["id"]
    assert new in _ids(logged_in, 4)


def test_deleted_photo_never_shown(logged_in):
    a, b, c = (_upload(logged_in).json()["id"] for _ in range(3))
    logged_in.delete(f"/api/photos/{b}")
    assert b not in _ids(logged_in, 9)


def test_show_next_overrides_shuffle(logged_in):
    ids = [_upload(logged_in).json()["id"] for _ in range(4)]
    _ids(logged_in, 1)
    for pick in ids:
        assert logged_in.post(f"/api/photos/{pick}/next").status_code == 200
        assert _ids(logged_in, 1) == [pick]


def test_show_next_requires_login_and_photo(client, logged_in):
    pid = _upload(logged_in).json()["id"]
    assert logged_in.post("/api/photos/999/next").status_code == 404
    client.cookies.clear()
    assert client.post(f"/api/photos/{pid}/next").status_code == 401


def test_status_reports_magnet(logged_in):
    for _ in range(3):
        _upload(logged_in)
    empty = logged_in.get("/api/status").json()
    assert empty["last_seen"] is None and empty["battery_mv"] is None
    shown = int(_next(logged_in, bat_mv=3900).headers["X-Photo-Id"])
    st = logged_in.get("/api/status").json()
    assert st["battery_mv"] == 3900
    assert st["battery_low"] is False
    assert st["last_seen"] is not None
    assert st["current_id"] == shown
    assert _ids(logged_in, 1) == [st["next_id"]]


def test_status_requires_login(client):
    assert client.get("/api/status").status_code == 401


def test_photo_images(logged_in):
    pid = _upload(logged_in, (200, 30, 30)).json()["id"]          # a 600 x 400 photo
    r = logged_in.get(f"/api/photos/{pid}/image?view=original")   # the whole photo, for the crop editor
    assert r.status_code == 200 and r.headers["content-type"] == "image/jpeg"
    assert Image.open(io.BytesIO(r.content)).size == (600, 400)
    r = logged_in.get(f"/api/photos/{pid}/image?view=photo")      # the 3:4 crop in true color
    assert r.status_code == 200 and r.headers["content-type"] == "image/jpeg"
    assert Image.open(io.BytesIO(r.content)).size == (480, 640)
    r = logged_in.get(f"/api/photos/{pid}/image?view=panel")      # the picture as the magnet draws it
    assert r.status_code == 200 and r.headers["content-type"] == "image/png"
    img = Image.open(io.BytesIO(r.content)).convert("RGB")
    assert img.size == (480, 640)
    import imaging
    assert {c for _, c in img.getcolors(10)} <= set(imaging.PALETTE.values())


def test_photo_images_require_login_and_photo(client, logged_in):
    pid = _upload(logged_in).json()["id"]
    assert logged_in.get("/api/photos/999/image?view=original").status_code == 404
    assert logged_in.get(f"/api/photos/{pid}/image?view=other").status_code == 422
    client.cookies.clear()
    assert client.get(f"/api/photos/{pid}/image?view=original").status_code == 401


def test_logout_ends_session(logged_in):
    assert logged_in.get("/api/photos").status_code == 200
    assert logged_in.post("/logout").status_code == 200
    assert logged_in.get("/api/photos").status_code == 401


# --- Movable 3:4 crop (Erik) ----------------------------------------------------------------

def _halves_png(w=1200, h=600):
    img = Image.new("RGB", (w, h), (255, 0, 0))
    img.paste(Image.new("RGB", (w // 2, h), (0, 0, 255)), (w // 2, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


CROP_W = 600 * 0.75 / 1200
LEFT = {"x": 0.0, "y": 0.0, "w": CROP_W, "h": 1.0}
RIGHT = {"x": 1 - CROP_W, "y": 0.0, "w": CROP_W, "h": 1.0}


def test_upload_lists_size_and_default_crop(logged_in):
    pid = logged_in.post("/api/photos", files={"file": ("h.png", _halves_png(), "image/png")}).json()["id"]
    (p,) = [p for p in logged_in.get("/api/photos").json() if p["id"] == pid]
    assert (p["width"], p["height"]) == (1200, 600)
    assert abs(p["crop"]["x"] + p["crop"]["w"] / 2 - 0.5) < 1e-6 and p["crop"]["h"] == 1


def test_upload_with_crop(logged_in):
    import imaging
    r = logged_in.post("/api/photos", files={"file": ("h.png", _halves_png(), "image/png")},
                       data={"crop": json.dumps(LEFT)})
    assert r.status_code == 200
    pid = r.json()["id"]
    assert logged_in.get("/api/photos").json()[0]["crop"]["x"] == 0
    assert _next(logged_in).content == imaging.render_frame(_halves_png(), LEFT)
    assert pid


def test_upload_rejects_bad_crop(logged_in):
    bad = {"x": 0.9, "y": 0, "w": CROP_W, "h": 1}
    r = logged_in.post("/api/photos", files={"file": ("h.png", _halves_png(), "image/png")},
                       data={"crop": json.dumps(bad)})
    assert r.status_code == 400
    assert logged_in.get("/api/photos").json() == []
    r = logged_in.post("/api/photos", files={"file": ("h.png", _halves_png(), "image/png")}, data={"crop": "nope"})
    assert r.status_code == 400


def test_change_crop_rerenders_frame(logged_in):
    import imaging
    pid = logged_in.post("/api/photos", files={"file": ("h.png", _halves_png(), "image/png")},
                         data={"crop": json.dumps(LEFT)}).json()["id"]
    assert logged_in.put(f"/api/photos/{pid}/crop", json=RIGHT).status_code == 200
    assert logged_in.get("/api/photos").json()[0]["crop"]["x"] == RIGHT["x"]
    assert _next(logged_in).content == imaging.render_frame(_halves_png(), RIGHT)


def test_change_crop_checks(client, logged_in):
    pid = logged_in.post("/api/photos", files={"file": ("h.png", _halves_png(), "image/png")}).json()["id"]
    assert logged_in.put("/api/photos/999/crop", json=LEFT).status_code == 404
    assert logged_in.put(f"/api/photos/{pid}/crop", json={"x": 0, "y": 0, "w": 0.5, "h": 1}).status_code == 400
    client.cookies.clear()
    assert client.put(f"/api/photos/{pid}/crop", json=LEFT).status_code == 401


def test_rerender_keeps_each_crop(logged_in, monkeypatch):
    import imaging
    logged_in.post("/api/photos", files={"file": ("h.png", _halves_png(), "image/png")}, data={"crop": json.dumps(RIGHT)})
    monkeypatch.setattr(imaging, "PICTURE_ROWS_FIRST", not imaging.PICTURE_ROWS_FIRST)
    with TestClient(create_app(), base_url="https://testserver") as c2:   # restart: settings changed
        assert _next(c2).content == imaging.render_frame(_halves_png(), RIGHT)
