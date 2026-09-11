import os
import subprocess
import sys


def main():
    root = os.path.dirname(os.path.abspath(__file__))
    script = os.path.join(root, "main.py")
    subprocess.run([sys.executable, script])


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExecution interrupted by user.")
        sys.exit(0)
    