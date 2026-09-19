"""
agent.py  -- Person B
The loop: prompt -> model -> (tool call | final answer) -> tool -> model -> ...

Hand-rolled JSON protocol rather than native tool-calling, because it works
identically on every open-weight model and is trivial to debug on stage.
"""

import json
import re
import requests

from router import route
from tools import call_tool, tool_manifest

OLLAMA = "http://localhost:11434/api/chat"   # loopback only. Never change this.

SYSTEM = """You are an offline industrial assistant. You run entirely on-premise.

You have these tools:
{tools}

On every turn reply with ONE json object and nothing else. No prose, no markdown fences.

To use a tool:
{{"thought": "<one short sentence>", "tool": "<tool_name>", "args": {{...}}}}

When you have the final answer:
{{"thought": "<one short sentence>", "answer": "<the complete answer>"}}

Rules:
- Never invent tool output. Call the tool and wait.
- If a tool returns ERROR, either fix the arguments and retry once, or explain the failure in your answer.
- Prefer calling a tool over guessing.
"""

def _repair(block: str) -> str:
    """Models emit real newlines inside string values (esp. code). Escape them."""
    out = []
    in_str = False
    esc = False
    for ch in block:
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            elif ch == "\n":
                out.append("\\n"); continue
            elif ch == "\t":
                out.append("\\t"); continue
            elif ch == "\r":
                continue
        elif ch == '"':
            in_str = True
        out.append(ch)
    return "".join(out)


def _json_objects(s: str):
    """Yield every balanced {...} block, ignoring braces inside strings."""
    depth = 0
    start = None
    in_str = False
    esc = False
    for i, ch in enumerate(s):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            if depth:
                depth -= 1
                if depth == 0:
                    yield s[start:i + 1]


MAX_CONTEXT_CHARS = 12000   # ~3-4k tokens, safe for a 7B at default num_ctx


def trim(messages: list) -> list:
    """Keep system + first user turn + the most recent turns under a char budget."""
    if len(messages) <= 3:
        return messages
    head, tail = messages[:2], messages[2:]
    budget = MAX_CONTEXT_CHARS - sum(len(m["content"]) for m in head)
    kept = []
    for m in reversed(tail):
        c = m["content"]
        if len(c) > 2000:
            c = c[:1000] + "\n...[trimmed]...\n" + c[-500:]
        if budget - len(c) < 0:
            break
        budget -= len(c)
        kept.append({"role": m["role"], "content": c})
    return head + list(reversed(kept))


def chat(model: str, messages: list, timeout: int = 180) -> str:
    r = requests.post(OLLAMA, json={
        "model": model,
        "messages": messages,
        "stream": False,
        "format": "json",          # Ollama constrains output to valid JSON
        "options": {"temperature": 0.2},
    }, timeout=timeout)
    r.raise_for_status()
    return r.json()["message"]["content"]


def parse(raw: str) -> dict:
    """Models leak fences and prose. Grab the outermost JSON object."""
    best = None
    for block in _json_objects(raw):
        try:
            obj = json.loads(block)
        except json.JSONDecodeError:
            try:
                obj = json.loads(_repair(block))
            except json.JSONDecodeError:
                continue
        if not isinstance(obj, dict):
            continue
        if "tool" in obj or "answer" in obj:
            return obj          # a usable instruction wins immediately
        best = best or obj
    return best or {"answer": raw.strip()}


def run(task: str, has_file: bool = False, file_kind: str = "",
        max_steps: int = 6, verbose: bool = True) -> dict:
    """Returns {"answer":..., "model":..., "reason":..., "trace":[...]}"""
    r = route(task, has_file, file_kind)
    if verbose:
        print(f"[router] {r.model}  ({r.reason})")

    messages = [
        {"role": "system", "content": SYSTEM.format(tools=tool_manifest())},
        {"role": "user", "content": task},
    ]
    trace = []

    for step in range(max_steps):
        raw = chat(r.model, trim(messages))
        step_obj = parse(raw)
        messages.append({"role": "assistant", "content": raw})

        if "answer" in step_obj:
            trace.append({"step": step, "type": "answer",
                          "thought": step_obj.get("thought", "")})
            return {"answer": step_obj["answer"], "model": r.model,
                    "reason": r.reason, "trace": trace}

        name = step_obj.get("tool", "")
        args = step_obj.get("args", {}) or {}
        if verbose:
            print(f"[step {step}] tool={name} args={list(args)}")

        result = call_tool(name, args)
        trace.append({"step": step, "type": "tool", "tool": name,
                      "args": args, "result": result[:300]})
        messages.append({"role": "user",
                         "content": f"TOOL RESULT ({name}):\n{result}"})

    return {"answer": "Stopped: step limit reached.", "model": r.model,
            "reason": r.reason, "trace": trace}


if __name__ == "__main__":
    import sys
    task = " ".join(sys.argv[1:]) or "Compute the area of a 300mm diameter pipe cross-section."
    out = run(task)
    print("\n--- ANSWER ---\n" + out["answer"])
