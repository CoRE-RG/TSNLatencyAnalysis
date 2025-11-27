################################################################################################
# File: UnlimetedBurstRecursion.py
# Description: This file is a reproduction of the unlimited burst recursion scenario from
#              the paper
#              Lisa Maile et al., "On the Validity of Credit-Based Shaper Delay Guarantees in
#              Decentralized Reservation Protocols," in the 31st International Conference on
#              Real-Time Networks and Systems (RTNS 2023), ACM, 2023.
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
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from analysis.network_latency_analysis import *
from analysis.network_components import *
from analysis.latency_calculation_cbs import *

CMI = 125 * 10 ** (-1 * 6)  # for class A 125 microseconds
LINK_SPEED = 100000000.0  # 100 Mbit/s
SWITCH_DELAY = 8 * 10 ** (-6)  # 8 microseconds
IFG = 96  # 96 bit interframe gap


class ExceedLatencyLvl0(NetworkLatencyAnalysis):

    def __init__(self):
        super().__init__(linkspeed=LINK_SPEED, cmi=CMI, switch_delay=SWITCH_DELAY)  # , max_packet_bytes=748)
        self.addNodes()
        self.addBridges()
        self.createLinks()
        self.addFlowsAndPaths()

    def addNodes(self):
        """
        Helper function to add nodes to the small network for evaluation.
        """
        self.network.addNode("GenFoi")
        self.network.addNode("GenBELeft")
        self.network.addNode("GenBeRight")
        self.network.addNode("SinkLeft")
        self.network.addNode("SinkRight")
        self.network.addNode("GenLeft")
        self.network.addNode("GenRight")
        self.network.addNode("SinkFinal")

    def addBridges(self):
        """
        Helper function to add bridges to the small network for evaluation.
        """
        self.network.addBridge("swtLeft")
        self.network.addBridge("swtRight")

    def createLinks(self):
        """
        Helper function to set up the small network for evaluation.
        """
        self.network.addBidirectionalLink("swtLeft", "swtRight", LINK_SPEED, SWITCH_DELAY, 0)
        self.network.addBidirectionalLink("GenFoi", "swtLeft", LINK_SPEED, SWITCH_DELAY, 0)
        self.network.addBidirectionalLink("GenBELeft", "swtLeft", LINK_SPEED, SWITCH_DELAY, 0)
        self.network.addBidirectionalLink("GenBeRight", "swtRight", LINK_SPEED, SWITCH_DELAY, 0)
        self.network.addBidirectionalLink("SinkLeft", "swtLeft", LINK_SPEED, SWITCH_DELAY, 0)
        self.network.addBidirectionalLink("SinkRight", "swtRight", LINK_SPEED, SWITCH_DELAY, 0)
        self.network.addBidirectionalLink("GenLeft", "swtLeft", LINK_SPEED, SWITCH_DELAY, 0)
        self.network.addBidirectionalLink("GenRight", "swtRight", LINK_SPEED, SWITCH_DELAY, 0)
        self.network.addBidirectionalLink("SinkFinal", "swtRight", LINK_SPEED, SWITCH_DELAY, 0)

    def addFlowsAndPaths(self):
        """
        Helper function to add flows and paths to the small network for evaluation.
        """
        # foi
        flowFoi = Flow("GenFoi", "SinkFinal", 370, 0.001, 0.000125, 7)
        pathFoi = Path("GenFoi", "SinkFinal", [])
        pathFoi.addLinks(self.network.getLink("GenFoi", "swtLeft"))
        pathFoi.addLinks(self.network.getLink("swtLeft", "swtRight"))
        pathFoi.addLinks(self.network.getLink("swtRight", "SinkFinal"))
        self.network.addFlow(flowFoi)
        self.network.addPath(pathFoi)
        # xf_1
        flowXF1 = Flow("GenLeft", "SinkRight", 370, 0.001, 0.005, 7)
        pathXF1 = Path("GenLeft", "SinkRight", [])
        pathXF1.addLinks(self.network.getLink("GenLeft", "swtLeft"))
        pathXF1.addLinks(self.network.getLink("swtLeft", "swtRight"))
        pathXF1.addLinks(self.network.getLink("swtRight", "SinkRight"))
        self.network.addFlow(flowXF1)
        self.network.addPath(pathXF1)
        # xf_2
        flowXF2 = Flow("GenRight", "SinkFinal", 370, 0.001, 0.005, 7)
        pathXF2 = Path("GenRight", "SinkFinal", [])
        pathXF2.addLinks(self.network.getLink("GenRight", "swtRight"))
        pathXF2.addLinks(self.network.getLink("swtRight", "SinkFinal"))
        self.network.addFlow(flowXF2)
        self.network.addPath(pathXF2)

    def setLinkIdleSlopes(self, idleSlope):
        """
        Helper function to set the idle slopes for the small network for evaluation.
        Simplified as each link has the same idle slope.
        """
        self.network.setLinkIdleSlope("GenFoi", "swtLeft", idleSlope)
        self.network.setLinkIdleSlope("GenLeft", "swtLeft", idleSlope)
        self.network.setLinkIdleSlope("GenRight", "swtRight", idleSlope)
        self.network.setLinkIdleSlope("swtLeft", "swtRight", idleSlope)
        self.network.setLinkIdleSlope("swtLeft", "SinkLeft", idleSlope)
        self.network.setLinkIdleSlope("swtRight", "SinkFinal", idleSlope)
        self.network.setLinkIdleSlope("swtRight", "SinkRight", idleSlope)

    def runStudy(self):
        filename = "maxLatenciesExceedLatencyLvl0.csv"
        if os.path.exists(filename):
            os.remove(filename)

        self.setLinkIdleSlopes(50000000)
        results = self.calculateEndToEndDelays()
        resultCols = [
            "Name",
            "qStandardL3V1",
            "qStandardL3V2",
            "qStandardL3V3",
        ]
        additionalValues = {
            "Name": "Lvl 0 total latency",
        }
        self.writeToCsv(filename, results, resultCols, additionalValues)

        classMaxFrame = self.network.findClassMaxFrame() * 8 + IFG
        flow = self.network.getFlow("GenFoi", "SinkFinal")

        resultS1 = dict()
        link = self.network.getLink("swtLeft", "swtRight")
        additionalValues["Name"] = "Lvl 0 Queue Switch1Left-Switch1Right"
        resultS1[flow] = self.calculateQueueDelayForLink(link, flow, classMaxFrame)
        self.writeToCsv(filename, resultS1, resultCols, additionalValues)

        resultS2 = dict()
        link = self.network.getLink("swtRight", "SinkFinal")
        additionalValues["Name"] = "Lvl 0 Queue Switch1Right-SinkFinal"
        resultS2[flow] = self.calculateQueueDelayForLink(link, flow, classMaxFrame)
        self.writeToCsv(filename, resultS2, resultCols, additionalValues)


def main():
    network = ExceedLatencyLvl0()
    network.runStudy()


if __name__ == "__main__":
    main()
