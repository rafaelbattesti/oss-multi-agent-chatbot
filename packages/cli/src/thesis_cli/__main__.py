"""Send a topic to the coordinator over A2A and print the resulting thesis."""

from __future__ import annotations

import argparse
import asyncio
import os

from a2a_core import call_agent
from thesis_contracts import ThesisRequest, ThesisResult

DEFAULT_URL = os.environ.get("COORDINATOR_URL", "http://localhost:9000")


def _render(thesis: ThesisResult) -> str:
    lines = [
        f"\nTOPIC: {thesis.topic}",
        f"\nTHESIS:\n  {thesis.statement}",
        f"\nARGUMENT:\n  {thesis.argument}",
        f"\nVIABLE: {thesis.viability.viable}  (after {thesis.revisions} revision(s))",
    ]
    if thesis.viability.issues:
        lines.append("\nOUTSTANDING ISSUES:")
        lines += [f"  - {i}" for i in thesis.viability.issues]
    if thesis.sources:
        lines.append("\nSOURCES:")
        lines += [f"  - {s.title} ({s.url})" for s in thesis.sources]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a reasoned, viable research thesis.")
    parser.add_argument("topic", help="research topic or area")
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"coordinator A2A URL (default: {DEFAULT_URL})",
    )
    args = parser.parse_args()

    result = asyncio.run(call_agent(args.url, ThesisRequest(topic=args.topic), ThesisResult))
    print(_render(result))


if __name__ == "__main__":
    main()
