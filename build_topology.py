import os
import sys
import random
from collections import defaultdict
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
# from time import sleep, time

class JellyFishTop(Topo):
    ''' TODO, build your topology here'''
    def build(self, nswitches=3, nhosts=3, k=3, r=1):
        nPortsUsed = defaultdict(int) # switch => num ports that have been connected to a link
        switches = [self.addSwitch('s' + str(i)) for i in range(nswitches)]
        hosts = [self.addHost('h' + str(i)) for i in range(nhosts)]
        
        # Connect each host to one switch
        for h in hosts:
            while True:
                s = random.choice(switches)
                nPorts = nPortsUsed[s]
                if r - nPorts > 0:
                    self.addLink(h, s)
                    nPortsUsed[s] = nPorts + 1
                    print h, "is connected to", s
                    break

        # Connect switches to each other
        linkPairs = set()

        switchPairs = []
        for idx, s1 in enumerate(switches):
            for idx2 in range(idx + 1, len(switches)):
                switchPairs.append((s1, switches[idx2]))

        random.shuffle(switchPairs)
        for s1, s2 in switchPairs:
            if nPortsUsed[s1] < k and nPortsUsed[s2] < k:
                self.addLink(s1, s2)
                print s1, "is connected to", s2
                nPortsUsed[s1] += 1
                nPortsUsed[s2] += 1


def experiment(net):
    net.start()
    # sleep(3)
    net.pingAll()
    net.stop()

TOPOS = {'JellyTopo' : (lambda : JellyFishTop())}
def main():
	topo = JellyFishTop()
	net = Mininet(topo=topo, host=CPULimitedHost, link = TCLink, controller=JELLYPOX)
	experiment(net)

if __name__ == "__main__":
	main()

