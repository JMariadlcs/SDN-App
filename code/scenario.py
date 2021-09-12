#!/usr/bin/env python

from mininet.node import Node
from mininet.node import RemoteController
from mininet.node import OVSSwitch
from functools import partial
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.log import setLogLevel
from mininet.cli import CLI


class SingleSwitchTopo(Topo):
    'We connect 1 single switch to n hosts'
    def build(self, N=1):
        switch = self.addSwitch('s1')
        for h in range(N):
            host=self.addHost('h%s'%(h+1),mac='00:00:00:00:00:0%s'%(h+1), ip='10.0.%d.2/24'%h,defaultRoute='via 10.0.%d.1'%h)
            self.addLink(host, switch)



def simpleTestCLI():
    topo = SingleSwitchTopo(2)
    net = Mininet(topo, controller=partial(RemoteController, ip="127.0.0.1", port=6633), switch=partial(OVSSwitch, protocols="OpenFlow13"))
    net.start()

    CLI(net)
    net.stop()

if __name__ == '__main__':  
    setLogLevel('info')
    simpleTestCLI()
