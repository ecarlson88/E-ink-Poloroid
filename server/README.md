# Magnet server

Erik uploads photos; the magnet fetches ready-to-draw frames. Uploads are kept
as originals under `DATA_DIR/originals`; when the palette or nibble order in
`imaging.py` changes, every frame is re-rendered from its original at the next
start.

## Run with Docker and a Cloudflare Tunnel (recommended)

The tunnel makes an outbound connection to Cloudflare, so no router ports
are opened, and Cloudflare provides the HTTPS certificate.

1. In the Cloudflare dashboard: Zero Trust > Networks > Tunnels > Create a
   tunnel (type Cloudflared). Copy the token from the Docker install command
   (the long value after `--token`); you do not need to run that command.
2. In the tunnel, add a public hostname, for example `magnet.yourdomain.com`,
   with service type `HTTP` and URL `magnet:8000` (the compose service name).
3. From the repo root: `cp .env.example .env` and fill it in, including
   `TUNNEL_TOKEN`. To make the password hash, build first and run:
   `docker compose run --rm --no-deps magnet python -c "from app import hash_password; print(hash_password('your password'))"`
   then paste it into `.env` with every `$` written as `$$`.
4. `docker compose up -d --build`
5. In Cloudflare, for the domain: SSL/TLS > Edge Certificates > turn on
   **Always Use HTTPS** (plain HTTP then redirects). Make sure **Bot Fight
   Mode** (Security > Bots) is off, or add a WAF skip rule for the path
   `/api/device/`: otherwise Cloudflare may answer the magnet with a browser
   challenge page instead of the photo, and the magnet keeps its old photo.
6. Check from outside: `curl -i https://magnet.yourdomain.com/api/device/next`
   gives `401`; with `-H "Authorization: Bearer <DEVICE_TOKEN>"` it gives `200`
   and `curl -s ... | wc -c` prints `172800` (once a photo is uploaded). Put
   the same URL in the firmware's `secrets.h` as `SERVER_URL`.

The app is also reachable at `http://127.0.0.1:8000` on the server itself, for
local checks (log in only works over HTTPS, so use the tunnel address for that).

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
