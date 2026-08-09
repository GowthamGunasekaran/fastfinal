from dataclasses import dataclass


@dataclass
class MetadataItem:
    market: str
    retailer: str
    channel: str
    category: str
    campaign: str