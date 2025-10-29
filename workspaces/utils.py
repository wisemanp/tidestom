from pathlib import Path
import time
import os
import pwd
import grp
import logging

logger= logging.getLogger(__name__)

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

def ensure_dir(path: Path, owner_user="sniduser", owner_group="snidgroup", mode=0o770):
    os.makedirs(path, exist_ok=True)
    try:
        uid = pwd.getpwnam(owner_user).pw_uid
        gid = grp.getgrnam(owner_group).gr_gid
        for root, dirs, files in os.walk(path):
            os.chown(root, uid, gid)
            os.chmod(root, mode)
            for d in dirs:
                full_d = os.path.join(root, d)
                os.chown(full_d, uid, gid)
                os.chmod(full_d, mode)
    except KeyError:
        logger.warning(f"User or group not found: {owner_user}:{owner_group}. Skipping chown.")
