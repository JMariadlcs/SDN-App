# SDN_APP
A SDN application development with basic implementation of IPv4 packets, ARP protocol integration  and ICMP protocol management

Software Defined Networking (SDN) application that implements the functionality of an IPv4 router and runs on the RYU controller. To demonstrate the operation, it will be supported in a network emulation environment over Mininet.


# Milestone 1

The objective of this practice is to reproduce the Layer 3 (IPv4) packet switching processes that take place in a router. (IPv4) packet switching processes that take place in a  router. To implement the complete environment, we will proceed incrementally:

I. Implementation of the routing table in the switch.

II. Implementation of the ICMP protocol responses on the switch

III. Implementation of the ARP protocol responses on the switch

![Alt text](https://github.com/JMariadlcs/SDN_APP/blob/main/images/milestone1.png "")

# Milestone 2

In this step we introduce the functionality of sending packets from the controller. To do this, we will make it possible for the end devices to check the status of the switch gates by sending ICMP messages to the corresponding IP address. To do this, the controller will have to send ICMP response packets to the ICMP_REQUEST packets it receives.

# Milestone 2

In this step we will remove the static ARP protocol scheduling on the end devices and have the controller handle the ARP protocol response. To do this, we will add code to detect and decode ARP packets and an ARP_REQUEST packet response function in the management of packets sent by the switch to the controller.

# License
This project is a contribution of Jose María de la Cruz Sánchez and Jacobo del Castillo Monche.




