from enum import Enum


class ScoringMode(str, Enum):
    WEIGHTED = "WEIGHTED"
    UNWEIGHTED = "UNWEIGHTED"


class PagerStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    DELETED = "DELETED"
    ARCHIVED = "ARCHIVED"


class PriorityLevel(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
