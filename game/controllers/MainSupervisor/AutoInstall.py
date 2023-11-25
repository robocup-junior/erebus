import importlib
import inspect

from typing import Optional
from pip._internal import main as _main


def _import(
    name: str,
    importModule: str,
    installModule: Optional[str] = None,
    ver: Optional[str] = None
) -> None:
    """Import and install python modules automatically

    Args:
        name (str): Name to reference module as (e.g. import numpy as np)
        importModule (str): Pip module name to import
        installModule (Optional[str], optional): Pip module name to install. Leave 
            blank (default None) to install the same module as is imported.
        ver (Optional[str], optional): Specify module version. Defaults to None.
    """
    try:
        inspect.stack()[1][0].f_globals[name] = importlib.import_module(
            importModule)
    except ImportError:
        try:
            if installModule is None:
                installModule = importModule
            if ver is None:
                _main(['install', installModule])
            else:
                _main(['install', f'{installModule}=={ver}'])
            inspect.stack()[1][0].f_globals[name] = importlib.import_module(
                importModule)
        except:
            print(f"[EREBUS IMPORT ERROR] can't import: {importModule}")
