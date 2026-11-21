# Magnet server

Run behind a TLS reverse proxy (the session cookie is HTTPS-only):

    DEVICE_TOKEN=... UPLOAD_PASSWORD_HASH=... SESSION_SECRET=... DATA_DIR=/var/lib/magnet \
    LOW_BATTERY_WEBHOOK_URL=https://... uvicorn app:create_app --factory --host 127.0.0.1 --port 8000

Uploads are kept as originals under `DATA_DIR/originals`; when the palette or nibble order in `imaging.py` changes, every frame is re-rendered from its original at the next start.

Make a password hash: `python -c "from app import hash_password; print(hash_password('your password'))"`

Device contract: `GET /api/device/next?bat_mv=<int>` with `Authorization: Bearer <DEVICE_TOKEN>`
returns a 172,800-byte frame (204 when no photos, 401 on a bad token).
