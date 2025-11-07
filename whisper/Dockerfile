FROM nvidia/cuda:12.2.0-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    wget \
    curl \
    ca-certificates \
    python3 \
    python3-pip \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt
RUN git clone https://github.com/ggerganov/whisper.cpp.git
WORKDIR /opt/whisper.cpp

# RUN mkdir build && cd build && cmake .. && make -j
RUN mkdir build && cd build && cmake -DWITH_CUBLAS=1 .. && make -j

RUN mkdir -p models
RUN bash ./models/download-ggml-model.sh medium

# 6. Start whisper-server
# CMD ["./build/bin/whisper-server", "--host", "0.0.0.0", "-m", "/opt/whisper.cpp/models/ggml-medium.bin","--language", "vi", "--threads", "8"]
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]
