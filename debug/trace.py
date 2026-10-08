"""Show the exchanges between opencode and its model.

A proxy that forwards every request of opencode to the model, unchanged, and prints what the
model is sent and what it answers.

Usage: python debug/trace.py [-f] [ollama|mistral]
  ollama   the local model (the default), on port 11435
  mistral  the Mistral API, on port 11436; needs the key in the variable MISTRAL_API_KEY
  -f       print the messages in full (otherwise, they are cut after 600 characters)
Then, in opencode, choose with /models the model whose name ends with "(traced)".
"""
import argparse
import http.server
import itertools
import json
import os
import sys
import threading
import urllib.error
import urllib.request

# Where each target listens (the ports of the providers "...-trace" in .opencode/opencode.json),
# and where it forwards to
TARGETS = {
    "ollama": {"port": 11435, "upstream": "http://127.0.0.1:11434", "key": None},
    "mistral": {"port": 11436, "upstream": "https://api.mistral.ai", "key": "MISTRAL_API_KEY"},
}

# The colours of the ReAct trace of the slides: thoughts in pale green, actions (tool calls)
# in pale blue, observations (tool results) in pale violet
GREEN, BLUE, VIOLET, GREY, BOLD, RESET = (
    "\033[38;5;151m", "\033[38;5;153m", "\033[38;5;183m", "\033[38;5;245m", "\033[1m", "\033[0m")

max_shown: int | None = 600  # characters of a message printed; None prints them in full
requests = itertools.count(1)
printing = threading.Lock()  # opencode may send several requests at once (e.g. to title the session)


# --- Display -----------------------------------------------------------------

def cut(text: str) -> str:
    """Return text, cut after max_shown characters."""
    if max_shown and len(text) > max_shown:
        return f"{text[:max_shown]} [... {len(text) - max_shown} more characters]"
    return text


def line(label: str, text: str, colour: str) -> str:
    """Return a labelled message, indented under its label."""
    body = cut(text).strip().replace("\n", "\n" + " " * 12)
    return f"{colour}{label:<11} {body}{RESET}"


def text_of(content: str | list | None) -> str:
    """Return the text of a message content, a string or a list of parts."""
    if isinstance(content, list):
        return "\n".join(part.get("text", "") for part in content if isinstance(part, dict))
    return content or ""


def show_request(n: int, request: dict) -> str:
    """Return what the model is sent: only the messages added since it last answered."""
    messages, tools = request.get("messages", []), request.get("tools", [])
    out = [f"\n{BOLD}=== request {n}: {len(messages)} messages, {len(tools)} tools, "
           f"{len(json.dumps(request))} characters ==={RESET}"]
    answered = [i for i, m in enumerate(messages) if m.get("role") == "assistant"]
    start = answered[-1] + 1 if answered else 0
    if start == 0:  # a new conversation: show the tools offered, then its system prompt
        names = ", ".join(t.get("function", {}).get("name", "?") for t in tools)
        out.append(line("tools", names or "(none)", GREY))
    for m in messages[start:]:
        if m.get("role") == "tool":
            out.append(line("tool result", text_of(m.get("content")), VIOLET))
        else:
            out.append(line(m.get("role", "?"), text_of(m.get("content")), GREY))
    return "\n".join(out)


def show_response(n: int, text: str, calls: list[dict], usage: dict | None) -> str:
    """Return what the model answered: its text, its tool calls, and the size of the prompt."""
    out = [f"{BOLD}--- response {n}{RESET}"]
    if text.strip():
        out.append(line("assistant", text, GREEN))
    out += [line("tool call", f"{c['name']}({c['arguments']})", BLUE) for c in calls]
    if usage:
        out.append(line("tokens", f"{usage.get('prompt_tokens')} in the prompt, "
                                  f"{usage.get('completion_tokens')} generated", GREY))
    return "\n".join(out)


# --- Reading the answer of the model -----------------------------------------

