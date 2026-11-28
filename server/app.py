"""Magnet server: Erik uploads photos, the device fetches ready frames."""
import hashlib
import hmac
import io
import json
import logging
import os
import random
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from typing import Literal

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from starlette.middleware.sessions import SessionMiddleware

import imaging
import notify
from imaging import render_frame

MAX_UPLOAD_BYTES = 15 * 1024 * 1024
LOW_BATTERY_MV = 3500
FRAME_BYTES = 172_800
# Failed logins allowed per client address in LOGIN_WINDOW_S before /login answers 429.
LOGIN_MAX_FAILURES = 5
LOGIN_WINDOW_S = 15 * 60
STATIC_DIR = Path(__file__).parent / "static"
log = logging.getLogger(__name__)
_rng = random.SystemRandom()


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt if salt is not None else os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        scheme, salt_hex, digest_hex = stored.split("$")
        if scheme != "scrypt":
            return False
        digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1)
    except ValueError:
        return False
    return hmac.compare_digest(digest.hex(), digest_hex)


def _write_atomic(path: Path, data: bytes) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


PAIR_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"   # no 0/O, 1/I/L: easy to type on a phone
PAIR_CODE_LEN = 8
PAIR_CODE_TTL = 24 * 3600
MAX_NAME = 60
FIRST_MAGNET_NAME = "My magnet"


