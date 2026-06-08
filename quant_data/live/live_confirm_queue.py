from __future__ import annotations

from quant_data.trading.human_confirm_queue import HumanConfirmQueue


class LiveConfirmQueue(HumanConfirmQueue):
    """Separate semantic queue for live orders; implementation reuses tested queue."""
