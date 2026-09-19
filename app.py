"""
app.py  -- Person B  |  THE DEMO SURFACE

Stdlib only. No Flask, no pip, no CDN. This matters: the whole pitch is
"runs air-gapped", so the UI must not fetch a single external byte.

    python3 app.py
    open http://localhost:8080

Shows the router decision and every tool call live. That visible trace is
the demo -- it proves an agent is reasoning, not just autocompleting.
"""

import json
import os
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer

import agent
from router import route

PORT = 8080
UPLOADS = "uploads"

PAGE = """<!doctype html><html><head><meta charset="utf-8">
<title>Sovereign AI Workbench</title><style>
:root{--bg:#0d1117;--fg:#e6edf3;--dim:#8b949e;--card:#161b22;--line:#30363d;--accent:#58a6ff;--ok:#3fb950}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 ui-sans-serif,system-ui,sans-serif}
header{padding:18px 24px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:12px}
header h1{font-size:17px;margin:0;font-weight:600}
.badge{margin-left:auto;font-size:12px;color:var(--ok);border:1px solid var(--ok);
  padding:3px 10px;border-radius:99px}
main{max-width:860px;margin:0 auto;padding:24px}
textarea{width:100%;background:var(--card);color:var(--fg);border:1px solid var(--line);
  border-radius:8px;padding:12px;font:inherit;resize:vertical;min-height:80px}
.row{display:flex;gap:10px;margin-top:10px;align-items:center}
button{background:var(--accent);color:#08121f;border:0;border-radius:8px;
  padding:10px 20px;font-weight:600;cursor:pointer}
button:disabled{opacity:.5;cursor:default}
input[type=file]{color:var(--dim);font-size:13px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;
  padding:14px 16px;margin-top:14px}
.label{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--dim);margin-bottom:6px}
.model{color:var(--accent);font-weight:600}
pre{white-space:pre-wrap;word-break:break-word;margin:6px 0 0;font-size:13px;color:var(--dim)}
.answer{border-left:3px solid var(--ok)}
</style></head><body>
<header><h1>Sovereign On-Premise Agentic AI Workbench</h1>
<span class="badge">OFFLINE &middot; localhost only</span></header>
<main>
  <textarea id="q" placeholder="e.g. Extract the findings from this inspection scan and write a Word report"></textarea>
  <div class="row">
    <input type="file" id="f">
    <button id="go" onclick="run()">Run</button>
  </div>
  <div id="out"></div>
</main>
<script>
const $ = s => document.querySelector(s);
function esc(t){const d=document.createElement('div');d.textContent=t;return d.innerHTML}
function card(label, body, cls){
  return `<div class="card ${cls||''}"><div class="label">${label}</div>${body}</div>`;
}
async function run(){
  const task = $('#q').value.trim(); if(!task) return;
  $('#go').disabled = true; $('#out').innerHTML = card('Status','Routing and running locally...');
  const fd = new FormData(); fd.append('task', task);
  if($('#f').files[0]) fd.append('file', $('#f').files[0]);
  try{
    const r = await fetch('/api/run', {method:'POST', body:fd});
    const d = await r.json();
    let h = card('Router', `<span class="model">${esc(d.model)}</span><pre>${esc(d.reason)}</pre>`);
    (d.trace||[]).forEach(t=>{
      if(t.type==='tool')
        h += card(`Tool call &middot; step ${t.step}`,
          `<span class="model">${esc(t.tool)}</span><pre>${esc(JSON.stringify(t.args))}</pre>
           <pre>&rarr; ${esc(t.result)}</pre>`);
    });
    h += card('Answer', `<pre style="color:var(--fg)">${esc(d.answer)}</pre>`, 'answer');
    $('#out').innerHTML = h;
  }catch(e){ $('#out').innerHTML = card('Error', `<pre>${esc(e)}</pre>`); }
  $('#go').disabled = false;
}
$('#q').addEventListener('keydown', e=>{ if(e.key==='Enter'&&(e.metaKey||e.ctrlKey)) run(); });
</script></body></html>"""


def parse_multipart(body: bytes, boundary: bytes):
    """Tiny multipart parser -- enough for one text field and one file."""
    fields, files = {}, {}
    for part in body.split(b"--" + boundary):
        if b"\r\n\r\n" not in part:
            continue
        head, data = part.split(b"\r\n\r\n", 1)
        data = data.rstrip(b"\r\n-")
        head = head.decode("utf-8", "ignore")
        if 'name="' not in head:
            continue
        name = head.split('name="', 1)[1].split('"', 1)[0]
        if 'filename="' in head:
            fn = head.split('filename="', 1)[1].split('"', 1)[0]
            if fn:
                files[name] = (fn, data)
        else:
            fields[name] = data.decode("utf-8", "ignore")
    return fields, files


def kind_of(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext in (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"):
        return "image"
    if ext == ".pdf":
        return "pdf"
    return "text"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass  # keep the demo terminal clean

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, PAGE.encode(), "text/html; charset=utf-8")
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):
        if self.path != "/api/run":
            return self._send(404, b"not found", "text/plain")
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            ctype = self.headers.get("Content-Type", "")
            boundary = ctype.split("boundary=")[-1].encode()
            fields, files = parse_multipart(body, boundary)

            task = fields.get("task", "")
            has_file, file_kind = False, ""
            if "file" in files:
                fn, data = files["file"]
                os.makedirs(UPLOADS, exist_ok=True)
                path = os.path.join(UPLOADS, os.path.basename(fn))
                with open(path, "wb") as fh:
                    fh.write(data)
                has_file, file_kind = True, kind_of(fn)
                task = f"{task}\n\n[Attached file saved at: {path}]"

            result = agent.run(task, has_file, file_kind)
        except Exception:
            traceback.print_exc()
            r = route("", False, "")
            result = {"answer": "Server error -- see terminal.",
                      "model": r.model, "reason": "n/a", "trace": []}
        self._send(200, json.dumps(result).encode(), "application/json")


if __name__ == "__main__":
    print(f"Workbench on http://localhost:{PORT}   (bound to loopback only)")
    # "127.0.0.1" not "0.0.0.0" -- nothing outside this machine can reach it.
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
