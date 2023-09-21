#!/usr/bin/env bash

function check_args_len() {
  if [[ $# == 0 ]] || [[ $# -gt 2 ]]; then
    echo "Host must be set"
    exit 0
  fi
}

function gen_tls() {
  check_args_len "$@"

  HOST=$1

  TLS_DIR="$PWD/youtube_notifier_bot/bot/TLS"

  PRIVATE_KEY="private_key.pem"
  CERT="cert.pem"

  openssl genrsa -out "$TLS_DIR/$PRIVATE_KEY" 2048
  openssl req -new -x509 -nodes -days 3650 -key "$TLS_DIR/$PRIVATE_KEY" -out "$TLS_DIR/$CERT" -subj "/CN=$HOST"
}

gen_tls "$@"
