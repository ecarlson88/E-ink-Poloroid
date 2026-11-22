// Demo stand-in for the magnet server: the real upload page runs unchanged on top of it.
// Photos live in memory; crops and the magnet preview are made on a canvas, the same way the
// server does it (3:4 picture, 480 x 640, dithered to the panel's six colours).
(() => {
  const PALETTE = [[0, 0, 0], [255, 255, 255], [255, 255, 0], [255, 0, 0], [0, 0, 255], [0, 255, 0]];
  const PW = 480, PH = 640, RATIO = 3 / 4, LOW_MV = 3500;
  const state = { auth: false, photos: [], queue: [], current: null, lastSeen: null, battery: null, nextId: 1 };

  const json = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
  const detail = (msg, status) => json({ detail: msg }, status);
  const byId = (id) => state.photos.find((p) => p.id === id);
  const shuffle = (a) => { for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };

  function defaultCrop(w, h) {
    if (w / h > RATIO) { const cw = RATIO * h / w; return { x: (1 - cw) / 2, y: 0, w: cw, h: 1 }; }
    const ch = w / (RATIO * h); return { x: 0, y: (1 - ch) / 2, w: 1, h: ch };
  }
  function validCrop(c, w, h) {
    if (!c || !["x", "y", "w", "h"].every((k) => typeof c[k] === "number" && isFinite(c[k]))) return "a crop needs numbers x, y, w and h";
    const e = 1e-6;
    if (c.w <= 0 || c.h <= 0 || c.x < -e || c.y < -e || c.x + c.w > 1 + e || c.y + c.h > 1 + e) return "the crop must lie inside the photo";
    if (Math.abs((c.w * w) / (c.h * h) / RATIO - 1) > 0.02) return "the crop must be 3:4";
    return null;
  }

  function loadImage(blob) {
    return new Promise((resolve, reject) => {
      const url = URL.createObjectURL(blob);
      const img = new Image();
      img.onload = () => resolve({ img, url });
      img.onerror = () => { URL.revokeObjectURL(url); reject(new Error("unreadable")); };
      img.src = url;
    });
  }
  const toURL = (canvas, type, q) => new Promise((r) => canvas.toBlob((b) => r(URL.createObjectURL(b)), type, q));

  function pictureCanvas(img, c) {
    const cv = document.createElement("canvas"); cv.width = PW; cv.height = PH;
    const g = cv.getContext("2d");
    g.imageSmoothingQuality = "high";
    const W = img.naturalWidth, H = img.naturalHeight;
    g.drawImage(img, c.x * W, c.y * H, c.w * W, c.h * H, 0, 0, PW, PH);
    return cv;
  }
  function dither(src) {   // Floyd-Steinberg to the panel palette, as the server does
    const cv = document.createElement("canvas"); cv.width = PW; cv.height = PH;
    const g = cv.getContext("2d"), d = src.getContext("2d").getImageData(0, 0, PW, PH);
    const p = new Float32Array(d.data.length);
    for (let i = 0; i < p.length; i++) p[i] = d.data[i];
    for (let y = 0; y < PH; y++) for (let x = 0; x < PW; x++) {
      const i = (y * PW + x) * 4;
      let best = 0, bd = Infinity;
      for (let k = 0; k < 6; k++) {
        const dr = p[i] - PALETTE[k][0], dg = p[i + 1] - PALETTE[k][1], db = p[i + 2] - PALETTE[k][2];
        const dd = dr * dr + dg * dg + db * db; if (dd < bd) { bd = dd; best = k; }
      }
      const c = PALETTE[best];
      for (let ch = 0; ch < 3; ch++) {
        const err = p[i + ch] - c[ch]; d.data[i + ch] = c[ch];
        if (x + 1 < PW) p[i + 4 + ch] += err * 7 / 16;
        if (y + 1 < PH) {
          if (x > 0) p[i + PW * 4 - 4 + ch] += err * 3 / 16;
          p[i + PW * 4 + ch] += err * 5 / 16;
          if (x + 1 < PW) p[i + PW * 4 + 4 + ch] += err / 16;
        }
      }
      d.data[i + 3] = 255;
    }
    g.putImageData(d, 0, 0);
    return cv;
  }
  async function renderViews(p) {
    for (const k of ["photo", "panel"]) if (p.urls[k]) URL.revokeObjectURL(p.urls[k]);
    const pic = pictureCanvas(p.img, p.crop);
    p.urls.photo = await toURL(pic, "image/jpeg", 0.88);
    p.urls.panel = await toURL(dither(pic), "image/png");
  }

  async function addPhoto(blob, crop, createdAt) {
    let loaded;
    try { loaded = await loadImage(blob); } catch { return detail("not a photo the server can read (use JPEG, PNG or WebP)", 400); }
    const W = loaded.img.naturalWidth, H = loaded.img.naturalHeight;
    const c = crop || defaultCrop(W, H);
    const bad = validCrop(c, W, H);
    if (bad) { URL.revokeObjectURL(loaded.url); return detail(bad, 400); }
    const p = { id: state.nextId++, created_at: createdAt || Date.now() / 1000, width: W, height: H, crop: c, img: loaded.img, urls: { original: loaded.url } };
    await renderViews(p);
    state.photos.push(p);
    state.queue.splice(Math.floor(Math.random() * (state.queue.length + 1)), 0, p.id);
    return json({ id: p.id });
  }

  function validQueue() { return state.queue.filter((id) => byId(id)); }
  function pickNext() {   // what the magnet's daily wake does: take the head of the shuffle
    let q = validQueue();
    if (!q.length) q = shuffle(state.photos.map((p) => p.id));
    if (!q.length) return null;
    const id = q.shift();
    if (!q.length) { q = shuffle(state.photos.map((p) => p.id)); if (q.length > 1 && q[0] === id) [q[0], q[1]] = [q[1], q[0]]; }
    state.queue = q; state.current = id;
    return id;
  }

  const realFetch = window.fetch.bind(window);
  window.fetch = async (input, opts = {}) => {
    const url = typeof input === "string" ? input : input.url;
    if (!url.startsWith("/")) return realFetch(input, opts);
    if (window.__demo) await window.__demo.ready;
    const method = (opts.method || "GET").toUpperCase();
    const path = url.split("?")[0];
    if (path === "/login" && method === "POST") {
      const pw = opts.body && opts.body.get ? opts.body.get("password") : "";
      if (!pw) return detail("wrong password", 401);
      state.auth = true; return json({ ok: true });
    }
    if (path === "/logout") { state.auth = false; return json({ ok: true }); }
    if (!state.auth) return detail("login required", 401);
    let m;
    if (path === "/api/photos" && method === "GET") {
      return json(state.photos.map(({ id, created_at, width, height, crop }) => ({ id, created_at, width, height, crop })));
    }
    if (path === "/api/photos" && method === "POST") {
      const file = opts.body.get("file"), crop = opts.body.get("crop");
      if (file.size > 15 * 1024 * 1024) return detail("file larger than 15 MB", 413);
      let c = null;
      if (crop) { try { c = JSON.parse(crop); } catch { return detail("the crop is not valid JSON", 400); } }
      return addPhoto(file, c);
    }
    if (path === "/api/status") {
      const q = validQueue();
      return json({ last_seen: state.lastSeen, battery_mv: state.battery, battery_low: state.battery != null && state.battery < LOW_MV,
                    current_id: state.current, next_id: q.length ? q[0] : null });
    }
    if ((m = path.match(/^\/api\/photos\/(\d+)$/)) && method === "DELETE") {
      const id = +m[1], p = byId(id);
      if (p) { Object.values(p.urls).forEach((u) => URL.revokeObjectURL(u)); state.photos = state.photos.filter((x) => x.id !== id); }
      state.queue = state.queue.filter((x) => x !== id);
      if (state.current === id) state.current = null;
      return json({ ok: true });
    }
    if ((m = path.match(/^\/api\/photos\/(\d+)\/next$/))) {
      const id = +m[1]; if (!byId(id)) return detail("no such photo", 404);
      state.queue = [id, ...state.queue.filter((x) => x !== id)]; return json({ ok: true });
    }
    if ((m = path.match(/^\/api\/photos\/(\d+)\/crop$/)) && method === "PUT") {
      const p = byId(+m[1]); if (!p) return detail("no such photo", 404);
      const c = JSON.parse(opts.body), bad = validCrop(c, p.width, p.height);
      if (bad) return detail(bad, 400);
      p.crop = c; await renderViews(p); return json({ ok: true });
    }
    return detail("not found", 404);
  };

  // The page shows photos with <img src="/api/photos/{id}/image?view=...">: point those at the demo's images.
  const srcDesc = Object.getOwnPropertyDescriptor(HTMLImageElement.prototype, "src");
  Object.defineProperty(HTMLImageElement.prototype, "src", {
    configurable: true,
    get() { return srcDesc.get.call(this); },
    set(v) {
      const mm = /\/api\/photos\/(\d+)\/image\?view=(\w+)/.exec(v);
      if (mm) { const p = byId(+mm[1]); v = p ? p.urls[mm[2]] || p.urls.photo : ""; }
      srcDesc.set.call(this, v);
    },
  });

  // --- Sample photos: generated scenes in different shapes, so cropping has something to do.
  function scene(w, h, draw) {
    const cv = document.createElement("canvas"); cv.width = w; cv.height = h;
    draw(cv.getContext("2d"), w, h);
    return new Promise((r) => cv.toBlob(r, "image/jpeg", 0.9));
  }
  const sky = (g, w, h, top, bottom) => { const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, top); gr.addColorStop(1, bottom); g.fillStyle = gr; g.fillRect(0, 0, w, h); };
  const hills = (g, w, h, y, color, amp, phase) => {
    g.fillStyle = color; g.beginPath(); g.moveTo(0, h);
    for (let x = 0; x <= w; x += 8) g.lineTo(x, y + Math.sin(x / w * 6 + phase) * amp + Math.sin(x / w * 17 + phase * 2) * amp * 0.3);
    g.lineTo(w, h); g.closePath(); g.fill();
  };
  const samples = [
    [1600, 1200, (g, w, h) => {   // sunset over hills (landscape 4:3)
      sky(g, w, h, "#2E4A7D", "#F2A65A");
      g.fillStyle = "#FFD27A"; g.beginPath(); g.arc(w * 0.68, h * 0.52, h * 0.11, 0, 7); g.fill();
      hills(g, w, h, h * 0.62, "#5B4A6B", h * 0.05, 0.4); hills(g, w, h, h * 0.75, "#3B3350", h * 0.04, 2); hills(g, w, h, h * 0.88, "#231E33", h * 0.03, 4);
    }],
    [1080, 1440, (g, w, h) => {   // lake and pines (portrait 3:4)
      sky(g, w, h * 0.55, "#8EC5E8", "#DDEFF7");
      hills(g, w, h, h * 0.5, "#5E7F96", h * 0.04, 1.2);
      g.fillStyle = "#3D6B8C"; g.fillRect(0, h * 0.58, w, h * 0.42);
      for (let i = 0; i < 9; i++) { const x = i * w / 8, s = 60 + (i % 3) * 30; g.fillStyle = "#24452F"; g.beginPath(); g.moveTo(x, h * 0.6 - s * 2.4); g.lineTo(x - s, h * 0.6); g.lineTo(x + s, h * 0.6); g.fill(); }
      g.fillStyle = "rgba(255,255,255,.25)"; for (let i = 0; i < 40; i++) g.fillRect(Math.random() * w, h * 0.62 + Math.random() * h * 0.36, 40 + Math.random() * 80, 3);
    }],
    [1500, 1500, (g, w, h) => {   // beach (square)
      sky(g, w, h * 0.5, "#4FA3D9", "#BFE3F5");
      g.fillStyle = "#1E7FA8"; g.fillRect(0, h * 0.5, w, h * 0.18);
      g.fillStyle = "#EED9A8"; g.fillRect(0, h * 0.68, w, h * 0.32);
      g.fillStyle = "#FFFFFF"; g.beginPath(); g.arc(w * 0.25, h * 0.2, h * 0.07, 0, 7); g.fill();
      g.fillStyle = "#D9534F"; g.beginPath(); g.moveTo(w * 0.62, h * 0.8); g.arc(w * 0.62, h * 0.8, h * 0.16, Math.PI, 0); g.fill();
      g.strokeStyle = "#7A5A3A"; g.lineWidth = 8; g.beginPath(); g.moveTo(w * 0.62, h * 0.8); g.lineTo(w * 0.6, h * 0.95); g.stroke();
    }],
    [2000, 1000, (g, w, h) => {   // flower field (wide 2:1)
      sky(g, w, h * 0.45, "#F7C6A3", "#FBE9D6");
      g.fillStyle = "#5E9C4A"; g.fillRect(0, h * 0.45, w, h * 0.55);
      const cols = ["#E84A5F", "#F9D423", "#FFFFFF", "#9B59B6", "#FF8C42"];
      for (let i = 0; i < 700; i++) { const y = h * 0.47 + Math.pow(Math.random(), 0.7) * h * 0.53, r = 3 + (y / h) * 12;
        g.fillStyle = cols[i % cols.length]; g.beginPath(); g.arc(Math.random() * w, y, r, 0, 7); g.fill(); }
    }],
  ];

  async function seed() {
    state.photos = []; state.queue = []; state.current = null; state.nextId = 1;
    const day = 86400;
    const now = Date.now() / 1000;
    for (const [i, [w, h, draw]] of samples.entries()) await addPhoto(await scene(w, h, draw), null, now - (samples.length - i) * 3 * day);
    pickNext();
    state.lastSeen = now - 5 * 3600; state.battery = 3920;
  }
  window.__demo = {
    ready: seed(),
    async checkIn() { pickNext(); state.lastSeen = Date.now() / 1000; state.battery = Math.max(3300, (state.battery || 4100) - 8 - Math.round(Math.random() * 10)); },
    lowBattery() { state.lastSeen = Date.now() / 1000; state.battery = 3410; },
    async reset() { state.photos.forEach((p) => Object.values(p.urls).forEach((u) => URL.revokeObjectURL(u))); await seed(); },
  };
})();
