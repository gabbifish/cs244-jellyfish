import os
import sys
import random
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.node import OVSController
from mininet.node import Controller
from mininet.node import RemoteController
from mininet.cli import CLI
sys.path.append("../../")
from pox.ext.jelly_pox import JELLYPOX
from subprocess import Popen
from time import sleep, time

class JellyFishTop(Topo):
    ''' TODO, build your topology here'''
    def build(self, nswitches=10, nhosts=10, k=4):
        switches = [self.addSwitch('s' + str(i)) for i in range(nswitches)]
        hosts = [self.addHost('h' + str(h)) for i in range(nhosts)]

        linkedSwitches = set()
        for s1 in switches:
            switches.remove(s1)
            for _ in range(k):
                s2 = random.choice(switches)
                if s1 != s2 and (s1, s2) not in linkedSwitches \
                        and (s2, s1) not in linkedSwitches:
                    self.addLink(s1, s2)
                    linkedSwitches.add((s1, s2))
            switches.add(s1)

        leftHost = self.addHost( 'h1' )
        rightHost = self.addHost( 'h2' )
        leftSwitch = self.addSwitch( 's3' )
        rightSwitch = self.addSwitch( 's4' )

        # Add links
        self.addLink( leftHost, leftSwitch )
        self.addLink( leftSwitch, rightSwitch )
        self.addLink( rightSwitch, rightHost )


def experiment(net):
    net.start()
    sleep(3)
    net.pingAll()
    net.stop()

def main():
	topo = JellyFishTop()
	net = Mininet(topo=topo, host=CPULimitedHost, link = TCLink, controller=JELLYPOX)
	experiment(net)

if __name__ == "__main__":
	main()

