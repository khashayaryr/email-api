"""A wrapper script to launch the entire email assistant application.

This script runs two key components in parallel as separate subprocesses:
1. The Streamlit web application (the user interface).
2. The background worker that sends scheduled emails.

Running this single file is the recommended way to start the application
for development. It ensures both the front-end and back-end services are active.
"""

import subprocess
import sys

from loguru import logger

# Configure logger for clean console output
logger.remove()
logger.add(
    sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    )


def main() -> None:
    """Launches the Streamlit UI and the background worker as parallel subprocesses.

    It waits for a KeyboardInterrupt (Ctrl+C) to gracefully terminate both child processes.
    """
    # List of shell commands to execute
    commands: list[str] = [
        "streamlit run src/Home.py",
        "python src/send_worker.py",
    ]

    # Launch all commands as parallel subprocesses
    processes: list[subprocess.Popen] = [
        subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for cmd in commands
    ]

    logger.info("Successfully launched Streamlit UI and background worker.")
    logger.info("Press Ctrl+C in this terminal to shut down all processes.")

    try:
        # This loop will block on the first process (streamlit), waiting for it to exit.
        # Its main purpose is to keep this script alive so we can catch the
        # KeyboardInterrupt (Ctrl+C) and terminate all managed subprocesses.
        for process in processes:
            process.wait()
    except KeyboardInterrupt:
        logger.warning("\nShutdown signal received. Terminating all processes...")
        for process in processes:
            process.terminate()
        logger.success("All processes terminated gracefully.")


if __name__ == "__main__":
    main()
