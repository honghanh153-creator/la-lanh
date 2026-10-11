# Database CA

`supabase-root-2021-ca.pem` is Supabase's public root CA ("Supabase Root 2021 CA",
valid until 2031-04-26). The app verifies PostgreSQL identity on every connection
(`app/db/session.py`), and Supabase's pooler certificate chains to this private root,
which is not in public trust stores.

- Source: Supabase dashboard → Database Settings → SSL Configuration → Download certificate
  (`https://supabase-downloads.s3-ap-southeast-1.amazonaws.com/prod/ssl/prod-ca-2021.crt`).
- SHA-256: `80:70:25:AD:50:D4:ED:21:9D:2C:9C:7D:29:9C:00:4F:82:4E:B0:0C:F7:F6:5A:FE:F6:07:D0:7B:72:E6:CA:FA`,
  matched on 2026-10-11 against the root presented by `aws-0-eu-central-1.pooler.supabase.com:5432`.
- Mounted read-only at `/etc/la-lanh/database-ca.pem`; the server-only `database_url` secret
  carries `sslrootcert=/etc/la-lanh/database-ca.pem`.
