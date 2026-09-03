#!/bin/bash
set -e

# The app itself always runs as this fixed, unprivileged user/group -- PUID/PGID
# only control what host-side numeric uid:gid that user maps to, so files this
# container creates under /config (and reads under /data) match ownership on
# the Unraid host share instead of showing up as some arbitrary container-internal
# uid. Defaults (99:100) match Unraid's own "nobody:users".
PUID="${PUID:-99}"
PGID="${PGID:-100}"

if ! getent group "$PGID" >/dev/null 2>&1; then
    groupadd -o -g "$PGID" modelhub
fi
GROUP_NAME="$(getent group "$PGID" | cut -d: -f1)"

if ! getent passwd "$PUID" >/dev/null 2>&1; then
    useradd -o -u "$PUID" -g "$PGID" -M -s /usr/sbin/nologin modelhub
fi
USER_NAME="$(getent passwd "$PUID" | cut -d: -f1)"

# /config is fully owned by this container (db, thumbnails, secret key) so it's
# safe to reclaim ownership on every start; /data is the user's own library
# share and is deliberately left untouched -- the app only ever reads from it.
mkdir -p /config
chown -R "$PUID":"$PGID" /config

exec gosu "$USER_NAME":"$GROUP_NAME" "$@"
