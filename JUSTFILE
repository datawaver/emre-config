#!/usr/bin/env just

set dotenv-load

default:
    just --list

init:
    poetry install
    
test:
    poetry run pytest

run:
    poetry run emre-config

validate:
    poetry run ruff check emre_config tests