def _hash(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def _normalize_code(code: str) -> str:
    return "".join(ch for ch in str(code).upper() if ch.isalnum())


def _new_pair_code() -> str:
    raw = "".join(_rng.choice(PAIR_ALPHABET) for _ in range(PAIR_CODE_LEN))
    return f"{raw[:4]}-{raw[4:]}"


def _clean_name(body: dict) -> str:
    name = str(body.get("name", "")).strip() if isinstance(body, dict) else ""
    if not name or len(name) > MAX_NAME:
        raise HTTPException(status_code=400, detail=f"give the magnet a name of 1 to {MAX_NAME} characters")
    return name


# --- Each magnet's shuffle: its own queue over the photos selected for it -------------------

def _selected(conn: sqlite3.Connection, device_id: int) -> list[int]:
    return [r["photo_id"] for r in conn.execute(
        "SELECT dp.photo_id FROM device_photos dp JOIN photos p ON p.id = dp.photo_id "
        "WHERE dp.device_id = ? ORDER BY dp.photo_id", (device_id,))]


def _load_queue(conn: sqlite3.Connection, device_id: int) -> list[int]:
    return json.loads(conn.execute("SELECT queue FROM devices WHERE id = ?", (device_id,)).fetchone()["queue"])


def _save_queue(conn: sqlite3.Connection, device_id: int, queue: list[int]) -> None:
    conn.execute("UPDATE devices SET queue = ? WHERE id = ?", (json.dumps(queue), device_id))


def _valid_queue(conn: sqlite3.Connection, device_id: int) -> list[int]:
    """The saved queue without photos since deleted or taken off this magnet."""
    ids = set(_selected(conn, device_id))
    return [i for i in _load_queue(conn, device_id) if i in ids]


def _new_round(ids: list[int], avoid_first: int | None) -> list[int]:
    """A fresh shuffle of every photo that does not start with avoid_first."""
    order = list(ids)
    _rng.shuffle(order)
    if len(order) > 1 and order[0] == avoid_first:
        swap = _rng.randrange(1, len(order))
        order[0], order[swap] = order[swap], order[0]
    return order


def _pick_next(conn: sqlite3.Connection, device_id: int) -> int | None:
    """Take the head of this magnet's shuffle and make it its current photo. The queue
    is refilled right away, so the page can always say what comes next."""
    queue = _valid_queue(conn, device_id)
    if not queue:
        current = conn.execute("SELECT current_id FROM devices WHERE id = ?", (device_id,)).fetchone()["current_id"]
        queue = _new_round(_selected(conn, device_id), current)
    if not queue:
        return None
    photo_id, queue = queue[0], queue[1:]
    if not queue:
        queue = _new_round(_selected(conn, device_id), photo_id)
    _save_queue(conn, device_id, queue)
    conn.execute("UPDATE devices SET current_id = ? WHERE id = ?", (photo_id, device_id))
    return photo_id


def create_app() -> FastAPI:
    legacy_token = os.environ.get("DEVICE_TOKEN")   # the first magnet's key, from before pairing existed
    password_hash = os.environ["UPLOAD_PASSWORD_HASH"]
    data_dir = Path(os.environ.get("DATA_DIR", "data"))
    frames_dir = data_dir / "frames"
    originals_dir = data_dir / "originals"
    frames_dir.mkdir(parents=True, exist_ok=True)
    originals_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "magnet.db"

    @contextmanager
    def db():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            with conn:  # commit on success, roll back on error
                yield conn
        finally:
            conn.close()

    with db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at REAL NOT NULL,
                width INTEGER,
                height INTEGER,
                crop TEXT
            );
            CREATE TABLE IF NOT EXISTS state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                queue TEXT NOT NULL DEFAULT '[]',
                current_id INTEGER,
                last_seen REAL,
                battery_mv INTEGER,
                low_streak INTEGER NOT NULL DEFAULT 0,
                alerted INTEGER NOT NULL DEFAULT 0,
                render_key TEXT
            );
            INSERT OR IGNORE INTO state (id) VALUES (1);
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at REAL NOT NULL,
                token_hash TEXT UNIQUE,
                pair_code_hash TEXT,
                pair_expires REAL,
                queue TEXT NOT NULL DEFAULT '[]',
                current_id INTEGER,
                last_seen REAL,
                battery_mv INTEGER,
                low_streak INTEGER NOT NULL DEFAULT 0,
                alerted INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS device_photos (
                device_id INTEGER NOT NULL,
                photo_id INTEGER NOT NULL,
                PRIMARY KEY (device_id, photo_id)
            );
            """
        )
        # Databases made before crops existed: add the columns.
        have = {r["name"] for r in conn.execute("PRAGMA table_info(photos)")}
        for col, kind in (("width", "INTEGER"), ("height", "INTEGER"), ("crop", "TEXT")):
            if col not in have:
                conn.execute(f"ALTER TABLE photos ADD COLUMN {col} {kind}")
        if "first_magnet_made" not in {r["name"] for r in conn.execute("PRAGMA table_info(state)")}:
            conn.execute("ALTER TABLE state ADD COLUMN first_magnet_made INTEGER NOT NULL DEFAULT 0")
        # Before pairing existed there was one magnet, keyed by DEVICE_TOKEN, showing every photo.
        # Make it the first magnet once, with its photos, shuffle and status, so nothing re-pairs.
        st = conn.execute("SELECT * FROM state WHERE id = 1").fetchone()
        no_devices = conn.execute("SELECT COUNT(*) FROM devices").fetchone()[0] == 0
        if legacy_token and no_devices and not st["first_magnet_made"]:
            cur = conn.execute(
                "INSERT INTO devices (name, created_at, token_hash, queue, current_id, last_seen, battery_mv,"
                " low_streak, alerted) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (FIRST_MAGNET_NAME, time.time(), _hash(legacy_token), st["queue"], st["current_id"],
                 st["last_seen"], st["battery_mv"], st["low_streak"], st["alerted"]))
            conn.execute("INSERT INTO device_photos (device_id, photo_id) SELECT ?, id FROM photos", (cur.lastrowid,))
            conn.execute("UPDATE state SET first_magnet_made = 1 WHERE id = 1")

    rerender_if_settings_changed(db, frames_dir, originals_dir)

    app = FastAPI()
    app.add_middleware(
        SessionMiddleware,
        secret_key=os.environ["SESSION_SECRET"],
        https_only=True,
        same_site="strict",
        max_age=60 * 60 * 24 * 30,
    )

    app.state.login_clock = time.monotonic     # tests swap in a fake clock
    login_failures: dict[str, list[float]] = {}  # client address -> times of recent failures

    def client_address(request: Request) -> str:
        """Behind the Cloudflare Tunnel every request comes from cloudflared, so the visitor is
        in CF-Connecting-IP. Safe to trust: the port is bound to 127.0.0.1 (docker-compose.yml)."""
        cf = request.headers.get("CF-Connecting-IP", "").strip()
        return cf or (request.client.host if request.client else "unknown")

    def recent_failures(addr: str, now: float) -> list[float]:
        times = [t for t in login_failures.get(addr, []) if now - t < LOGIN_WINDOW_S]
        if times:
            login_failures[addr] = times
        else:
            login_failures.pop(addr, None)
        return times

    def require_login(request: Request) -> None:
        if not request.session.get("auth"):
            raise HTTPException(status_code=401, detail="login required")

    def require_device(request: Request) -> sqlite3.Row:
        """The magnet making the request, found by its key (stored only as a hash)."""
        header = request.headers.get("Authorization", "")
        scheme, _, token = header.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise HTTPException(status_code=401, detail="bad device token")
        with db() as conn:
            row = conn.execute("SELECT id, name FROM devices WHERE token_hash = ?", (_hash(token),)).fetchone()
        if row is None:
            raise HTTPException(status_code=401, detail="bad device token")
        return row

    def device_or_404(conn: sqlite3.Connection, device_id: int) -> sqlite3.Row:
        row = conn.execute("SELECT * FROM devices WHERE id = ?", (device_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="no such magnet")
        return row

    def photo_or_404(conn: sqlite3.Connection, photo_id: int) -> None:
        if conn.execute("SELECT 1 FROM photos WHERE id = ?", (photo_id,)).fetchone() is None:
            raise HTTPException(status_code=404, detail="no such photo")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html", media_type="text/html")

    @app.post("/login")
    def login(request: Request, password: str = Form(...)) -> dict:
        addr, now = client_address(request), app.state.login_clock()
        times = recent_failures(addr, now)
        if len(times) >= LOGIN_MAX_FAILURES:
            wait = int(times[0] + LOGIN_WINDOW_S - now) + 1
            raise HTTPException(status_code=429, detail=f"too many tries; wait {wait // 60 + 1} minutes",
                                headers={"Retry-After": str(wait)})
        if not _verify_password(password, password_hash):
            login_failures.setdefault(addr, []).append(now)
            raise HTTPException(status_code=401, detail="wrong password")
        login_failures.pop(addr, None)
        request.session["auth"] = True
        return {"ok": True}

    @app.post("/logout")
    def logout(request: Request) -> dict:
        request.session.clear()
        return {"ok": True}

    @app.post("/api/photos", dependencies=[Depends(require_login)])
    def upload(file: UploadFile = File(...), crop: str | None = Form(None)) -> dict:
        data = file.file.read(MAX_UPLOAD_BYTES + 1)
        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="file larger than 15 MB")
        try:
            w, h = imaging.photo_size(data)
            if crop is None:
                chosen = imaging.default_crop(w, h)
            else:
                try:
                    chosen = imaging.validate_crop(json.loads(crop), w, h)
                except json.JSONDecodeError as exc:
                    raise ValueError("the crop is not valid JSON") from exc
            frame = render_frame(data, chosen)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        with db() as conn:  # the row is committed only if both files were written
            cur = conn.execute("INSERT INTO photos (created_at, width, height, crop) VALUES (?, ?, ?, ?)",
                               (time.time(), w, h, json.dumps(chosen)))
            photo_id = cur.lastrowid
            original, frame_path = originals_dir / str(photo_id), frames_dir / f"{photo_id}.bin"
            try:
                _write_atomic(original, data)
                _write_atomic(frame_path, frame)
            except OSError:
                original.unlink(missing_ok=True)
                frame_path.unlink(missing_ok=True)
                raise
        return {"id": photo_id}   # in the library only: choose its magnets on the page

    @app.get("/api/photos", dependencies=[Depends(require_login)])
    def list_photos() -> list[dict]:
        with db() as conn:
            rows = conn.execute("SELECT id, created_at, width, height, crop FROM photos ORDER BY id").fetchall()
        return [{"id": r["id"], "created_at": r["created_at"], "width": r["width"], "height": r["height"],
                 "crop": json.loads(r["crop"]) if r["crop"] else None} for r in rows]

    @app.put("/api/photos/{photo_id}/crop", dependencies=[Depends(require_login)])
    def change_crop(photo_id: int, crop: dict) -> dict:
        """Move a photo's 3:4 crop (fractions of the upright photo) and re-render its frame."""
        original = originals_dir / str(photo_id)
        with db() as conn:
            row = conn.execute("SELECT width, height FROM photos WHERE id = ?", (photo_id,)).fetchone()
        if row is None or not original.exists():
            raise HTTPException(status_code=404, detail="no such photo")
        data = original.read_bytes()
        w, h = (row["width"], row["height"]) if row["width"] else imaging.photo_size(data)
        try:
            chosen = imaging.validate_crop(crop, w, h)
            frame = render_frame(data, chosen)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        _write_atomic(frames_dir / f"{photo_id}.bin", frame)
        with db() as conn:
            conn.execute("UPDATE photos SET crop = ?, width = ?, height = ? WHERE id = ?",
                         (json.dumps(chosen), w, h, photo_id))
        return {"ok": True}

    @app.delete("/api/photos/{photo_id}", dependencies=[Depends(require_login)])
    def delete_photo(photo_id: int) -> dict:
        with db() as conn:
            conn.execute("DELETE FROM photos WHERE id = ?", (photo_id,))
            conn.execute("DELETE FROM device_photos WHERE photo_id = ?", (photo_id,))
            conn.execute("UPDATE devices SET current_id = NULL WHERE current_id = ?", (photo_id,))
        (frames_dir / f"{photo_id}.bin").unlink(missing_ok=True)
        (originals_dir / str(photo_id)).unlink(missing_ok=True)
        return {"ok": True}

    def record_battery(conn: sqlite3.Connection, device_id: int, bat_mv: int) -> int | None:
        """Update this magnet's low-battery streak; return mV to alert about, if any."""
        st = conn.execute("SELECT low_streak, alerted FROM devices WHERE id = ?", (device_id,)).fetchone()
        if bat_mv < LOW_BATTERY_MV:
            streak = st["low_streak"] + 1
            alert = streak >= 2 and not st["alerted"]
            conn.execute("UPDATE devices SET low_streak = ?, alerted = ? WHERE id = ?",
                         (streak, 1 if (alert or st["alerted"]) else 0, device_id))
            return bat_mv if alert else None
        conn.execute("UPDATE devices SET low_streak = 0, alerted = 0 WHERE id = ?", (device_id,))
        return None

    @app.get("/api/device/next")
    def device_next(bat_mv: int | None = None, device: sqlite3.Row = Depends(require_device)) -> Response:
        alert_mv = None
        with db() as conn:
            conn.execute("UPDATE devices SET last_seen = ? WHERE id = ?", (time.time(), device["id"]))
            if bat_mv is not None:
                conn.execute("UPDATE devices SET battery_mv = ? WHERE id = ?", (bat_mv, device["id"]))
                alert_mv = record_battery(conn, device["id"], bat_mv)
            photo_id = _pick_next(conn, device["id"])
        if alert_mv is not None:
            notify.notify_low_battery(alert_mv, magnet=device["name"])
        if photo_id is None:
            return Response(status_code=204)
        frame = (frames_dir / f"{photo_id}.bin").read_bytes()
        if len(frame) != FRAME_BYTES:
            return JSONResponse({"detail": "stored frame is corrupt"}, status_code=500)
        return Response(frame, media_type="application/octet-stream",
                        headers={"X-Photo-Id": str(photo_id), "Cache-Control": "no-store"})

    @app.post("/api/device/pair")
    def device_pair(body: dict) -> dict:
        """A magnet trades the one-time pairing code (typed into its setup page) for its own
        long-term key. The code works once and expires after PAIR_CODE_TTL."""
        code = _normalize_code(body.get("code", "")) if isinstance(body, dict) else ""
        token = secrets.token_urlsafe(32)
        with db() as conn:
            row = conn.execute("SELECT id, name, pair_expires FROM devices WHERE pair_code_hash = ?",
                               (_hash(code),)).fetchone() if code else None
            if row is None or row["pair_expires"] is None or row["pair_expires"] < time.time():
                raise HTTPException(status_code=401, detail="unknown or expired pairing code")
            conn.execute("UPDATE devices SET token_hash = ?, pair_code_hash = NULL, pair_expires = NULL WHERE id = ?",
                         (_hash(token), row["id"]))
        return {"token": token, "name": row["name"]}

    # --- Magnets on the page --------------------------------------------------------------

    def describe(conn: sqlite3.Connection, d: sqlite3.Row) -> dict:
        queue = _valid_queue(conn, d["id"])
        bat = d["battery_mv"]
        pending = d["pair_code_hash"] is not None and d["pair_expires"] and d["pair_expires"] > time.time()
        return {
            "id": d["id"], "name": d["name"], "paired": d["token_hash"] is not None,
            "pairing_expires": d["pair_expires"] if pending else None,
            "last_seen": d["last_seen"], "battery_mv": bat,
            "battery_low": bat is not None and bat < LOW_BATTERY_MV,
            "current_id": d["current_id"], "next_id": queue[0] if queue else None,
            "photo_ids": _selected(conn, d["id"]),
        }

    def set_pair_code(conn: sqlite3.Connection, device_id: int) -> dict:
        code, expires = _new_pair_code(), time.time() + PAIR_CODE_TTL
        conn.execute("UPDATE devices SET pair_code_hash = ?, pair_expires = ? WHERE id = ?",
                     (_hash(_normalize_code(code)), expires, device_id))
        return {"pair_code": code, "pair_expires": expires}

    @app.get("/api/devices", dependencies=[Depends(require_login)])
    def list_devices() -> list[dict]:
        with db() as conn:
            return [describe(conn, d) for d in conn.execute("SELECT * FROM devices ORDER BY id").fetchall()]

    @app.post("/api/devices", dependencies=[Depends(require_login)])
    def add_device(body: dict) -> dict:
        """Add a magnet; returns its pairing code (shown once: only a hash is kept)."""
        name = _clean_name(body)
        with db() as conn:
            device_id = conn.execute("INSERT INTO devices (name, created_at) VALUES (?, ?)",
                                     (name, time.time())).lastrowid
            return {"id": device_id, "name": name, **set_pair_code(conn, device_id)}

    @app.patch("/api/devices/{device_id}", dependencies=[Depends(require_login)])
    def rename_device(device_id: int, body: dict) -> dict:
        name = _clean_name(body)
        with db() as conn:
            device_or_404(conn, device_id)
            conn.execute("UPDATE devices SET name = ? WHERE id = ?", (name, device_id))
        return {"ok": True}

    @app.delete("/api/devices/{device_id}", dependencies=[Depends(require_login)])
    def remove_device(device_id: int) -> dict:
        """Remove a magnet: its key stops working at once. The photos stay in the library."""
        with db() as conn:
            device_or_404(conn, device_id)
            conn.execute("DELETE FROM devices WHERE id = ?", (device_id,))
            conn.execute("DELETE FROM device_photos WHERE device_id = ?", (device_id,))
        return {"ok": True}

    @app.post("/api/devices/{device_id}/pair-code", dependencies=[Depends(require_login)])
    def new_pair_code(device_id: int) -> dict:
        """A new pairing code (a replacement magnet, or a lost code). The magnet's current key
        keeps working until the new code is used, then it is replaced."""
        with db() as conn:
            device_or_404(conn, device_id)
            return set_pair_code(conn, device_id)

    @app.put("/api/devices/{device_id}/photos/{photo_id}", dependencies=[Depends(require_login)])
    def select_photo(device_id: int, photo_id: int) -> dict:
        """Put a library photo on a magnet; it joins that magnet's current round."""
        with db() as conn:
            device_or_404(conn, device_id)
            photo_or_404(conn, photo_id)
            added = conn.execute("INSERT OR IGNORE INTO device_photos (device_id, photo_id) VALUES (?, ?)",
                                 (device_id, photo_id)).rowcount
            if added:
                queue = _valid_queue(conn, device_id)
                queue.insert(_rng.randint(0, len(queue)), photo_id)
                _save_queue(conn, device_id, queue)
        return {"ok": True}

    @app.delete("/api/devices/{device_id}/photos/{photo_id}", dependencies=[Depends(require_login)])
    def unselect_photo(device_id: int, photo_id: int) -> dict:
        with db() as conn:
            device_or_404(conn, device_id)
            conn.execute("DELETE FROM device_photos WHERE device_id = ? AND photo_id = ?", (device_id, photo_id))
        return {"ok": True}

    @app.post("/api/devices/{device_id}/photos/{photo_id}/next", dependencies=[Depends(require_login)])
    def show_next(device_id: int, photo_id: int) -> dict:
        """Make this photo the magnet's next one."""
        with db() as conn:
            device_or_404(conn, device_id)
            photo_or_404(conn, photo_id)
            if photo_id not in _selected(conn, device_id):
                raise HTTPException(status_code=409, detail="that photo is not on this magnet")
            _save_queue(conn, device_id, [photo_id] + [i for i in _valid_queue(conn, device_id) if i != photo_id])
        return {"ok": True}

    @app.get("/api/photos/{photo_id}/image", dependencies=[Depends(require_login)])
    def photo_image(photo_id: int, view: Literal["original", "photo", "panel"]) -> Response:
        """original: the whole upright photo (for the crop editor); photo: the 3:4 crop in true
        color; panel: the picture as the magnet draws it."""
        frame_path = frames_dir / f"{photo_id}.bin"
        with db() as conn:
            row = conn.execute("SELECT crop FROM photos WHERE id = ?", (photo_id,)).fetchone()
        if row is None or not frame_path.exists():
            raise HTTPException(status_code=404, detail="no such photo")
        buf = io.BytesIO()
        original = originals_dir / str(photo_id)
        if view == "original" and original.exists():
            imaging.preview_original(original.read_bytes()).save(buf, format="JPEG", quality=85)
            media = "image/jpeg"
        elif view == "photo" and original.exists():
            crop = json.loads(row["crop"]) if row["crop"] else None
            imaging.picture_image(original.read_bytes(), crop).save(buf, format="JPEG", quality=85)
            media = "image/jpeg"
        else:  # the panel view, also the fallback for photos stored before originals were kept
            imaging.frame_picture(frame_path.read_bytes()).save(buf, format="PNG")
            media = "image/png"
        return Response(buf.getvalue(), media_type=media,
                        headers={"Cache-Control": "private, max-age=3600"})

    return app


def rerender_if_settings_changed(db, frames_dir: Path, originals_dir: Path) -> None:
    """Re-render every stored frame from its original when the palette, nibble
    order or render version changed since the frames were made."""
    key = imaging.render_key()
    with db() as conn:
        stored = conn.execute("SELECT render_key FROM state WHERE id = 1").fetchone()["render_key"]
        if stored == key:
            return
        rows = conn.execute("SELECT id, crop FROM photos ORDER BY id").fetchall()
    ids = [r["id"] for r in rows]
    crops = {r["id"]: json.loads(r["crop"]) if r["crop"] else None for r in rows}
    for photo_id in ids:
        original = originals_dir / str(photo_id)
        if not original.exists():
            log.warning("photo %s has no original; keeping its old frame", photo_id)
            continue
        try:
            frame = render_frame(original.read_bytes(), crops[photo_id])
        except ValueError:
            log.exception("photo %s could not be re-rendered; keeping its old frame", photo_id)
            continue
        _write_atomic(frames_dir / f"{photo_id}.bin", frame)
    log.info("re-rendered %d photo(s) for new render settings", len(ids))
    with db() as conn:
        conn.execute("UPDATE state SET render_key = ? WHERE id = 1", (key,))
