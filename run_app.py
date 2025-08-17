"""A wrapper script to launch the entire email assistant application."""
import subprocess
import sys
import time

from loguru import logger

logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
)

def main() -> None:
    # Commands as arg lists (no shell=True)
    commands: list[list[str]] = [
        ["streamlit", "run", "src/Home.py"],
        ["python", "src/send_worker.py"],
    ]

    processes: list[subprocess.Popen] = []
    for cmd in commands:
        p = subprocess.Popen(cmd)  # inherits stdio
        processes.append(p)

    logger.info("Successfully launched Streamlit UI and background worker.")
    logger.info("Press Ctrl+C in this terminal to shut down all processes.")

    try:
        # Keep the wrapper alive while children run
        while True:
            # If any process exits unexpectedly, break
            for p in processes:
                ret = p.poll()
                if ret is not None and ret != 0:
                    logger.error(f"Process {p.args} exited with code {ret}. Shutting down others.")
                    raise KeyboardInterrupt
            time.sleep(1)
    except KeyboardInterrupt:
        logger.warning("Shutdown signal received. Terminating all processes...")
        for p in processes:
            try:
                p.terminate()
            except Exception:
                pass
        # Grace period
        time.sleep(2)
        for p in processes:
            if p.poll() is None:
                try:
                    p.kill()
                except Exception:
                    pass
        logger.success("All processes terminated gracefully.")

if __name__ == "__main__":
    main()
