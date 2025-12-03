import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
import sys  # noqa: E402

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.graph_builder import GraphBuilder  # noqa: E402


async def build_from_file(query: str, signals_path: Path) -> Dict[str, Any]:
    with signals_path.open("r", encoding="utf-8") as fp:
        payload = json.load(fp)
    signals = payload.get("signals") or payload
    builder = GraphBuilder()
    return await builder.build_graph(query=query or payload.get("query", ""), signals=signals)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build expert network graph from signals file.")
    parser.add_argument(
        "--signals",
        type=Path,
        default=PROJECT_ROOT / "tests" / "sample_graph_signals.json",
        help="Path to JSON file containing signals payload.",
    )
    parser.add_argument("--query", type=str, default=None, help="Override query text for the build request.")
    args = parser.parse_args()

    result = asyncio.run(build_from_file(query=args.query or "", signals_path=args.signals))
    print(json.dumps({"graph_id": result["graph_id"], "preview": result["preview"]}, indent=2))
    print(f"\nGraph saved to {result['graph']['meta']['path']}")


if __name__ == "__main__":
    main()

