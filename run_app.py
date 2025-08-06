import subprocess

# Commands to run
commands = [
    "streamlit run src/Home.py",
    "python src/send_worker.py",
]

# Run commands in parallel
processes = [subprocess.Popen(cmd, shell=True) for cmd in commands]


try:
    for process in processes:
        process.wait()
except KeyboardInterrupt:
    print("\nShutting down all processes...")
    for process in processes:
        process.terminate()
    print("All processes terminated.")
