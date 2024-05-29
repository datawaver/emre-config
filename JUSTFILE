#!/usr/bin/env just

set dotenv-load

default:
    just --list

init:
    poetry install
    just check
    
test:
    poetry run pytest --without-slow-integration --without-integration

# including integration tests, needs manual setup
test-all:
    poetry run pytest

run:
    poetry run emre-config

check:
    poetry run ruff check emre_config tests 

verify: check test

lint: # autolint
    poetry run ruff format emre_config tests
    poetry run ruff check --fix emre_config tests