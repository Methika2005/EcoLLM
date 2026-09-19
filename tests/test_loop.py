"""
test_loop.py  -- Person B
Run the whole agent loop WITHOUT Ollama, WITHOUT Docker, WITHOUT C's OCR.

This is your safety net. Run it after every change:
    python3 test_loop.py

If this passes and the live demo breaks, the bug is in the model or a
teammate's tool -- not in your loop. That saves you an hour at 2am.
"""

from agent import agent
import tools

PASS, FAIL = 0, 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        print(f"  FAIL  {name}  {detail}")


def scripted(*replies):
    """Replace agent.chat with a fixed sequence of model outputs."""
    it = iter(replies)
    agent.chat = lambda model, messages, timeout=180: next(it)


# ---------------------------------------------------------------- 1. router
print("\n[1] routing")
from router import route
check("code -> coder", route("write a python script").model.startswith("qwen2.5-coder"))
check("doc  -> general", route("summarise the inspection report").model == "qwen2.5:7b")
check("image-> vision", route("read this", True, "image").needs_vision)

# ---------------------------------------------------------------- 2. parser
print("\n[2] parsing messy model output")
p = agent.parse
check("fenced json", p('```json\n{"answer":"x"}\n```').get("answer") == "x")
check("preamble", p('Sure!\n{"answer":"x"}').get("answer") == "x")
check("two objects", p('{"thought":"a"} {"answer":"b"}').get("answer") == "b")
check("multiline code", p('{"tool":"run_python","args":{"code":"a=1\nprint(a)"}}').get("tool") == "run_python")
check("plain prose", p("I cannot help.").get("answer") == "I cannot help.")

# ---------------------------------------------------------------- 3. one tool call
print("\n[3] single tool call then answer")
tools.TOOLS["run_python"] = (lambda code: "3.14", "stub")
scripted(
    '{"thought":"compute","tool":"run_python","args":{"code":"print(3.14)"}}',
    '{"thought":"done","answer":"The value is 3.14"}',
)
out = agent.run("compute pi", verbose=False)
check("final answer returned", out["answer"] == "The value is 3.14", out["answer"])
check("trace has tool step", any(t["type"] == "tool" for t in out["trace"]))

# ---------------------------------------------------------------- 4. tool errors
print("\n[4] tool failure is survivable")
scripted(
    '{"tool":"does_not_exist","args":{}}',
    '{"answer":"That tool is unavailable."}',
)
out = agent.run("do a thing", verbose=False)
check("recovers from unknown tool", "unavailable" in out["answer"])

scripted(
    '{"tool":"run_python","args":{"wrong":"arg"}}',
    '{"answer":"Bad arguments, corrected."}',
)
out = agent.run("compute something", verbose=False)
check("recovers from bad args", "corrected" in out["answer"])

# ---------------------------------------------------------------- 5. step cap
print("\n[5] runaway loop is capped")
agent.chat = lambda model, messages, timeout=180: '{"tool":"run_python","args":{"code":"1"}}'
out = agent.run("loop forever", max_steps=4, verbose=False)
check("stops at limit", "step limit" in out["answer"].lower())
check("no more than 4 steps", len(out["trace"]) <= 4, str(len(out["trace"])))

# ---------------------------------------------------------------- 6. trimming
print("\n[6] context stays bounded")
msgs = [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}]
msgs += [{"role": "user", "content": "x" * 5000} for _ in range(10)]
t = agent.trim(msgs)
total = sum(len(m["content"]) for m in t)
check("under budget", total <= agent.MAX_CONTEXT_CHARS, f"{total} chars")
check("system kept", t[0]["content"] == "s")
check("original task kept", t[1]["content"] == "u")

print(f"\n{PASS} passed, {FAIL} failed\n")
raise SystemExit(1 if FAIL else 0)
