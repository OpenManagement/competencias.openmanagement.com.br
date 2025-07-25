# força uso de shell para expandir $PORT
web: sh -lc "exec gunicorn app:app --bind 0.0.0.0:${PORT:-8080}"

