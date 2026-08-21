from .pdnd_plugin import PdndPlugin

def classFactory(iface):
    return PdndPlugin(iface)
