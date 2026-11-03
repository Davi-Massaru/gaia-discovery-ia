ARG IRIS_IMAGE
FROM ${IRIS_IMAGE}
USER root
RUN mkdir -p /durable && chown irisowner:irisowner /durable
USER irisowner
WORKDIR /opt/gaia
COPY --chown=irisowner:irisowner requirements.txt module.xml ./
COPY --chown=irisowner:irisowner src/ src/
COPY --chown=irisowner:irisowner backend/ backend/
COPY --chown=irisowner:irisowner web/ web/
COPY --chown=irisowner:irisowner docs/contracts/ docs/contracts/
COPY --chown=irisowner:irisowner java-pex/src/ java-pex/src/
COPY --chown=irisowner:irisowner scripts/install.cos scripts/build_java.sh scripts/start.sh scripts/
RUN python3 -m pip install --user --break-system-packages --no-cache-dir -r requirements.txt \
    && sh scripts/build_java.sh \
    && iris start IRIS \
    && iris session IRIS -U USER < scripts/install.cos > /tmp/gaia-install.log \
    && cat /tmp/gaia-install.log \
    && grep -q '^GAIA_INSTALL_OK' /tmp/gaia-install.log \
    && iris stop IRIS quietly
CMD ["--check-caps", "false", "--after", "/opt/gaia/scripts/start.sh"]
