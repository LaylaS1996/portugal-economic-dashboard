"""Source check for use in a recurring GitHub Actions workflow."""
from datetime import datetime, timezone
import json
from app import get_all

results, errors, timestamp = get_all()
status = {"checked_at_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
          "refresh_timestamp":timestamp,
          "loaded":{k:{"period":v["data"].iloc[-1]["Period"],"value":float(v["data"].iloc[-1]["Value"])} for k,v in results.items()},
          "errors":errors}
print(json.dumps(status, indent=2))
if errors or len(results) != 6:
    raise SystemExit("Incomplete source refresh — review errors above")
