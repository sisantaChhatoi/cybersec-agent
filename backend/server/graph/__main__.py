"""CLI entry: `python -m server.graph` rebuilds the fraud-intelligence layer."""

from server.graph.pipeline import run


def main() -> None:
    summary = run()
    print("fraud-intelligence build complete:")
    for key, value in summary.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
