# harness/context.py

import subprocess

from pathlib import Path

from harness.utils import clip


# ------------------------------------------------------------
# Project Documents
# ------------------------------------------------------------

DOC_NAMES = (
    "AGENTS.md",
    "README.md",
    "README.txt",
    "pyproject.toml",
    "package.json",
)

# ------------------------------------------------------------
# Ignore Directories
# ------------------------------------------------------------

IGNORED_PATH_NAMES = {
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    ".mini-coding-agent",
}


# ------------------------------------------------------------

def git(args, cwd):
    """
    git 명령 실행
    """

    try:

        result = subprocess.run(

            ["git"] + args,

            cwd=cwd,

            capture_output=True,

            text=True,

            timeout=5,

        )

        if result.returncode == 0:
            return result.stdout.strip()

    except Exception:
        pass

    return ""


# ------------------------------------------------------------

class WorkspaceContext:

    def __init__(

        self,

        cwd,

        repo_root,

        branch,

        default_branch,

        status,

        recent_commits,

        project_docs,

    ):

        self.cwd = Path(cwd)

        self.repo_root = Path(repo_root)

        self.branch = branch

        self.default_branch = default_branch

        self.status = status

        self.recent_commits = recent_commits

        self.project_docs = project_docs

    # --------------------------------------------------------

    @classmethod
    def build(cls, cwd):

        cwd = Path(cwd).resolve()

        repo_root = git(

            ["rev-parse", "--show-toplevel"],

            cwd,

        )

        if not repo_root:

            repo_root = cwd

            branch = "-"

            default_branch = "-"

            status = "Not a Git repository"

            commits = ""

        else:

            branch = git(

                ["branch", "--show-current"],

                cwd,

            )

            default_branch = git(

                ["remote", "show", "origin"],

                cwd,

            )

            if "HEAD branch:" in default_branch:

                default_branch = default_branch.split(
                    "HEAD branch:"
                )[-1].strip()

            status = git(

                ["status", "--short"],

                cwd,

            )

            commits = git(

                [

                    "log",

                    "--oneline",

                    "-5",

                ],

                cwd,

            )

        docs = []

        root = Path(repo_root)

        for name in DOC_NAMES:

            file = root / name

            if file.exists():

                try:

                    docs.append(

                        f"===== {name} ====="

                    )

                    docs.append(

                        clip(

                            file.read_text(

                                encoding="utf-8",

                                errors="ignore",

                            ),

                            2000,

                        )

                    )

                except Exception:

                    pass

        return cls(

            cwd,

            repo_root,

            branch,

            default_branch,

            status,

            commits,

            docs,

        )

    # --------------------------------------------------------

    def summary(self):

        """
        Agent에서 사용하는 간단한 요약
        """

        return self.text()

    # --------------------------------------------------------

    def text(self):

        parts = [

            f"Current Directory : {self.cwd}",

            f"Repository        : {self.repo_root}",

            f"Current Branch    : {self.branch}",

            f"Default Branch    : {self.default_branch}",

            "",

            "Git Status",

            self.status or "(clean)",

            "",

            "Recent Commits",

            self.recent_commits or "(none)",

        ]

        if self.project_docs:

            parts.append("")
            parts.append("Project Documents")
            parts.extend(self.project_docs)

        return "\n".join(parts)