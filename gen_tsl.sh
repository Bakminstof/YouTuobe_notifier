#!/usr/bin/env bash

function check_args_len() {
  if [[ $# == 0 ]] || [[ $# -gt 2 ]]; then
    echo "Host must be set"
    exit 0
  fi
}

function gen_tsl() {
  check_args_len "$@"

  HOST=$1

  TSL_DIR="$PWD/youtube_notifier_bot/bot/TSL"

  PRIVATE_KEY="private_key.pem"
  CERT="cert.pem"

  openssl genrsa -out "$TSL_DIR/$PRIVATE_KEY" 2048
  openssl req -new -x509 -nodes -days 3650 -key "$TSL_DIR/$PRIVATE_KEY" -out "$TSL_DIR/$CERT" -subj "/CN=$HOST"
}

gen_tsl "$@"
