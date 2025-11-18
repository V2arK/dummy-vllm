# dummy-vllm

High-throughput FastAPI backend that mimics the OpenAI/vLLM interface and returns
pre-generated responses immediately. Use it to benchmark client tooling such as FIB
without GPU inference noise.

## Quick Start

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Launch the server with hot reload:
   ```bash
   ./run_server.sh
   ```
3. Send OpenAI-compatible requests against `http://localhost:8000`.

## Automation & Containers

- Task runner: use `just` for repeatable workflows.
  - `just install` — create/refresh the local virtual environment.
  - `just test` — run the pytest suite with the correct `PYTHONPATH`.
  - `just run` — start uvicorn with auto-reload for local development.
  - `just docker-build target=dev` — build the multi-stage image (`dev` or `prod`).
  - `just docker-run target=prod` — run the built image on port 8000.

- Container image: the root `Dockerfile` mirrors the platform API layout with `base`, `prod`,
  and `dev` stages. `prod` runs `./run_server.sh` directly, while `dev` bundles extra tooling
  for iterative work.

## API Surface

- `POST /v1/completions` — supports `prompt` as string or list, `n`, and `stream`.
- `POST /v1/chat/completions` — supports multi-choice responses and streaming SSE.
- `GET /v1/models` — returns a single configurable model entry.
- `GET /health` — liveness probe.
- `GET /metrics` — exposes request counts and generated token totals.

## Configuration

All knobs are available as environment variables (see `src/config.py` for defaults):

| Variable | Description |
| --- | --- |
| `DUMMY_VLLM_HOST` | Bind address for uvicorn. |
| `DUMMY_VLLM_PORT` | Listen port (default `8000`). |
| `DUMMY_VLLM_LOG_LEVEL` | Uvicorn log level. |
| `DUMMY_VLLM_MODEL` | Model identifier returned from `/v1/models`. |
| `DUMMY_VLLM_TTFT_DELAY` | Optional artificial delay before the first streamed token. |
| `DUMMY_VLLM_TOKEN_DELAY` | Optional per-token delay for streaming responses. |
| `DUMMY_VLLM_TOKEN_DELAY_JITTER` | Jitter range added to the token delay. |

## Testing

Run the pytest suite after installing requirements:

```bash
pytest
```

## Notes

- The dummy generator never touches GPUs and keeps latency below a few milliseconds.
- Streaming responses follow SSE semantics (`data: ...` + `[DONE]` terminator) and emit
  distinct choice indexes when the client requests multiple completions.
