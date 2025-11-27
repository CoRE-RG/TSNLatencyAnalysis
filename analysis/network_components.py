################################################################################################
# File: networking_components.py
# Description: Contains classes for network components like flows, links and paths.
# Author: Timo Salomon
#
# Copyright (C) 2025 Timo Salomon, for HAW Hamburg, Germany
#
# This file is licensed under the GNU Lesser General Public License v3.0 or later.
# You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <https://www.gnu.org/licenses/lgpl-3.0.html>
# SPDX-License-Identifier: LGPL-3.0-or-later
################################################################################################


class Flow:
    """
    Represents a flow in the network.
    Note: Cross Traffic flows should not be created as flows but are considered via the MAX_PACKET_BITS.

    Attributes:
        src (str): The source node of the flow.
        dst (str): The destination node of the flow.
        size (int): The size of the flow in bytes.
        deadline (float): The deadline for the flow in seconds.
        period (float): The period of the flow in seconds.
        priority (int): The priority of the flow.
    """

    def __init__(self, src, dst, size, deadline, period, priority):
        self.src = src
        self.dst = dst
        self.size = size
        self.deadline = deadline
        self.period = period
        self.priority = priority

    def __str__(self):
        return (
            "Flow: src: "
            + str(self.src)
            + " dst: "
            + str(self.dst)
            + " size: "
            + str(self.size)
            + " deadline: "
            + str(self.deadline)
            + " period: "
            + str(self.period)
            + " priority: "
            + str(self.priority)
        )

    def __repr__(self):
        return self.__str__()


class Link:
    """
    Represents a link between two nodes (including bridges) in a network.

    Attributes:
        src (str): The source node of the link.
        dst (str): The destination node of the link.
        rate (float): The rate of the link in units per second. Currently unused, instead LINKSPEED is used for all links.
        delay (float): The delay of the link in seconds. Currently unused.
        idleSlope (float): The idle slope of the link.
    """

    def __init__(self, src, dst, rate, delay, idleSlope):
        self.src = src
        self.dst = dst
        self.rate = rate
        self.delay = delay
        self.idleSlope = idleSlope

    def isLinkFor(self, src, dst, ignoreDirection=False):
        """
        Checks if the link is between the specified source and destination nodes.

        Args:
            src (str): The source node to check.
            dst (str): The destination node to check.
            ignoreDirection (bool, optional): If True, ignores the direction of the link. Defaults to False.

        Returns:
            bool: True if the link is between the specified source and destination nodes, False otherwise.
        """
        if ignoreDirection:
            return (self.src == src and self.dst == dst) or (self.src == dst and self.dst == src)
        else:
            return self.src == src and self.dst == dst

    def __str__(self):
        return (
            "Link: src: "
            + str(self.src)
            + " dst: "
            + str(self.dst)
            + " rate: "
            + str(self.rate)
            + " delay: "
            + str(self.delay)
            + " idleSlope: "
            + str(self.idleSlope)
        )

    def __repr__(self):
        return self.__str__()


class Path:
    """
    Represents a path from a source node to a destination node in a network.

    Attributes:
        src (str): The source node of the path.
        dst (str): The destination node of the path.
        links (list): A list of links that make up the path. (must not be necessarily in order)
    """

    def __init__(self, src, dst, links=[]):
        self.src = src
        self.dst = dst
        self.links = links

    def addLinks(self, link):
        """
        Adds a link to the path if it doesn't already exist.

        Args:
            link (Link): The link to be added.
        """
        for l in self.links:
            if l.isLinkFor(link.src, link.dst):
                return
        self.links.append(link)

    def __str__(self):
        return "Path from " + str(self.src) + " to " + str(self.dst) + " via links: " + str(self.links)

    def __repr__(self):
        return self.__str__()


