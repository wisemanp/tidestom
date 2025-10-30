from pathlib import Path
import datetime
import logging

logger= logging.getLogger(__name__)

def list_existing_results(workspace_path: str, target_name: str):
    base = Path(workspace_path) / target_name
    results = []

    if not base.exists():
        return results

    for path in base.rglob("*.h5"):
        try:
            stat = path.stat()
            results.append({
                "run": path.parent.name,
                "path": str(path),
                "modified": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "size_kb": round(path.stat().st_size / 1024, 2),
            })
        except Exception as e:
            logger.warning(f"Failed to read metadata for {path}: {e}")

    results.sort(key=lambda r: r["modified"], reverse=True)
    return results