class Answer:
    """The answer of the model, rebuilt from its stream of deltas, or from one piece."""

    def __init__(self) -> None:
        """Start with an empty answer."""
        self.text: list[str] = []
        self.calls: dict[int, dict] = {}
        self.usage: dict | None = None

    def add_delta(self, data: dict) -> None:
        """Add one chunk of a streamed answer: a piece of text, or of a tool call."""
        self.usage = data.get("usage") or self.usage
        for choice in data.get("choices", []):
            delta = choice.get("delta", {})
            self.text.append(delta.get("content") or "")
            for call in delta.get("tool_calls") or []:
                c = self.calls.setdefault(call.get("index", len(self.calls)), {"name": "", "arguments": ""})
                c["name"] += call.get("function", {}).get("name") or ""
                c["arguments"] += call.get("function", {}).get("arguments") or ""

    def set_whole(self, data: dict) -> None:
        """Set an answer that came in one piece."""
        self.usage = data.get("usage")
        message = (data.get("choices") or [{}])[0].get("message", {})
        self.text = [message.get("content") or ""]
        for i, call in enumerate(message.get("tool_calls") or []):
            self.calls[i] = {"name": call["function"]["name"], "arguments": call["function"]["arguments"]}


# --- The proxy ---------------------------------------------------------------

class Proxy(http.server.BaseHTTPRequestHandler):
    """Forwards each request to the model, and prints the chat completions."""

    upstream = ""        # set by main
    key: str | None = None

    def log_message(self, *args) -> None:
        """Do not log each request: the chat completions are printed instead."""

    def do_GET(self) -> None:
        """Forward a GET (e.g. the list of models)."""
        self.forward(None)

    def do_POST(self) -> None:
        """Forward a POST, and print it if it is a chat completion."""
        self.forward(self.rfile.read(int(self.headers.get("Content-Length", 0))))

    def forward(self, body: bytes | None) -> None:
        """Send the request to the model, and stream its answer back, line by line."""
        chat = body is not None and self.path.endswith("/chat/completions")
        if chat:
            n = next(requests)
            request = json.loads(body)
            with printing:
                print(show_request(n, request), flush=True)

        headers = {"Content-Type": self.headers.get("Content-Type", "application/json")}
        if self.key:
            headers["Authorization"] = f"Bearer {self.key}"
        upstream = urllib.request.Request(self.upstream + self.path, data=body, method=self.command,
                                          headers=headers)
        try:
            response = urllib.request.urlopen(upstream)
        except urllib.error.HTTPError as error:  # forwarded as is: opencode shows the error
            response = error
        self.send_response(response.status)
        self.send_header("Content-Type", response.headers.get("Content-Type", "application/json"))
        self.end_headers()

        answer, raw = Answer(), []
        for chunk in response:  # one line at a time: the stream reaches opencode as it comes
            self.wfile.write(chunk)
            self.wfile.flush()
            raw.append(chunk)
            if chat and chunk.startswith(b"data: {"):  # a streamed answer: one delta per line
                answer.add_delta(json.loads(chunk[6:]))
        if not chat:
            return
        if not request.get("stream"):
            answer.set_whole(json.loads(b"".join(raw) or b"{}"))
        if response.status != 200:
            answer.text = [f"(error {response.status}) " + b"".join(raw).decode(errors="replace")]
        with printing:
            print(show_response(n, "".join(answer.text), list(answer.calls.values()), answer.usage),
                  flush=True)


def main() -> None:
    """Parse the command line, then run the proxy until Ctrl-C."""
    global max_shown
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("target", nargs="?", choices=TARGETS, default="ollama")
    parser.add_argument("-f", "--full", action="store_true", help="print the messages in full")
    args = parser.parse_args()
    target = TARGETS[args.target]
    if args.full:
        max_shown = None
    Proxy.upstream = target["upstream"]
    if target["key"]:
        Proxy.key = os.environ.get(target["key"])
        if not Proxy.key:
            sys.exit(f"Set your key first: export {target['key']}=...")

    print(f"Forwarding http://127.0.0.1:{target['port']} to {target['upstream']}; Ctrl-C to stop.")
    server = http.server.ThreadingHTTPServer(("127.0.0.1", target["port"]), Proxy)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
