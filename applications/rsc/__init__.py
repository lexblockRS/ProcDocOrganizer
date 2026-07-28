"""Superfície pública estável da Application RSC.

Os imports históricos continuam disponíveis em seus módulos originais,
mas novos consumidores devem usar este pacote ou ``applications.rsc.api``.
"""

from .api import *  # noqa: F401,F403
from .api import __all__
