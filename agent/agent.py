"""
agent.py -- Person B
The loop: prompt -> model -> (tool call | final answer) -> tool -> model -> ...

Hand-rolled JSON protocol rather than native tool-calling, because it works
identically on every open-weight model and is easy to debug on stage.
"""

import json
import re
import requests

from router import route
from tools import call_tool, tool_manifest


OLLAMA = "http://localhost:11434/api/chat"


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
- If the user asks for a report, approval note, Word document, or other file deliverable, you must call the appropriate writing tool before giving the final answer.
- After reading a document, use the extracted information to complete the user's requested task rather than returning the raw extraction as the final answer.
"""


def _repair(block: str) -> str:
    """Models sometimes emit real newlines inside JSON string values."""
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
                out.append("\\n")
                continue
            elif ch == "\t":
                out.append("\\t")
                continue
            elif ch == "\r":
                continue

        elif ch == '"':
            in_str = True

        out.append(ch)

    return "".join(out)


def _json_objects(s: str):
    """Yield balanced JSON objects while ignoring braces inside strings."""
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


MAX_CONTEXT_CHARS = 12000


def trim(messages: list) -> list:
    """Keep context within a safe character budget."""
    if len(messages) <= 3:
        return messages

    head, tail = messages[:2], messages[2:]

    budget = MAX_CONTEXT_CHARS - sum(
        len(m["content"]) for m in head
    )

    kept = []

    for m in reversed(tail):
        c = m["content"]

        if len(c) > 2000:
            c = c[:1000] + "\n...[trimmed]...\n" + c[-500:]

        if budget - len(c) < 0:
            break

        budget -= len(c)

        kept.append({
            "role": m["role"],
            "content": c
        })

    return head + list(reversed(kept))


def chat(model: str, messages: list, timeout: int = 180) -> str:
    response = requests.post(
        OLLAMA,
        json={
            "model": model,
            "messages": messages,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.2
            },
        },
        timeout=timeout,
    )

    response.raise_for_status()

    return response.json()["message"]["content"]


def parse(raw: str) -> dict:
    """Extract a usable tool call or final answer from model output."""

    best = None

    for block in _json_objects(raw):

        try:
            obj = json.loads(block, strict=False)

        except json.JSONDecodeError:

            try:
                obj = json.loads(
                    _repair(block),
                    strict=False
                )

            except json.JSONDecodeError:
                continue

        if not isinstance(obj, dict):
            continue

        if "tool" in obj or "answer" in obj:
            return obj

        best = best or obj

    return best or {"answer": raw.strip()}


def run(
    task: str,
    has_file: bool = False,
    file_kind: str = "",
    max_steps: int = 6,
    verbose: bool = True
) -> dict:

    r = route(task, has_file, file_kind)

    # Start with the model selected by the router.
    model = r.model

    if verbose:
        print(f"[router] {r.model}  ({r.reason})")

    messages = [
        {
            "role": "system",
            "content": SYSTEM.format(
                tools=tool_manifest()
            ),
        },
        {
            "role": "user",
            "content": task,
        },
    ]

    trace = []

    for step in range(max_steps):

        # Ask the current model what to do.
        raw = chat(
            model,
            trim(messages)
        )

        step_obj = parse(raw)

        messages.append({
            "role": "assistant",
            "content": raw
        })

        # Final answer.
        if "answer" in step_obj:

            trace.append({
                "step": step,
                "type": "answer",
                "thought": step_obj.get(
                    "thought",
                    ""
                ),
            })

            return {
                "answer": step_obj["answer"],
                "model": model,
                "reason": r.reason,
                "trace": trace,
            }

        # Tool call.
        name = step_obj.get("tool", "")
        args = step_obj.get("args", {}) or {}

        if verbose:
            print(
                f"[step {step}] tool={name} "
                f"args={list(args)}"
            )

        # Normalize write_report arguments.
        if name == "write_report":

            sections = args.get("sections_json")

            # Model sometimes returns sections_json as an actual list.
            if isinstance(sections, list):

                args["sections_json"] = json.dumps(
                    sections
                )

            # Model sometimes returns sections_json as a JSON string.
            elif isinstance(sections, str):

                try:
                    parsed = json.loads(
                        sections,
                        strict=False
                    )

                    args["sections_json"] = json.dumps(
                        parsed
                    )

                except json.JSONDecodeError:

                    args["sections_json"] = (
                        sections.replace(
                            "\n",
                            "\\n"
                        )
                    )

        # Execute the tool.
        result = call_tool(
            name,
            args
        )

        trace.append({
            "step": step,
            "type": "tool",
            "tool": name,
            "args": args,
            "result": result[:300],
        })

        # Give the tool result back to the model.
        messages.append({
            "role": "user",
            "content": (
                f"TOOL RESULT ({name}):\n"
                f"{result}"
            ),
        })

        # After OCR/vision extraction, hand the task
        # to the general reasoning model.
        if name == "read_document":
            model = "qwen2.5:7b"

    return {
        "answer": "Stopped: step limit reached.",
        "model": model,
        "reason": r.reason,
        "trace": trace,
    }


if __name__ == "__main__":
    import sys

    task = " ".join(sys.argv[1:])

    if not task:
        task = (
            "Compute the area of a 300mm "
            "diameter pipe cross-section."
        )

    out = run(task)

    print(
        "\n--- ANSWER ---\n"
        + str(out["answer"])
    )