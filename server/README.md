# Magnet server

Erik uploads photos; the magnet fetches ready-to-draw frames. Uploads are kept
as originals under `DATA_DIR/originals`; when the palette or nibble order in
`imaging.py` changes, every frame is re-rendered from its original at the next
start.

## Run with Docker (recommended)

From the repo root:

1. `cp .env.example .env` and fill it in (see the comments in it). To make the
   password hash, build first and run:
   `docker compose run --rm magnet python -c "from app import hash_password; print(hash_password('your password'))"`
   then paste it into `.env` with every `$` written as `$$`.
2. `docker compose up -d --build`
3. The app listens on `127.0.0.1:8000` on the host only. Put an HTTPS reverse
   proxy in front of it (the login cookie only works over HTTPS).
4. Check from outside: `curl -i https://<host>/api/device/next` gives `401`;
   with `-H "Authorization: Bearer <DEVICE_TOKEN>"` it gives `200` and
   `curl -s ... | wc -c` prints `172800` (once a photo is uploaded).

Data lives in the Docker volume `magnet-data`. Back it up with:
`docker compose cp magnet:/data ./magnet-backup`

Update after a `git pull`: `docker compose up -d --build`.

## Run without Docker

    DEVICE_TOKEN=... UPLOAD_PASSWORD_HASH=... SESSION_SECRET=... DATA_DIR=/var/lib/magnet \
    LOW_BATTERY_WEBHOOK_URL=https://... uvicorn app:create_app --factory --host 127.0.0.1 --port 8000

Make a password hash: `python -c "from app import hash_password; print(hash_password('your password'))"`

## Tests

    pip install fastapi uvicorn pillow httpx python-multipart itsdangerous pytest
    pytest

## Device contract

`GET /api/device/next?bat_mv=<int>` with `Authorization: Bearer <DEVICE_TOKEN>`
returns a 172,800-byte frame (204 when no photos, 401 on a bad token).
