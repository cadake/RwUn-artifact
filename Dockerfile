ARG PYTHON_IMAGE=python:3.10.18-slim-bookworm

FROM ${PYTHON_IMAGE} AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_RESUME_RETRIES=10 \
    PIP_RETRIES=10 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update \
    && apt-get install --yes --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /artifact
COPY requirements-lock.txt build-constraints.txt ./

RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    find /usr/local/lib/python3.10/site-packages -name '*.pyc' -delete \
    && python -m pip install --upgrade pip==25.1 \
    && PIP_CONSTRAINT=/artifact/build-constraints.txt \
        python -m pip wheel --wheel-dir /wheels --requirement requirements-lock.txt

COPY pyproject.toml README.md LICENSE ./
COPY Reqomp-master ./Reqomp-master
COPY RwUn ./RwUn

RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    python -m pip wheel --wheel-dir /wheels --no-deps ./Reqomp-master .


FROM ${PYTHON_IMAGE}

LABEL org.opencontainers.image.title="RwUn OOPSLA 2026 artifact" \
      org.opencontainers.image.description="Reproduction package for RwUn ancilla uncomputation" \
      org.opencontainers.image.licenses="MIT"

ENV MPLBACKEND=Agg \
    MPLCONFIGDIR=/tmp/matplotlib \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /artifact
RUN --mount=type=bind,from=builder,source=/wheels,target=/wheels \
    python -m pip install --no-index --find-links=/wheels reqomp rwun \
    && python -m pip check

COPY . .
RUN python run_evaluation.py 0 \
    && chmod --recursive a+rwX "${MPLCONFIGDIR}"

CMD ["/bin/bash"]
