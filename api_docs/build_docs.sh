#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ROOT="$(dirname "$DIR")"

$ROOT/api_docs/gen_api_rst.py

#$ROOT/api-docs/gen_api_rst.py
sphinx-build -a "$ROOT/api_docs" "$ROOT/public"
