################################################################################################
# File: TSSDNSOASmallNetwork.py
# Description: Evaluation of the small network for the TSSDN SOA from SDN4CoRE simulation model.
# Author: Timo Salomon
#
# Copyright (C) 2025 Timo Salomon, for HAW Hamburg, Germany
#
# This file is licensed under the GNU Lesser General Public License v3.0 or later.
# You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <https://www.gnu.org/licenses/lgpl-3.0.html>
# SPDX-License-Identifier: LGPL-3.0-or-later
################################################################################################

import os
import sys

modulePath = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if modulePath not in sys.path:
    sys.path.append(modulePath)
from analysis.latency_calculation_cbs import *
from analysis.network_latency_analysis import *
from analysis.network_components import *

CMI = 125 * 10 ** (-1 * 6)  # for class A 125 microseconds
LINK_SPEED = 100000000.0  # 100 Mbit/s
SWITCH_DELAY = 8 * 10 ** (-6)  # 8 microseconds


class SmallEvalNetworkReducedPayload(NetworkLatencyAnalysis):

    def __init__(self):
        super().__init__(linkspeed=LINK_SPEED, cmi=CMI, switch_delay=SWITCH_DELAY)
        self.addNodes()
        self.addBridges()
        self.createLinks()
        self.addFlowsAndPaths()

    def addNodes(self):
        """
        Helper function to add nodes to the small network for evaluation.
        """
        self.network.addNode("N0")
        self.network.addNode("N1")
        self.network.addNode("N2")
        self.network.addNode("N3")
        self.network.addNode("CT0")
        self.network.addNode("CT1")

    def addBridges(self):
        """
        Helper function to add bridges to the small network for evaluation.
        """
        self.network.addBridge("S0")
        self.network.addBridge("S1")
        self.network.addBridge("S2")

    def createLinks(self):
        """
        Helper function to set up the small network for evaluation.
        """
        self.network.addBidirectionalLink("S0", "S1", LINK_SPEED, SWITCH_DELAY)
        self.network.addBidirectionalLink("S1", "S2", LINK_SPEED, SWITCH_DELAY)
        self.network.addBidirectionalLink("N0", "S0", LINK_SPEED, SWITCH_DELAY)
        self.network.addBidirectionalLink("N1", "S1", LINK_SPEED, SWITCH_DELAY)
        self.network.addBidirectionalLink("N2", "S2", LINK_SPEED, SWITCH_DELAY)
        self.network.addBidirectionalLink("N3", "S1", LINK_SPEED, SWITCH_DELAY)
        self.network.addBidirectionalLink("CT0", "S0", LINK_SPEED, SWITCH_DELAY)
        self.network.addBidirectionalLink("CT1", "S2", LINK_SPEED, SWITCH_DELAY)

    def addFlowsAndPaths(self):
        """
        Helper function to add flows and paths to the small network for evaluation.
        """
        flow = Flow("N0", "N2", 750, 0.001, 0.001, 7)
        path = Path("N0", "N2")
        path.addLinks(self.network.getLink("N0", "S0"))
        path.addLinks(self.network.getLink("S0", "S1"))
        path.addLinks(self.network.getLink("S1", "S2"))
        path.addLinks(self.network.getLink("S2", "N2"))
        self.network.addFlow(flow)
        self.network.addPath(path)

    def setLinkIdleSlopes(self, idleSlope):
        """
        Helper function to set the idle slopes for the small network for evaluation.
        Simplified as each link has the same idle slope.
        """
        self.network.setLinkIdleSlope("N0", "S0", idleSlope)
        self.network.setLinkIdleSlope("S0", "S1", idleSlope)
        self.network.setLinkIdleSlope("S1", "S2", idleSlope)
        self.network.setLinkIdleSlope("S2", "N2", idleSlope)

    def runStudy(self, useFlowIntervalAsCMI=False):

        idleSlopes = {
            "FixedCMI": 48832000,
            "FlowRate": 6144000,
            "NCMin": 52120383,
            "NCMax": 70101196,
        }

        resultCols = [
            "Name",
            "Idle Slope",
            "Flow Interval as CMI",
            "baStandard",
            "qStandardL3V2",
            "plenary100Mbit",
            "plenaryFasterMedia",
            "plenaryFasterMediaV2",
        ]
        # remove old file
        if os.path.exists("maxLatenciesSmallEvalNetworkReducedPayload.csv"):
            os.remove("maxLatenciesSmallEvalNetworkReducedPayload.csv")
        for key in idleSlopes:
            additionalValues = {
                "Name": key,
                "Idle Slope": idleSlopes[key],
                "Flow Interval as CMI": str(useFlowIntervalAsCMI),
            }
            self.setLinkIdleSlopes(idleSlopes[key])
            results = self.calculateEndToEndDelays()
            self.writeToCsv("maxLatenciesSmallEvalNetworkReducedPayload.csv", results, resultCols, additionalValues)


## main function setting up the network and calling the algorithms
def main():
    network = SmallEvalNetworkReducedPayload()
    network.runStudy()


if __name__ == "__main__":
    main()
