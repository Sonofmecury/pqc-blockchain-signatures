# Reproducible build image (Protocol Section 7.2 / 7.3 step 7).
# Pins liboqs to tag 0.15.0 so `docker build` reproduces the exact crypto stack,
# then runs the full pipeline: tests -> benchmarks -> model -> figures.
#
#   docker build -t pqc-blockchain .
#   docker run --rm -v "$PWD/results:/app/results" pqc-blockchain
#
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV LIBOQS_TAG=0.15.0
ENV LD_LIBRARY_PATH=/usr/local/lib
ENV PYTHONWARNINGS=ignore

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential cmake ninja-build git python3 python3-pip \
        libssl-dev ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# --- Build liboqs (C library), pinned, signature algorithms only ---
RUN git clone --depth 1 --branch ${LIBOQS_TAG} \
        https://github.com/open-quantum-safe/liboqs /tmp/liboqs && \
    cmake -GNinja -DBUILD_SHARED_LIBS=ON -DOQS_BUILD_ONLY_LIB=ON \
          -DOQS_MINIMAL_BUILD="SIG_ml_dsa_44;SIG_falcon_512;SIG_sphincs_sha2_128f_simple;SIG_sphincs_sha2_128s_simple" \
          -DCMAKE_INSTALL_PREFIX=/usr/local -B /tmp/liboqs/build /tmp/liboqs && \
    cmake --build /tmp/liboqs/build && \
    cmake --install /tmp/liboqs/build && \
    rm -rf /tmp/liboqs

WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt && \
    pip3 install --no-cache-dir git+https://github.com/open-quantum-safe/liboqs-python.git@0.12.0

COPY . .
# Full reproduction pipeline (tests -> bench -> model -> plots).
CMD ["bash", "scripts/run_all.sh"]
