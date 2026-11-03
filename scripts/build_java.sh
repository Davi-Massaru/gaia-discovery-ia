#!/bin/sh
set -eu
cd /opt/gaia
mkdir -p java-pex/build/classes
pex=$(find /usr/irissys/dev/java/lib -name 'intersystems-pex-*-shaded.jar' | head -n 1)
test -n "$pex"
javac -cp "$pex" -d java-pex/build/classes java-pex/src/main/java/com/gaia/discovery/pex/TapOutboundAdapter.java
jar cf java-pex/build/gaia-tap-pex.jar -C java-pex/build/classes .
