"""Magnet server: Erik uploads photos, the device fetches ready frames."""
import hashlib
import hmac
import io
import json
import logging
import os
import random
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
from imaging import frame_to_image, render_frame

MAX_UPLOAD_BYTES = 15 * 1024 * 1024
LOW_BATTERY_MV = 3500
FRAME_BYTES = 172_800
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


def _load_queue(conn: sqlite3.Connection) -> list[int]:
    return json.loads(conn.execute("SELECT queue FROM state WHERE id = 1").fetchone()["queue"])


def _save_queue(conn: sqlite3.Connection, queue: list[int]) -> None:
    conn.execute("UPDATE state SET queue = ? WHERE id = 1", (json.dumps(queue),))


def _valid_queue(conn: sqlite3.Connection) -> list[int]:
    """The saved queue without photos that have since been deleted."""
    ids = {r["id"] for r in conn.execute("SELECT id FROM photos")}
    return [i for i in _load_queue(conn) if i in ids]


def _new_round(ids: list[int], avoid_first: int | None) -> list[int]:
    """A fresh shuffle of every photo that does not start with avoid_first."""
    order = list(ids)
    _rng.shuffle(order)
    if len(order) > 1 and order[0] == avoid_first:
        swap = _rng.randrange(1, len(order))
        order[0], order[swap] = order[swap], order[0]
    return order


def _pick_next(conn: sqlite3.Connection) -> int | None:
    """Take the head of the shuffle queue and make it the current photo. The
    queue is refilled right away, so status can always say what comes next."""
    queue = _valid_queue(conn)
    if not queue:
        ids = [r["id"] for r in conn.execute("SELECT id FROM photos")]
        current = conn.execute("SELECT current_id FROM state WHERE id = 1").fetchone()["current_id"]
        queue = _new_round(ids, current)
    if not queue:
        return None
    photo_id, queue = queue[0], queue[1:]
    if not queue:
        ids = [r["id"] for r in conn.execute("SELECT id FROM photos")]
        queue = _new_round(ids, photo_id)
    _save_queue(conn, queue)
    conn.execute("UPDATE state SET current_id = ? WHERE id = 1", (photo_id,))
    return photo_id


