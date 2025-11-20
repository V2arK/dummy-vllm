set shell := ["bash", "-uc"]

export PROJECT_ROOT := justfile_directory()
export DOCKER_IMAGE := "dummy-vllm"

default:
    just --list

build:
    docker build "{{PROJECT_ROOT}}" --file "{{PROJECT_ROOT}}/Dockerfile" --tag {{DOCKER_IMAGE}}

run:
    docker run --rm -p 8000:8000 -p 9000:9000 {{DOCKER_IMAGE}}

test:
    docker run --rm {{DOCKER_IMAGE}} pytest

shell:
    docker run --rm -it {{DOCKER_IMAGE}} /bin/bash

clean:
    docker rmi {{DOCKER_IMAGE}} || true

