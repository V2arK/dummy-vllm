set shell := ["bash", "-uc"]

export PROJECT_ROOT := justfile_directory()
export PYTHONPATH := PROJECT_ROOT
export DOCKER_IMAGE := "dummy-vllm"

venv_dir := PROJECT_ROOT + "/.venv"
python := venv_dir + "/bin/python"
pip := venv_dir + "/bin/pip"

default:
    just --list

install:
    if [ ! -d "{{venv_dir}}" ]; then python3 -m venv "{{venv_dir}}"; fi
    "{{pip}}" install --upgrade pip
    "{{pip}}" install -r "{{PROJECT_ROOT}}/requirements.txt"

test: install
    PYTHONPATH="{{PROJECT_ROOT}}" "{{python}}" -m pytest

run: install
    PYTHONPATH="{{PROJECT_ROOT}}" "{{python}}" -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

lint: install
    PYTHONPATH="{{PROJECT_ROOT}}" "{{python}}" -m compileall src tests

docker-build target="prod":
    docker build "{{PROJECT_ROOT}}" --file "{{PROJECT_ROOT}}/Dockerfile" --target {{target}} --tag {{DOCKER_IMAGE}}:{{target}}

docker-run target="prod":
    docker run --rm -p 8000:8000 {{DOCKER_IMAGE}}:{{target}}

docker-shell:
    docker run --rm -it {{DOCKER_IMAGE}}:dev /bin/bash

clean:
    rm -rf "{{venv_dir}}" "{{PROJECT_ROOT}}/.pytest_cache" "{{PROJECT_ROOT}}/.mypy_cache" "{{PROJECT_ROOT}}/.ruff_cache"

