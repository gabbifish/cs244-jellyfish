from mininet.node import Controller
import os

POXDIR = os.getcwd() + '/../..'

class JELLYPOX( Controller ):
    def __init__( self, name, cdir=POXDIR,
                  command='python pox.py', cargs=('log --file=jelly.log,w openflow.of_01 --port=%s ext.jelly_controller' ),
                  **kwargs ):
        Controller.__init__( self, name, cdir=cdir,
                             command=command,
                             cargs=cargs, **kwargs )

class JELLYPOXECMP( Controller ):
    def __init__( self, name, cdir=POXDIR,
                  command='python pox.py', cargs=('log --file=jelly.log,w openflow.of_01 --port=%s ext.jelly_controller_ecmp' ),
                  **kwargs ):
        Controller.__init__( self, name, cdir=cdir,
                             command=command,
                             cargs=cargs, **kwargs )

controllers={ 'jelly': JELLYPOX, 'jellyecmp': JELLYPOXECMP}
