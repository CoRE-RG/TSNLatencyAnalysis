################################################################################################
# File: latency_calculation_cbs.py
# Description: Contains functions to calculate the worst-case queuing latency for a port
# Author: Timo Salomon
#
# Thanks to Lisa Maile, FAU Erlangen-Nürnberg, for the initial implementation of some queue delay formulas.
#
# Copyright (C) 2025 Timo Salomon, for HAW Hamburg, Germany
#
# This file is licensed under the GNU Lesser General Public License v3.0 or later.
# You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <https://www.gnu.org/licenses/lgpl-3.0.html>
# SPDX-License-Identifier: LGPL-3.0-or-later
################################################################################################

from math import floor, ceil


class CBSLatencyCalculator:
    """
    Class to calculate the worst-case queuing latency for a port

    Attributes:
        LINKSPEED: The speed of the link in bits per second
        CMI: The cycle time of the port in seconds
        IFG: The interframe gap in bits
        MIN_PACKET: The minimum packet size in bytes
        MIN_PACKET_BITS: The minimum packet size in bits
        MIN_PACKET_BITS_W_IFG: The minimum packet size in bits with interframe gap
        MAX_PACKET: The maximum packet size in bytes
        MAX_PACKET_BITS: The maximum packet size in bits
        MAX_PACKET_BITS_W_IFG: The maximum packet size in bits with interframe gap
        ctMaxFrame: The maximum frame size with interframe gap
    """

    def __init__(self, linkspeed, cmi, min_packet_bytes=64, max_packet_bytes=1526, ifg_bits=96):
        self.LINKSPEED = linkspeed
        self.CMI = cmi
        self.IFG = ifg_bits
        self.MIN_PACKET = min_packet_bytes
        self.MIN_PACKET_BITS = min_packet_bytes * 8
        self.MIN_PACKET_BITS_W_IFG = self.MIN_PACKET_BITS + ifg_bits
        self.MAX_PACKET = max_packet_bytes
        self.MAX_PACKET_BITS = max_packet_bytes * 8
        self.MAX_PACKET_BITS_W_IFG = self.MAX_PACKET_BITS + ifg_bits
        self.ctMaxFrame = self.MAX_PACKET_BITS_W_IFG

    def setCMI(self, cmi):
        """
        Set the CMI of the port

        Args:
            cmi: The cycle time of the port in seconds
        """
        self.CMI = cmi

    def baStandard(self, idleSlope, streamMaxFrame):
        """
        Calculate the worst-case queuing latency for a port according to the 802.1BA-2021 standard
            802.1BA-2021 https://ieeexplore.ieee.org/document/9653970
            See Section 6 Equation 6-1

        Args:
            idleSlope: The idle slope of the port in bits per second
            streamMaxFrame: The maximum frame size of the stream in bits
        """
        tMaxPacket = self.ctMaxFrame / self.LINKSPEED
        tStreamPacket = (streamMaxFrame - self.IFG) / self.LINKSPEED  # without IPG
        delayA = idleSlope * self.CMI / self.LINKSPEED
        tClassA = (delayA - streamMaxFrame / self.LINKSPEED) * self.LINKSPEED / idleSlope
        # tClass can be negative if idleSlope is calculated for a larger interval than CMI (e.g., flow interval)
        if (
            tClassA < 0
        ):  # TODO verify this, ignoring negative values (only happens when idle slope is calculated not according to standards)
            tClassA = 0
        # MaxLatency = tDevice + tMaxPacket + tClassA + tStreamPacket
        MaxLatency = tMaxPacket + tClassA + tStreamPacket
        return MaxLatency

    def qStandardL3V1(self, idleSlope, classMaxFrame, nrInputLinks):
        """
        Calculate the worst-case queuing latency for a port according to the 802.1Q-2022 standard
        This implementation assumes that permanent buffer delay is already included with the fan-in delay, which may not be correct.
            802.1Q-2022 https://ieeexplore.ieee.org/document/10004498
            See Annex L.3

        Args:
            idleSlope: The idle slope of the port in bits per second
            classMaxFrame: The maximum frame size of the class in bits
            nrInputLinks: The number of input links
        """
        qDelayStand = (
            self.ctMaxFrame / self.LINKSPEED
        )  # only one max frame on the way, as we assume we are the highest priority
        fan_in_data = 0
        B0 = idleSlope
        # we assume that the first link has everything
        for i in range(nrInputLinks):
            if B0 > 0:
                Bi = idleSlope
                W = self.LINKSPEED - max(B0, Bi)
                fan_in_data += (
                    self.ctMaxFrame * idleSlope * self.LINKSPEED / (W * self.LINKSPEED)
                    + classMaxFrame * self.LINKSPEED / W
                )
                B0 -= Bi
            else:
                fan_in_data += classMaxFrame
        fan_in_delay = fan_in_data / self.LINKSPEED
        maxDelayStandard = qDelayStand + fan_in_delay + classMaxFrame / self.LINKSPEED
        return maxDelayStandard

    def qStandardL3V2(self, idleSlope, classMaxFrame, inputIdleSlopes):
        """
        Calculate the worst-case queuing latency for a port according to the 802.1Q-2022 standard
        This implementation includes both fan-in delay and permanent buffer delay.
            802.1Q-2022 https://ieeexplore.ieee.org/document/10004498
            See Annex L.3

        Args:
            idleSlope: The idle slope of the port in bits per second
            classMaxFrame: The maximum frame size of the class in bits
            inputIdleSlopes: The incoming idle slopes of the input ports in bits per second
        """
        queueing_delay = (
            self.ctMaxFrame / self.LINKSPEED
        )  # only one max frame on the way, as we assume we are the highest priority
        fan_in_data = 0
        B0 = idleSlope
        for Bi in inputIdleSlopes:
            if B0 > 0:
                W = self.LINKSPEED - max(B0, Bi)
                # fan_in_data += ctMaxFrame * idleSlope * self.LINKSPEED / (W * self.LINKSPEED) + classMaxFrame * self.LINKSPEED / W
                fan_in_data += (self.ctMaxFrame * idleSlope / W) + (classMaxFrame * self.LINKSPEED / W)
                B0 -= Bi
            else:
                fan_in_data += classMaxFrame
        fan_in_delay = fan_in_data / self.LINKSPEED
        # permanent_delay = classMaxFrame / self.LINKSPEED # this is not enough!
        # permanent buffer occupancy occurs when bridges are starved and then a burst occurs due to queueing delay (see 3.1.3)
        # Since this kind of event could happen on multiple input ports at the same time, the “permanently buffered” data equals the worst-case fan-in data.
        permanent_delay = fan_in_delay
        maxDelayStandard = queueing_delay + fan_in_delay + permanent_delay
        return maxDelayStandard

    def getMaxReservedPlenary(self, idleSlope):
        """
        Calculate the maximum reserved packet according to the plenary discussions
            https://www.ieee802.org/1/files/public/docs2009/av-fuller-queue-delay-calculation-0809-v02.pdf

        Args:
            idleSlope: The idle slope of the port in bits per second
        """
        # return np.floor(CMI / (1/self.LINKSPEED) * (idleSlope / self.LINKSPEED))
        return floor(self.CMI * idleSlope)

    def plenary100Mbit(self, idleSlope, streamMaxFrame, nrInputLinks):
        """
        Calculate the worst-case queuing latency for a port according to the plenary discussions for 100 Mbit/s Media
            https://www.ieee802.org/1/files/public/docs2009/av-fuller-queue-delay-calculation-0809-v02.pdf
            see Fast Ethernet (100 Mb) Media

        Args:
            idleSlope: The idle slope of the port in bits per second
            streamMaxFrame: The maximum frame size of the stream in bits
            nrInputLinks: The number of input links
        """
        maxReserved = self.getMaxReservedPlenary(idleSlope)
        N = min(
            nrInputLinks - 1,
            floor((maxReserved - streamMaxFrame) / self.MIN_PACKET_BITS_W_IFG),
        )
        otherPackets = 0
        if N > 0:
            otherPackets = 2 * (maxReserved - streamMaxFrame) - ceil((maxReserved - streamMaxFrame) / N)
        qDelayOctets = self.ctMaxFrame + otherPackets + streamMaxFrame
        qDelay = qDelayOctets / self.LINKSPEED
        return qDelay

    def plenaryFasterMedia(self):
        """
        Calculate the worst-case queuing latency for a port according to the plenary discussions for Gigabit Ethernet and Faster Media
            https://www.ieee802.org/1/files/public/docs2009/av-fuller-queue-delay-calculation-0809-v02.pdf
            see Gigabit Ethernet and Faster Media

        Args:
            idleSlope: The idle slope of the port in bits per second
            streamMaxFrame: The maximum frame size of the stream in bits
        """
        # maxReserved = self.getMaxReservedPlenary(idleSlope)
        # qDelayFaster = maxReserved / (self.LINKSPEED * idleSlope/self.LINKSPEED) + ctMaxFrame / self.LINKSPEED
        qDelayFaster = self.CMI + self.ctMaxFrame / self.LINKSPEED
        return qDelayFaster

    def plenaryFasterMediaV2(self, idleSlope, streamMaxFrame):
        """
        Calculate the worst-case queuing latency for a port according to the plenary discussions for Gigabit Ethernet and Faster Media (Version 2)
            https://www.ieee802.org/1/files/public/docs2009/av-fuller-queue-delay-calculation-0809-v02.pdf
            see Gigabit Ethernet and Faster Media (Version 2)

        Args:
            idleSlope: The idle slope of the port in bits per second
            streamMaxFrame: The maximum frame size of the stream in bits
        """
        maxReserved = self.getMaxReservedPlenary(idleSlope)
        N = self.LINKSPEED / 100000000  # linkrate_graph / 100Mbps
        streamBits = ceil((maxReserved - streamMaxFrame) / N)
        # streamBits can be negative if idleSlope is calculated for a larger interval than CMI (e.g., flow interval)
        if (
            streamBits < 0
        ):  # TODO verify this, ignoring negative values (only happens when idle slope is calculated not according to standards)
            streamBits = 0
        sendSlope = idleSlope - self.LINKSPEED
        loCredit = streamBits * sendSlope / self.LINKSPEED
        hiCredit = self.ctMaxFrame * idleSlope / self.LINKSPEED
        maxBurstSize = self.LINKSPEED * (loCredit - hiCredit) / sendSlope
        maxBurstTime = (loCredit - hiCredit) / sendSlope
        totalBitsQueued = N * maxBurstSize + floor(maxBurstTime / self.CMI) * streamMaxFrame
        qDelayFasterV2 = (
            (totalBitsQueued / idleSlope)
            - (maxBurstTime - (streamBits / self.LINKSPEED))
            + self.ctMaxFrame / self.LINKSPEED
        )
        return qDelayFasterV2

    def runAlgorithmsForPort(self, idleSlope, streamMaxFrame, classMaxFrame, nrInputLinks, inputIdleSlopes):
        """
        Run all algorithms for a port and return the results as a dictionary

        Args:
            idleSlope: The idle slope of the port in bits per second
            streamMaxFrame: The maximum frame size of the stream in bits
            nrInputLinks: The number of input links
            inputIdleSlopes: The incoming idle slopes of the input ports in bits per second

        Returns:
            A dictionary containing the results of all algorithms with the algorithm function name as key
        """
        inputIdleSlopesSorted = sorted(inputIdleSlopes)
        results = {}
        results["baStandard"] = self.baStandard(idleSlope, streamMaxFrame)
        results["qStandardL3V1"] = self.qStandardL3V1(idleSlope, classMaxFrame, nrInputLinks)
        results["qStandardL3V2"] = self.qStandardL3V2(idleSlope, classMaxFrame, inputIdleSlopesSorted)
        results["plenary100Mbit"] = self.plenary100Mbit(idleSlope, streamMaxFrame, nrInputLinks)
        results["plenaryFasterMedia"] = self.plenaryFasterMedia()
        results["plenaryFasterMediaV2"] = self.plenaryFasterMediaV2(idleSlope, streamMaxFrame)
        inputIdleSlopesSorted.reverse()
        results["qStandardL3V3"] = self.qStandardL3V2(idleSlope, classMaxFrame, inputIdleSlopesSorted)
        return results

    def getEmptyResultDict(self):
        """
        Get an empty result dictionary with all algorithms as keys delay values set to zero

        Returns:
            A dictionary containing the results of all algorithms with the algorithm function name as key
        """
        return {
            "baStandard": 0,
            "qStandardL3V1": 0,
            "qStandardL3V2": 0,
            "plenary100Mbit": 0,
            "plenaryFasterMedia": 0,
            "plenaryFasterMediaV2": 0,
            "qStandardL3V3": 0,
        }
