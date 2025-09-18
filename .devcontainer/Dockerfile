FROM mcr.microsoft.com/devcontainers/base:alpine-3.22

RUN    echo "@edge https://dl-cdn.alpinelinux.org/alpine/edge/main" >> /etc/apk/repositories \
    && echo "@edge https://dl-cdn.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories

RUN apk add curl abuild python3 py3-pydantic py3-rich uv@edge ruff@edge go-task-task@edge direnv

RUN UV_TOOL_DIR=/usr/local/share/uv/tools UV_TOOL_BIN_DIR=/usr/local/bin uv tool install -n bump-my-version

RUN echo 'eval "$(direnv hook bash)"' >> /etc/bash/bashrc