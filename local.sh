#!/bin/bash

export FLASK_ENV=development
export PROJ_DIR=$PWD
export DEBUG=1

# Override by setting these in the environment, e.g. PORT=8080 ./local.sh
# Keep HOST on loopback by default: this dev server has no authentication.
HOST=${HOST:-127.0.0.1}
PORT=${PORT:-8000}

# This must be exported, not a bare assignment. A shell variable that is
# not exported is NOT inherited by the flask process below, so the server
# would fail to import our packages.
export PYTHONPATH=$(pwd):$PYTHONPATH

# run our server locally:
FLASK_APP=server.endpoints flask run --debug --host=$HOST --port=$PORT
