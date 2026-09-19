# Interface contract — post this in the team group NOW

Person B owns the router and agent loop. Everything crosses between us through
exactly one shape. If we agree on this at hour 1, integration at hour 6 is
wiring, not rewriting.

## For Person D — code sandbox

Fill in the body of `run_python` in `tools.py`. Nothing else.

```python
def run_python(code: str) -> str:
```

- Takes one keyword arg `code`, a string of Python.
- Returns a **string**: stdout + stderr combined.
- On failure return `"ERROR: <reason>"`. Do not raise. Do not print.
- Must return within 30s. Enforce it yourself; I also cap it.
- Keep output under 2000 chars — it goes back into the model's context.

I call it as `run_python(code="print(1)")`. Nothing else about your Docker
setup matters to me.

## For Person C — documents

Fill in these two in `tools.py`:

```python
def read_document(path: str) -> str:      # OCR / parse, return plain text
def search_documents(query: str) -> str:  # vector search, return top passages
```

Same rules: string in, string out, `"ERROR: ..."` on failure, never raise.

Also tell me, by hour 2, **whether you are using LLaVA or Tesseract**:
- LLaVA → I keep the vision branch in `router.py`, you confirm the exact
  `ollama pull` tag.
- Tesseract → I delete the vision branch. `read_document` handles OCR and the
  general model gets plain text.

A dead code path that errors on stage is worse than no path.

## For Person A — network

The loop only ever calls `http://localhost:11434`. The web UI binds to
`127.0.0.1`, not `0.0.0.0`. Nothing in my code fetches anything external —
the UI has no CDN, no web fonts, no remote scripts. Verify that in your
egress monitor and use it in the demo.

## Adding a new tool

One entry in `TOOLS`, in `tools.py`:

```python
"tool_name": (function, "What it does. Args: name (type). Returns what."),
```

The description string is literally what the model reads. Blunt and literal
beats elegant. Then run `python3 test_loop.py` — if it passes, you didn't
break the loop.

## Rules we don't break after hour 9

- No new tools after the freeze.
- Any change to a function signature gets announced in the group, not just
  committed.
- `test_loop.py` must pass before anyone pushes.
