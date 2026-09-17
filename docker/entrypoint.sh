#!/bin/sh
# Starts the CODESYS Control for Linux SL runtime in the foreground so the
# container keeps running and its logs are visible via `docker logs`.
set -e

/etc/init.d/codesyscontrol start

CODESYSLOG=/var/opt/codesys/codesyscontrol.log
[ -f "$CODESYSLOG" ] || CODESYSLOG=/dev/null

trap '/etc/init.d/codesyscontrol stop; exit 0' TERM INT

tail -F "$CODESYSLOG" &
TAIL_PID=$!

# Keep the container alive while the runtime process is up.
while /etc/init.d/codesyscontrol status >/dev/null 2>&1; do
    sleep 5
done

kill "$TAIL_PID" 2>/dev/null || true
