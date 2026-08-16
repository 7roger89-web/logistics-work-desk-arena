"""Worker một lượt cho Telegram notification outbox."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.notifications import process_notification_outbox

if __name__ == "__main__":
    print(process_notification_outbox(batch_size=100))
