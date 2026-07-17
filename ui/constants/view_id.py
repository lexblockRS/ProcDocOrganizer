"""
Identificadores das views da aplicação.
"""

from enum import Enum, auto


class ViewId(Enum):
    """
    Identificadores únicos das views.
    """

    HOME = auto()
    FILES = auto()
    EVIDENCES = auto()
    TIMELINE = auto()
    CLASSIFICATIONS = auto()