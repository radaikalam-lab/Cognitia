"""Startup script for Cognitia Standalone Runtime."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

# Add src and runtime to sys.path
RUNTIME_DIR = Path(__file__).resolve().parent.parent
COGNITIA_SRC = RUNTIME_DIR.parent / "src"

if str(COGNITIA_SRC) not in sys.path:
    sys.path.insert(0, str(COGNITIA_SRC))
if str(RUNTIME_DIR.parent) not in sys.path:
    sys.path.insert(0, str(RUNTIME_DIR.parent))

from runtime.gateway.app import create_gateway_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [CognitiaRuntime] %(message)s",
)
logger = logging.getLogger("CognitiaRuntime")


def main() -> None:
    parser = argparse.ArgumentParser(description="Cognitia Standalone Runtime")
    parser.add_argument("--host", default=os.getenv("COGNITIA_HOST", "127.0.0.1"), help="Host address (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=int(os.getenv("COGNITIA_PORT", "8000")), help="Port (default 8000)")
    args = parser.parse_args()

    # Invariant: Never allow 0.0.0.0 binding in standalone mode unless explicitly controlled
    if args.host == "0.0.0.0" and os.getenv("ALLOW_INSECURE_BIND") != "1":
        logger.warning("Attempted to bind to 0.0.0.0. Resetting to 127.0.0.1 for local security.")
        args.host = "127.0.0.1"

    config_dir = RUNTIME_DIR / "config"
    logger.info(f"Starting Cognitia Standalone Runtime on http://{args.host}:{args.port}")
    logger.info(f"Cognitive ABI: 1.0.0 | Epistemic Subsystem: Active | Authority: NONE")

    server = create_gateway_server(host=args.host, port=args.port, config_dir=config_dir)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Cognitia Runtime shutting down gracefully.")
        server.server_close()


if __name__ == "__main__":
    main()