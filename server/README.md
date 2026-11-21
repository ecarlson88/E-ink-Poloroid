# Magnet server

Erik uploads photos; the magnet fetches ready-to-draw frames. Uploads are kept
as originals under `DATA_DIR/originals`; when the palette or nibble order in
`imaging.py` changes, every frame is re-rendered from its original at the next
start.

## Run with Docker and a Cloudflare Tunnel (recommended)

The app listens on `127.0.0.1:8000` on the server only. A Cloudflare Tunnel
publishes it over HTTPS without opening router ports.

1. From the repo root: `cp .env.example .env` and fill it in (leave
   `TUNNEL_TOKEN` empty). To make the password hash, build first and run:
   `docker compose run --rm --no-deps magnet python -c "from app import hash_password; print(hash_password('your password'))"`
   then paste it into `.env` with every `$` written as `$$`.
2. Point the `cloudflared` already installed on the server at the app. Which
   way depends on how that tunnel is managed:
   - **Managed in the Cloudflare dashboard** (installed with a `--token`
     command): Zero Trust > Networks > Tunnels > your tunnel > Public
     Hostname > Add, for example `magnet.yourdomain.com`, service type
     `HTTP`, URL `localhost:8000`. Nothing to restart.
   - **Managed by a config file** (usually `/etc/cloudflared/config.yml` or
     `~/.cloudflared/config.yml`): add a rule above the final catch-all, then
     `cloudflared tunnel route dns <tunnel-name> magnet.yourdomain.com` and
     restart cloudflared (`sudo systemctl restart cloudflared`):

         ingress:
           - hostname: magnet.yourdomain.com
             service: http://localhost:8000
           # ...your existing rules...
           - service: http_status:404

   (No cloudflared on the server? Put a tunnel token in `.env` as
   `TUNNEL_TOKEN`, use `magnet:8000` as the service URL, and start with
   `docker compose --profile tunnel up -d --build` instead.)
3. `docker compose up -d --build`
4. In Cloudflare, for the domain: SSL/TLS > Edge Certificates > turn on
   **Always Use HTTPS** (plain HTTP then redirects). Make sure **Bot Fight
   Mode** (Security > Bots) is off, or add a WAF skip rule for the path
   `/api/device/`: otherwise Cloudflare may answer the magnet with a browser
   challenge page instead of the photo, and the magnet keeps its old photo.
5. Check from outside: `curl -i https://magnet.yourdomain.com/api/device/next`
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
