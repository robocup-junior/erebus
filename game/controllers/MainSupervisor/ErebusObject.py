from __future__ import annotations
from abc import ABC, abstractmethod

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from MainSupervisor import Erebus

class ErebusObject(ABC):
    """Abstract class used to store erebus reference objects used within other
    objects
    """
    
    @abstractmethod
    def __init__(self, erebus: Erebus):
        self._erebus = erebus