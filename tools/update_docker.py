from pathlib import Path
import subprocess

REPO_PATH = Path(__file__).parent.parent

def main():
    subprocess.run(
        ["docker", "build", "-f", REPO_PATH / ".devcontainer" / "Dockerfile", 
         "-t", "ghcr.io/fuquery/antora:latest", "."],
        check=True,
        cwd=str(REPO_PATH))
    
    subprocess.run(
        ["docker", "push", "ghcr.io/fuquery/antora:latest"],
        check=True,
        cwd=str(REPO_PATH))


if __name__ == "__main__":
    main()
