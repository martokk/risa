import subprocess


def get_git_branch() -> str | None:
    """
    Get the current git branch by running 'git rev-parse --abbrev-ref HEAD'.

    Returns:
        The current git branch name, or None if not in a git repo or on error.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )
        branch = result.stdout.strip()
        return branch
    except Exception:
        return None
