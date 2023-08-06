#!/bin/sh
alembic upgrade d9a5180c30e7

exec "$@"