class Network:
    """
    Represents a network consisting of bridges, nodes, links, flows and paths.

    Attributes:
        bridges (list): A list of bridges in the network.
        nodes (list): A list of nodes in the network.
        links (list): A list of links in the network.
        flows (list): A list of flows in the network.
        paths (list): A list of paths in the network.
        IFG (int): The interframe gap in bits.
    """

    def __init__(self, bridges=[], nodes=[], links=[], flows=[], paths=[], IFG=96):
        self.bridges = bridges
        self.nodes = nodes
        self.links = links
        self.flows = flows
        self.paths = paths
        self.IFG = IFG

    def __str__(self):
        return (
            "Network: bridges: "
            + str(self.bridges)
            + " nodes: "
            + str(self.nodes)
            + " links: "
            + str(self.links)
            + " flows: "
            + str(self.flows)
            + " paths: "
            + str(self.paths)
        )

    def __repr__(self):
        return self.__str__()

    def addBridge(self, bridge):
        """
        Adds a bridge to the network if it doesn't already exist.

        Args:
            bridge (str): The bridge to be added.
        """
        if bridge not in self.bridges:
            self.bridges.append(bridge)

    def addNode(self, node):
        """
        Adds a node to the network if it doesn't already exist.

        Args:
            node (str): The node to be added.
        """
        if node not in self.nodes:
            self.nodes.append(node)

    def addBidirectionalLink(self, src, dst, rate, delay, idleSlope=0.0):
        """
        Adds a bidirectional link between two nodes.

        Args:
            src (str): The source node.
            dst (str): The destination node.
            rate (float): The link rate in Mbps.
            delay (float): The link delay in milliseconds.
            idleSlope (float): The idle slope of the link in bit/s.

        Returns:
            None
        """
        self.addLink(src, dst, rate, delay, idleSlope)
        self.addLink(dst, src, rate, delay, idleSlope)

    def addLink(self, src, dst, rate, delay, idleSlope):
        """
        Adds a link between two nodes.

        Args:
            src (str): The source node.
            dst (str): The destination node.
            rate (float): The link rate in Mbps.
            delay (float): The link delay in milliseconds.
            idleSlope (float): The idle slope of the link.
        """
        if self.getLink(src, dst) is None:
            link = Link(src, dst, rate, delay, idleSlope)
            self.links.append(link)

    def getLink(self, src, dst):
        """
        Gets the link from the source two the destination node.

        Args:
            src (str): The source node.
            dst (str): The destination node.

        Returns:
            Link: The link between the two nodes, or None if no link exists.
        """
        for link in self.links:
            if link.isLinkFor(src, dst):
                return link
        return None

    def calculateShortestPath(self, src, dst):
        """
        Calculates the shortest path from the source to the destination node.

        Args:
            src (str): The source node.
            dst (str): The destination node.

        Returns:
            Path: The shortest path from the source to the destination node.
        """
        # check if path is already known
        path = self.lookupPath(src, dst)
        if path is not None:
            return path
        # find shortest path with Dijkstra's algorithm
        unvisited = [src]
        visited = []
        distances = {src: 0}
        previous = {}
        while unvisited:
            current = unvisited[0]
            unvisited.remove(current)
            visited.append(current)
            for link in self.links:
                if link.src == current and link.dst not in visited:
                    if link.dst not in unvisited:
                        unvisited.append(link.dst)
                    if link.dst not in distances:
                        distances[link.dst] = distances[current] + 1
                        previous[link.dst] = current
        path = Path(src, dst)
        current = dst
        while current != src:
            path.addLinks(self.getLink(previous[current], current))
            current = previous[current]
        # add path to network for future use
        self.addPath(path)
        return path

    def lookupPath(self, src, dst):
        """
        Finds the path from the source to the destination node.

        Args:
            src (str): The source node.
            dst (str): The destination node.

        Returns:
            Path: The path from the source to the destination node, or None if no path exists.
        """
        for path in self.paths:
            if path.src == src and path.dst == dst:
                return path
        return None

    def initializeAllPaths(self):
        """
        Initializes all possible paths in the network.
        """
        for src in self.nodes:
            for dst in self.nodes:
                if src != dst:
                    self.calculateShortestPath(src, dst)

    def addPath(self, path):
        """
        Adds a path to the network if it doesn't already exist.

        Args:
            path (Path): The path to be added.
        """
        if self.lookupPath(path.src, path.dst) is None:
            self.paths.append(path)

    def addFlow(self, flow):
        """
        Adds a flow to the network if it doesn't already exist.

        Args:
            flow (Flow): The flow to be added.
        """
        if self.getFlow(flow.src, flow.dst) is None:
            self.flows.append(flow)

    def getFlow(self, src, dst):
        """
        Gets the flow from the source to the destination node.

        Args:
            src (str): The source node.
            dst (str): The destination node.

        Returns:
            Flow: The flow between the two nodes, or None if no flow exists.
        """
        for flow in self.flows:
            if flow.src == src and flow.dst == dst:
                return flow
        return None

    def setLinkIdleSlope(self, src, dst, idleSlope):
        """
        Sets the idle slope of the link between the source and destination nodes.

        Args:
            src (str): The source node.
            dst (str): The destination node.
            idleSlope (float): The idle slope of the link.
        """
        link = self.getLink(src, dst)
        if link is not None:
            link.idleSlope = idleSlope

    def calculateLinkIdleSlopesFromFlows(self, cmi):
        """
        (Re-)calculates the idle slopes for all links based on the flows in the network.
        Assumes that all registered flows have the same priority / class.
        """
        for link in self.links:
            idleSlope = 0
            for flow in self.flows:
                path = self.lookupPath(flow.src, flow.dst)
                for l in path.links:
                    if l.isLinkFor(link.src, link.dst):
                        idleSlope += (flow.size * 8 + self.IFG) / cmi
            if idleSlope > link.rate:
                print("Warning: Idle slope exceeds link speed for link " + str(link) + ".")
            link.idleSlope = idleSlope

    def getInputIdleSlopes(self, link):
        """
        Gets the idle slopes of all input links for the specified link.

        Args:
            link (Link): The link to check.

        Returns:
            dict: A dictionary containing the idle slopes of all input links.
        """
        inputIdleSlopes = []
        for l in self.links:
            if l.src != link.dst and l.dst == link.src:
                inputIdleSlopes.append(l.idleSlope)
        return inputIdleSlopes

    def findClassMaxFrame(self):
        """
        Finds the maximum frame size of all flows in the network.
        Assumes that all registered flows have the same priority / class.

        Returns:
            int: The maximum frame size of all flows in byte in the network.
        """
        maxFrame = 0
        for flow in self.flows:
            if flow.size > maxFrame:
                maxFrame = flow.size
        return maxFrame

    def existsFlowOnLink(self, link):
        """
        Checks if a priority flow exists on the given link.

        Args:
            link (Link): The link to check.

        Returns:
            bool: True if a flow exists on the link, False otherwise.
        """
        for flow in self.flows:
            path = self.findPath(flow.src, flow.dst)
            for l in path.links:
                if l.isLinkFor(link.src, link.dst):
                    return True
        return False

    def getNumInputLinks(self, link, onlyCountLinksWithFlows=False):
        """
        Calculates the number of input links for the specified link.

        Args:
            link (Link): The link to check.
            onlyCountLinksWithFlows (bool, optional): If True, only counts links with known priority flows. Defaults to False.

        Returns:
            int: The number of input links for the specified link.
        """
        count = 0
        for l in self.links:
            if (
                l.src != link.dst  # same link but reverse direction so don't count it
                and l.dst == link.src  # is input link
                and (not onlyCountLinksWithFlows or self.existsFlowOnLink(l))  # verify only count if it has flows
            ):
                count += 1
        return count
