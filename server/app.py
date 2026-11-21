"""Magnet server: Erik uploads photos, the device fetches ready frames."""
import hashlib
import hmac
import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from starlette.middleware.sessions import SessionMiddleware

import notify
from imaging import render_frame

MAX_UPLOAD_BYTES = 15 * 1024 * 1024
LOW_BATTERY_MV = 3500
FRAME_BYTES = 172_800
STATIC_DIR = Path(__file__).parent / "static"


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


def create_app() -> FastAPI:
    device_token = os.environ["DEVICE_TOKEN"]
    password_hash = os.environ["UPLOAD_PASSWORD_HASH"]
    data_dir = Path(os.environ.get("DATA_DIR", "data"))
    frames_dir = data_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
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
                cursor INTEGER NOT NULL DEFAULT 0,
                last_seen REAL,
                battery_mv INTEGER,
                low_streak INTEGER NOT NULL DEFAULT 0,
                alerted INTEGER NOT NULL DEFAULT 0
            );
            INSERT OR IGNORE INTO state (id) VALUES (1);
            """
        )

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

    @app.post("/api/photos", dependencies=[Depends(require_login)])
    def upload(file: UploadFile = File(...)) -> dict:
        data = file.file.read(MAX_UPLOAD_BYTES + 1)
        if len(data) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="file larger than 15 MB")
        try:
            frame = render_frame(data)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"unsupported image: {exc}")
        with db() as conn:
            cur = conn.execute("INSERT INTO photos (created_at) VALUES (?)", (time.time(),))
            photo_id = cur.lastrowid
        (frames_dir / f"{photo_id}.bin").write_bytes(frame)
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
        (frames_dir / f"{photo_id}.bin").unlink(missing_ok=True)
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
            cursor = conn.execute("SELECT cursor FROM state WHERE id = 1").fetchone()["cursor"]
            row = conn.execute(
                "SELECT id FROM photos WHERE id > ? ORDER BY id LIMIT 1", (cursor,)
            ).fetchone() or conn.execute("SELECT id FROM photos ORDER BY id LIMIT 1").fetchone()
            if row is not None:
                conn.execute("UPDATE state SET cursor = ? WHERE id = 1", (row["id"],))
        if alert_mv is not None:
            notify.notify_low_battery(alert_mv)
        if row is None:
            return Response(status_code=204)
        frame = (frames_dir / f"{row['id']}.bin").read_bytes()
        if len(frame) != FRAME_BYTES:
            return JSONResponse({"detail": "stored frame is corrupt"}, status_code=500)
        return Response(frame, media_type="application/octet-stream",
                        headers={"X-Photo-Id": str(row["id"])})

    return app
