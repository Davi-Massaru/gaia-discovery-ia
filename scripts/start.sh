#!/bin/sh
set -eu
iris session IRIS -U USER < /opt/gaia/scripts/install.cos > /tmp/gaia-start.log
cat /tmp/gaia-start.log
grep -q '^GAIA_INSTALL_OK' /tmp/gaia-start.log
