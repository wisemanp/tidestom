from pathlib import Path
import time

def list_existing_results(workspace_path: str, target_name: str):
    base = Path(workspace_path) / target_name
    results = []

    if not base.exists():
        return results

    for path in base.rglob("*.h5"):
        results.append({
            "run": path.parent.name,
            "path": str(path),
            "modified": time.ctime(path.stat().st_mtime),
            "size_kb": round(path.stat().st_size / 1024, 2),
        })

    results.sort(key=lambda r: r["modified"], reverse=True)
    return results