def create_app() -> FastAPI:
    device_token = os.environ["DEVICE_TOKEN"]
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
                created_at REAL NOT NULL
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
            """
        )

    rerender_if_settings_changed(db, frames_dir, originals_dir)

    app = FastAPI()
    app.add_middleware(
        SessionMiddleware,
        secret_key=os.environ["SESSION_SECRET"],
        https_only=True,
        same_site="strict",
        max_age=60 * 60 * 24 * 30,
    )

    def require_login(request: Request) -> None:
        if not request.session.get("auth"):
            raise HTTPException(status_code=401, detail="login required")

    def require_device(request: Request) -> None:
        header = request.headers.get("Authorization", "")
        scheme, _, token = header.partition(" ")
        if scheme.lower() != "bearer" or not hmac.compare_digest(token, device_token):
            raise HTTPException(status_code=401, detail="bad device token")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html", media_type="text/html")

    @app.post("/login")
    def login(request: Request, password: str = Form(...)) -> dict:
        if not _verify_password(password, password_hash):
            raise HTTPException(status_code=401, detail="wrong password")
        request.session["auth"] = True
        return {"ok": True}

    @app.post("/logout")
    def logout(request: Request) -> dict:
        request.session.clear()
        return {"ok": True}

    @app.post("/api/photos", dependencies=[Depends(require_login)])
    def upload(file: UploadFile = File(...)) -> dict:
        data = file.file.read(MAX_UPLOAD_BYTES + 1)
        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="file larger than 15 MB")
        try:
            frame = render_frame(data)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        with db() as conn:  # the row is committed only if both files were written
            cur = conn.execute("INSERT INTO photos (created_at) VALUES (?)", (time.time(),))
            photo_id = cur.lastrowid
            original, frame_path = originals_dir / str(photo_id), frames_dir / f"{photo_id}.bin"
            try:
                _write_atomic(original, data)
                _write_atomic(frame_path, frame)
            except OSError:
                original.unlink(missing_ok=True)
                frame_path.unlink(missing_ok=True)
                raise
            queue = _load_queue(conn)
            queue.insert(_rng.randint(0, len(queue)), photo_id)
            _save_queue(conn, queue)
        return {"id": photo_id}

    @app.get("/api/photos", dependencies=[Depends(require_login)])
    def list_photos() -> list[dict]:
        with db() as conn:
            rows = conn.execute("SELECT id, created_at FROM photos ORDER BY id").fetchall()
        return [{"id": r["id"], "created_at": r["created_at"]} for r in rows]

    @app.delete("/api/photos/{photo_id}", dependencies=[Depends(require_login)])
    def delete_photo(photo_id: int) -> dict:
        with db() as conn:
            conn.execute("DELETE FROM photos WHERE id = ?", (photo_id,))
            _save_queue(conn, [i for i in _load_queue(conn) if i != photo_id])
            conn.execute("UPDATE state SET current_id = NULL WHERE id = 1 AND current_id = ?",
                         (photo_id,))
        (frames_dir / f"{photo_id}.bin").unlink(missing_ok=True)
        (originals_dir / str(photo_id)).unlink(missing_ok=True)
        return {"ok": True}

    def record_battery(conn: sqlite3.Connection, bat_mv: int) -> int | None:
        """Update the low-battery streak; return mV to alert about, if any."""
        state = conn.execute("SELECT low_streak, alerted FROM state WHERE id = 1").fetchone()
        if bat_mv < LOW_BATTERY_MV:
            streak = state["low_streak"] + 1
            alert = streak >= 2 and not state["alerted"]
            conn.execute(
                "UPDATE state SET low_streak = ?, alerted = ? WHERE id = 1",
                (streak, 1 if (alert or state["alerted"]) else 0),
            )
            return bat_mv if alert else None
        conn.execute("UPDATE state SET low_streak = 0, alerted = 0 WHERE id = 1")
        return None

    @app.get("/api/device/next", dependencies=[Depends(require_device)])
    def device_next(bat_mv: int | None = None) -> Response:
        alert_mv = None
        with db() as conn:
            conn.execute("UPDATE state SET last_seen = ? WHERE id = 1", (time.time(),))
            if bat_mv is not None:
                conn.execute("UPDATE state SET battery_mv = ? WHERE id = 1", (bat_mv,))
                alert_mv = record_battery(conn, bat_mv)
            photo_id = _pick_next(conn)
        if alert_mv is not None:
            notify.notify_low_battery(alert_mv)
        if photo_id is None:
            return Response(status_code=204)
        frame = (frames_dir / f"{photo_id}.bin").read_bytes()
        if len(frame) != FRAME_BYTES:
            return JSONResponse({"detail": "stored frame is corrupt"}, status_code=500)
        return Response(frame, media_type="application/octet-stream",
                        headers={"X-Photo-Id": str(photo_id), "Cache-Control": "no-store"})

    @app.post("/api/photos/{photo_id}/next", dependencies=[Depends(require_login)])
    def show_next(photo_id: int) -> dict:
        with db() as conn:
            if conn.execute("SELECT 1 FROM photos WHERE id = ?", (photo_id,)).fetchone() is None:
                raise HTTPException(status_code=404, detail="no such photo")
            _save_queue(conn, [photo_id] + [i for i in _load_queue(conn) if i != photo_id])
        return {"ok": True}

    @app.get("/api/status", dependencies=[Depends(require_login)])
    def status() -> dict:
        with db() as conn:
            st = conn.execute(
                "SELECT last_seen, battery_mv, current_id FROM state WHERE id = 1").fetchone()
            queue = _valid_queue(conn)
        bat = st["battery_mv"]
        return {
            "last_seen": st["last_seen"],
            "battery_mv": bat,
            "battery_low": bat is not None and bat < LOW_BATTERY_MV,
            "current_id": st["current_id"],
            "next_id": queue[0] if queue else None,
        }

    @app.get("/api/photos/{photo_id}/image", dependencies=[Depends(require_login)])
    def photo_image(photo_id: int, view: Literal["original", "panel"]) -> Response:
        frame_path = frames_dir / f"{photo_id}.bin"
        with db() as conn:
            exists = conn.execute("SELECT 1 FROM photos WHERE id = ?", (photo_id,)).fetchone()
        if exists is None or not frame_path.exists():
            raise HTTPException(status_code=404, detail="no such photo")
        buf = io.BytesIO()
        original = originals_dir / str(photo_id)
        if view == "original" and original.exists():
            imaging.preview_original(original.read_bytes()).save(buf, format="JPEG", quality=85)
            media = "image/jpeg"
        else:  # the panel view, also the fallback for photos stored before originals were kept
            frame_to_image(frame_path.read_bytes()).save(buf, format="PNG")
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
        ids = [r["id"] for r in conn.execute("SELECT id FROM photos ORDER BY id")]
    for photo_id in ids:
        original = originals_dir / str(photo_id)
        if not original.exists():
            log.warning("photo %s has no original; keeping its old frame", photo_id)
            continue
        try:
            frame = render_frame(original.read_bytes())
        except ValueError:
            log.exception("photo %s could not be re-rendered; keeping its old frame", photo_id)
            continue
        _write_atomic(frames_dir / f"{photo_id}.bin", frame)
    log.info("re-rendered %d photo(s) for new render settings", len(ids))
    with db() as conn:
        conn.execute("UPDATE state SET render_key = ? WHERE id = 1", (key,))
