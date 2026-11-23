# Magnet server

Erik uploads photos; the magnet fetches ready-to-draw frames. Uploads are kept
as originals under `DATA_DIR/originals`; when the palette, nibble order or picture
placement in `imaging.py` changes, every frame is re-rendered from its original
(with its crop) at the next start.

**3:4 picture with a movable crop.** The case masks the panel's ribbon end, so each
photo fills a 480 x 640 (3:4) picture at the other end of the frame and the last
80 rows stay white. `PICTURE_ROWS_FIRST` in `imaging.py` says which end; it's an
assumption until the bench test (Task 1 Step 4). The upload page opens a crop
editor for each photo (drag the 3:4 box, zoom slider, or "upload the rest
centred"), and each photo's **Crop** button moves it later. API:
`POST /api/photos` takes an optional `crop` form field (JSON `{x, y, w, h}`,
fractions of the upright photo, 3:4); `PUT /api/photos/{id}/crop` with the same
JSON re-renders that photo; `GET /api/photos` lists `width`, `height` and `crop`;
`GET /api/photos/{id}/image?view=original|photo|panel` gives the whole photo, the
3:4 crop, or the picture as the magnet draws it.

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
   gives `401`. To check a real frame, add a magnet on the page (you get a
   pairing code), pair it by hand with
   `curl -s -H "Content-Type: application/json" -d '{"code":"ABCD-2345"}' https://magnet.yourdomain.com/api/device/pair`,
   put a photo on it, then `curl -s -H "Authorization: Bearer <token>" https://magnet.yourdomain.com/api/device/next | wc -c`
   prints `172800`. Put `https://magnet.yourdomain.com` in the firmware's
   `secrets.h` as `SERVER_URL`.

The app is also reachable at `http://127.0.0.1:8000` on the server itself, for
local checks (log in only works over HTTPS, so use the tunnel address for that).

Data lives in the Docker volume `magnet-data`. Back it up with:
`docker compose cp magnet:/data ./magnet-backup`

Update after a `git pull`: `docker compose up -d --build`.

## Run without Docker

    UPLOAD_PASSWORD_HASH=... SESSION_SECRET=... DATA_DIR=/var/lib/magnet \
    LOW_BATTERY_WEBHOOK_URL=https://... uvicorn app:create_app --factory --host 127.0.0.1 --port 8000

Make a password hash: `python -c "from app import hash_password; print(hash_password('your password'))"`

## Tests

    pip install fastapi uvicorn pillow httpx python-multipart itsdangerous pytest
    pytest

## Magnets and pairing

One photo library, any number of magnets. Uploads go to the library only; on the page,
pick a magnet and choose which library photos it shows. Each magnet has its own shuffle,
status (last check-in, battery, what it shows) and low-battery alert.

Adding a magnet: **+ Add magnet** on the page, give it a name, and you get a pairing
code like `ABCD-2345` (works once, for 24 hours). On the magnet's Wi-Fi setup page,
type the code along with the Wi-Fi details. The magnet trades the code for its own
key and keeps it; the server stores only a hash of keys and codes. **New pairing code**
gives a magnet a fresh code (its old key keeps working until the new code is used);
**Remove magnet** cuts it off.

`DEVICE_TOKEN` (optional) is for a magnet keyed before pairing existed: on first
start with it set and no magnets yet, the server creates "My magnet" with that key,
carries over its status and puts every photo on it.

## Device contract

- `POST /api/device/pair` with JSON `{"code": "ABCD-2345"}` (case, spaces and the dash
  don't matter) returns `{"token": "...", "name": "..."}`; `401` if the code is unknown,
  used or expired.
- `GET /api/device/next?bat_mv=<int>` with `Authorization: Bearer <token>` returns a
  172,800-byte frame with header `X-Photo-Id` (204 when the magnet has no photos, 401 on
  a bad token).

Page API (session cookie): `GET/POST /api/photos`, `DELETE /api/photos/{id}`,
`PUT /api/photos/{id}/crop`, `GET /api/photos/{id}/image?view=original|photo|panel`;
`GET/POST /api/devices`, `PATCH/DELETE /api/devices/{id}`,
`POST /api/devices/{id}/pair-code`, `PUT/DELETE /api/devices/{id}/photos/{photo_id}`,
`POST /api/devices/{id}/photos/{photo_id}/next`.
