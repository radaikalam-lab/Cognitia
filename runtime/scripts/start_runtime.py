"""Startup script for Cognitia Standalone Runtime."""

from __future__ import annotations

import argparse
import json
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
    format="%(asctime)s [%(levelname)s] [Cognitia] %(message)s",
)
logger = logging.getLogger("Cognitia")


def main() -> None:
    config_dir = RUNTIME_DIR / "config"
    runtime_cfg_path = config_dir / "runtime_config.json"
    default_host = "127.0.0.1"
    default_port = 8000

    if runtime_cfg_path.exists():
        try:
            cfg = json.loads(runtime_cfg_path.read_text(encoding="utf-8-sig"))
            default_host = cfg.get("host", default_host)
            default_port = cfg.get("port", default_port)
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Cognitia Standalone Runtime")
    parser.add_argument("--host", default=os.getenv("COGNITIA_HOST", default_host), help="Host address")
    parser.add_argument("--port", type=int, default=int(os.getenv("COGNITIA_PORT", default_port)), help="Port")
    args = parser.parse_args()

    logger.info(f"Starting Cognitia on http://{args.host}:{args.port}")
    logger.info("Cognitive ABI: 1.0.0 | Epistemic Subsystem: Active | Authority: NONE")

    server = create_gateway_server(host=args.host, port=args.port, config_dir=config_dir)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Cognitia shutting down gracefully.")
        server.server_close()


if __name__ == "__main__":
    main()