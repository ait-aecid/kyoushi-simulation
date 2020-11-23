import sys
from .cli import cli

if __name__ == "__main__":
    cli(prog_name=f"{sys.executable} -m {__package__}")
