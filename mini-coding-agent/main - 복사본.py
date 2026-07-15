"""
__main__.py

Application Bootstrap

Program Start
    ↓
Console UI
    ↓
MiniAgent
"""

from tui.console import main as console_main


def main():
    """
    Bootstrap the application.
    """

    console_main()


if __name__ == "__main__":
    main()