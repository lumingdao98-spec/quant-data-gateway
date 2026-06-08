class BrokerAdapterError(RuntimeError):
    """Base broker adapter error."""


class BrokerUnsupportedError(BrokerAdapterError):
    """Raised internally when local broker SDK is unavailable."""


class LiveTradingDisabledError(BrokerAdapterError):
    """Raised internally when live trading flags block an operation."""
