# dummy-vllm

High-throughput FastAPI backend that mimics the OpenAI/vLLM interface and returns
pre-generated responses immediately. Use it to benchmark client tooling such as FIB
without GPU inference noise.

## Quick Start

1. Build the container image:
   ```bash
   docker build -t dummy-vllm .
   ```
2. Launch the server (HTTP on `8000`, gRPC on `9000`):
   ```bash
   docker run --rm -p 8000:8000 -p 9000:9000 dummy-vllm
   ```
3. Send OpenAI-compatible requests against `http://localhost:8000`.

## Automation & Containers

- Use `just` for recurring tasks (all commands operate inside the container image):
  - `just build` — build the Docker image.
  - `just run` — run the container with both HTTP (8000) and gRPC (9000) exposed.
  - `just test` — execute `pytest` within the container.
  - `just shell` — open an interactive shell inside the image.

- The root `Dockerfile` builds a lean Python 3.12 image, installs `requirements.txt`, copies the
  repository, and executes `./run_server.sh`. No local virtual environment is required; run all
  workflows via the container.

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
| `DUMMY_VLLM_ENABLE_GRPC` | Toggle the gRPC server (default `true`). |
| `DUMMY_VLLM_GRPC_HOST` | Bind address for the gRPC server (defaults to `DUMMY_VLLM_HOST`). |
| `DUMMY_VLLM_GRPC_PORT` | gRPC listen port (default `9000`). |

## gRPC Interface

The container now exposes the same functionality via gRPC using the OpenAI-compatible
`VLLMService` proto (see `src/grpc_service/proto/openai.proto`). Available RPCs:

- `Completion` / `CompletionStream`
- `ChatCompletion` / `ChatCompletionStream`
- `ListModels`, `GetModelInfo`
- Health checks: `ServerLive`, `ServerReady`, `ModelReady`

Clients can point to `localhost:9000` by default; disable the gRPC server entirely by
setting `DUMMY_VLLM_ENABLE_GRPC=false`.

## Testing

Run the pytest suite after installing requirements:

```bash
pytest
```

## Notes

- The dummy generator never touches GPUs and keeps latency below a few milliseconds.
- Streaming responses follow SSE semantics (`data: ...` + `[DONE]` terminator) and emit
  distinct choice indexes when the client requests multiple completions.
