# CODESYS Control for Linux SL runtime image (target: CODESYS V3.5 SP22)
#
# CODESYS Control for Linux SL is NOT publicly downloadable - it requires a
# CODESYS Store account and license agreement. Before building this image:
#
#   1. Log in to https://store.codesys.com with your account.
#   2. Download "CODESYS Control for Linux SL" matching V3.5 SP22
#      (package name looks like codesyscontrol-diagnosis-<arch>-<version>.deb
#      or a self-extracting *.sh / *.tar.gz installer, depending on the store).
#   3. Place the downloaded installer file into docker/installers/
#      and pass its filename as the CODESYS_RTE_INSTALLER build arg.
#
# Example:
#   docker build --build-arg CODESYS_RTE_INSTALLER=codesyscontrol_linux_x64_3.5.22.0.deb \
#                -t codesys-rte:3.5.22 -f docker/Dockerfile docker
#
# The runtime runs WITHOUT a runtime license in demo mode (limited running
# time per session, restart required afterwards) unless a valid license/
# container-license is provided - sufficient for CI smoke tests.

FROM ubuntu:latest

ARG CODESYS_RTE_INSTALLER
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        iproute2 \
        net-tools \
        libssl3 \
        libcap2-bin \
        procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/codesys-installer
COPY installers/${CODESYS_RTE_INSTALLER} ./installer.deb

# Install the runtime. The official installer registers a SysV init script
# under /etc/init.d/codesyscontrol - we do not rely on systemd since it is
# not PID 1 inside the container.
RUN dpkg -i ./installer.deb || apt-get install -f -y \
    && rm -rf /opt/codesys-installer

# Gateway (engineering/download traffic), OPC UA, WebVisu/webserver
EXPOSE 1217 4840 8080

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

HEALTHCHECK --interval=10s --timeout=5s --retries=6 \
    CMD /etc/init.d/codesyscontrol status || exit 1

ENTRYPOINT ["/entrypoint.sh"]
