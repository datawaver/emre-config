#!/usr/bin/env just

set dotenv-load

default:
    just --list

init:
    poetry update
    poetry install
    
test:
    poetry run pytest

run:
    poetry run emre-config
