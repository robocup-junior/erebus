from pip._internal import main as _main
import importlib
import inspect

def _import(name, importModule, installModule=None, ver=None):
    try:
        inspect.stack()[1][0].f_globals[name] = importlib.import_module(importModule)
    except ImportError:
        try:
            if installModule is None:
                installModule = importModule
            if ver is None:
                _main(['install', installModule])
            else:
                _main(['install', '{}=={}'.format(installModule, ver)])
            inspect.stack()[1][0].f_globals[name] = importlib.import_module(importModule)
        except:
            print("[EREBUS IMPORT ERROR] can't import: {}".format(importModule))