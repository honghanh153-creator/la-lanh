#!/usr/bin/env bash
# Create a private CA and a server certificate for a self-hosted PostgreSQL
# (rehearsal or staging), so the app's mandatory verified TLS still applies.
# Usage: make-db-tls.sh <output-dir> <server-hostname>
set -euo pipefail
out="${1:?output dir}"
host="${2:?server hostname}"
install -d -m 0755 "$out"
umask 077
openssl req -x509 -newkey rsa:2048 -nodes -days 30 -subj "/CN=la-lanh-db-ca" \
  -addext "basicConstraints=critical,CA:TRUE" -addext "keyUsage=critical,keyCertSign,cRLSign" \
  -addext "subjectKeyIdentifier=hash" \
  -keyout "$out/ca.key" -out "$out/ca.pem" >/dev/null 2>&1
openssl req -newkey rsa:2048 -nodes -subj "/CN=${host}" \
  -keyout "$out/server.key" -out "$out/server.csr" >/dev/null 2>&1
printf '%s\n' "basicConstraints=critical,CA:FALSE" "keyUsage=critical,digitalSignature,keyEncipherment" \
  "extendedKeyUsage=serverAuth" "subjectAltName=DNS:${host}" \
  "subjectKeyIdentifier=hash" "authorityKeyIdentifier=keyid" > "$out/ext.cnf"
openssl x509 -req -in "$out/server.csr" -CA "$out/ca.pem" -CAkey "$out/ca.key" -CAcreateserial \
  -days 30 -extfile "$out/ext.cnf" -out "$out/server.crt" >/dev/null 2>&1
rm -f "$out/server.csr" "$out/ext.cnf" "$out/ca.key" "$out/ca.srl"
# postgres (uid 70 in the alpine image) must own the key; the app only needs the CA.
chown 70:70 "$out/server.key" "$out/server.crt"
chmod 0600 "$out/server.key"
chmod 0644 "$out/server.crt" "$out/ca.pem"
chmod 0755 "$out"   # postgres must traverse it; the key itself stays 0600
