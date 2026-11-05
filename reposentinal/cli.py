"""
Backward compatibility bridge to backend.cli.cli.
"""
from backend.cli.cli import (
    main,
    parse_args,
)

__all__ = [
    "main",
    "parse_args",
]

if __name__ == "__main__":
    main()
