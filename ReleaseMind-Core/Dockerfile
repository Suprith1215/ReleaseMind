# ============================================================
#  ReleaseMind — Production Dockerfile (AI Governance Engine)
#  Multi-stage build + gunicorn WSGI server
# ============================================================

# ── Stage 1: dependency builder ─────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install dependencies into an isolated prefix so we can copy them cleanly
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: runtime image ───────────────────────────────────
FROM python:3.11-slim AS runtime

# System deps (curl for HEALTHCHECK only)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy pre-built Python packages from builder stage
COPY --from=builder /install /usr/local

# Copy application code
COPY backend/  ./backend/
COPY frontend/ ./frontend/

# Copy the two new Python simulators (already inside backend/, no extra step needed)

# Create runtime directories
RUN mkdir -p backend/database backend/logs

# Non-root user for security
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser /app
USER appuser

# Environment
ENV PORT=7000
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 7000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:7000/ || exit 1

# ── Gunicorn: production WSGI server ──────────────────────────
# workers = (2 × CPU cores) + 1  →  3 workers is sensible for most VMs
# --chdir sets the working dir so module imports resolve correctly
CMD ["gunicorn", "api:app", \
     "--chdir", "backend", \
     "--bind", "0.0.0.0:7000", \
     "--workers", "3", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
