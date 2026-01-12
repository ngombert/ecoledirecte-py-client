from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import Client


class BaseManager:
    """Base class for all API resource managers."""

    def __init__(self, client: "Client"):
        self.client = client
