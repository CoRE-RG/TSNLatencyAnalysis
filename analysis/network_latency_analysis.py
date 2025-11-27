################################################################################################
# File: network_latency_analysis.py
# Description: This file contains the code to calculate the network latency for a given network
#              topology, flows and CBS IdleSlope.
# Author: Timo Salomon
#
# Copyright (C) 2025 Timo Salomon, for HAW Hamburg, Germany
#
# This file is licensed under the GNU Lesser General Public License v3.0 or later.
# You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <https://www.gnu.org/licenses/lgpl-3.0.html>
# SPDX-License-Identifier: LGPL-3.0-or-later
################################################################################################

import datetime
import os
import sys

modulePath = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if modulePath not in sys.path:
    sys.path.append(modulePath)

from analysis.network_components import *
from analysis.latency_calculation_cbs import *


class NetworkLatencyAnalysis:
    """
    Base Class for analyzing network latency in different scenarios.

    Attributes:
        network (Network): The network to analyze.
        calculator (CBSLatencyCalculator): The calculator to calculate the latency.
        switchDelay (float): The delay for a switch.
        ifg (int): The Inter Frame Gap.
    """

    def __init__(
        self,
        linkspeed=100000000.0,  # 100 Mbit/s
        cmi=125 * 10 ** (-1 * 6),  # default for class A 125 microseconds
        switch_delay=0,  # 0 seconds
        min_packet_bytes=64,
        max_packet_bytes=1526,  # not including IFG
        ifg_bits=96,
    ):
        """
        Initializes the NetworkLatencyAnalysis.

        Args:
            linkspeed (float, optional): The link speed in bits per second. Defaults to 100Mbit/s.
            cmi (float, optional): The CBS CMI. Defaults to 125us.
            switch_delay (float, optional): The delay for a switch. Defaults to 0s.
            min_packet_bytes (int, optional): The minimum packet size in bytes. Defaults to 64Byte.
            max_packet_bytes (int, optional): The maximum packet size in bytes, NOT including IFG. Defaults to 1526Byte.
            ifg_bits (int, optional): The Inter Frame Gap in bits. Defaults to 96.
        """
        self.network = Network(bridges=[], nodes=[], links=[], flows=[], paths=[], IFG=ifg_bits)
        self.calculator = CBSLatencyCalculator(linkspeed, cmi, min_packet_bytes, max_packet_bytes, ifg_bits)
        self.linkspeed = linkspeed
        self.cmi = cmi
        self.switchDelay = switch_delay
        self.ifg = ifg_bits

    def calculateQueueDelayForLink(self, link, flow, classMaxFrame=-1):
        """
        Collects the queue delays from all formulas for the specified link and flow.

        Args:
            link (Link): The link to calculate the queue delays for.
            flow (Flow): The flow to calculate the queue delays for.
            classMaxFrame (int): The maximum frame size in bits of all priority flows in the network (should include IFG).

        Returns:
            dict: A dictionary containing the queue delays for all formulas.
        """
        if link.src in self.network.nodes:
            return self.calculator.getEmptyResultDict()
        if classMaxFrame == -1:
            classMaxFrame = self.network.findClassMaxFrame() * 8 + self.ifg
        streamMaxFrame = flow.size * 8 + self.ifg
        inputIdleSlopes = self.network.getInputIdleSlopes(link)
        nrInputLinks = self.network.getNumInputLinks(link)
        ## TODO check if we can ignore links that do not have priority flows?
        # nrInputLinksWSRClass = self.network.getNumInputLinks(link, True)
        return self.calculator.runAlgorithmsForPort(
            link.idleSlope, streamMaxFrame, classMaxFrame, nrInputLinks, inputIdleSlopes
        )

    def calculateEndToEndDelayForFlow(self, flow):
        """
        Calculates the delay for the specified flow for all formulas.
        Includes queueing, forwarding and transmission delay.
        For the traffic source only the transmission delay is considered.

        Args:
            flow (Flow): The flow to calculate the delay for.

        Returns:
            dict: A dictionary containing the aggregated delay for the flow for all formulas.
        """
        classMaxFrame = self.network.findClassMaxFrame() * 8 + self.ifg
        flowDelay = self.calculator.getEmptyResultDict()
        transmissionDelay = (flow.size * 8 + self.ifg) / self.linkspeed
        path = self.network.lookupPath(flow.src, flow.dst)
        if path is not None:
            for link in path.links:
                result = self.calculateQueueDelayForLink(link, flow, classMaxFrame)
                for key in result:
                    flowDelay[key] = flowDelay[key] + result[key] + transmissionDelay
                    if link.src in self.network.bridges:
                        flowDelay[key] += self.switchDelay
        return flowDelay

    def calculateEndToEndDelays(self, useFlowIntervalAsCMI=False):
        """
        Collects the delay for all flows in the network for all formulas.

        Args:
            useFlowIntervalAsCMI (bool, optional): If True, uses the flow interval as CMI. Defaults to False.

        Returns:
            dict: A dictionary containing the delay for all flows for all formulas.
        """
        perFlowDelay = dict()
        for flow in self.network.flows:
            if useFlowIntervalAsCMI:
                self.calculator.setCMI(flow.period)
            perFlowDelay[flow] = self.calculateEndToEndDelayForFlow(flow)
        if useFlowIntervalAsCMI:
            # reset CMI to default value
            self.calculator.setCMI(self.cmi)
        return perFlowDelay

    def getHeader(self, resultCols):
        """
        Returns the header for the CSV file.

        Returns:
            str: The header for the CSV file.
        """
        resultHeaderColumns = ", ".join(resultCols)
        return "ExecutionTime, Flow, " + resultHeaderColumns

    def getResultLine(self, result, flow, resultCols, additionalValues=dict()):
        """
        Returns the result line for the CSV file.

        Args:
            result (dict): The result to write to the CSV file.
            flow (Flow): The flow to write to the CSV file.
            resultCols (dict): The columns of the results, including columns for additional values.
            additionalValues (dict, optional): Additional values to add to the results. Defaults to dict().

        Returns:
            str: The result line for the CSV file.
        """
        resultLine = str(datetime.datetime.now()) + ", " + str(flow.src) + "-" + str(flow.dst)
        for key in resultCols:
            resultLine += ", "
            if key in additionalValues.keys():
                resultLine += str(additionalValues[key])
            elif key in result:
                resultLine += f"{result[key]:.6f}"
        return resultLine

    def writeToCsv(self, fileName, results, resultCols, additionalValues=dict()):
        """
        Writes the results to a CSV file.

        Args:
            fileName (str): The name of the CSV file.
            results (dict(dict)): The result rows to write to the CSV file.
            resultCols (dict): The columns of the results, including columns for additional values.
            additionalValues (dict, optional): Additional values to add to the results. Defaults to dict().
        """
        writeHeader = False
        if not os.path.isfile(fileName):
            writeHeader = True
        with open(fileName, "a+") as file:
            if writeHeader:
                file.write(self.getHeader(resultCols) + "\n")
            for flow in results:
                resultLine = self.getResultLine(results[flow], flow, resultCols, additionalValues)
                file.write(resultLine + "\n")
