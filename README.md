# TSN Latency Analysis
This project implements some TSN standard formulas (e.g., from 802.1Q-2022) and a small framework to enable latency analysis of queues in a TSN network using Credit Based Shapers (CBS).
Note: none of these formulas actually provides a worst-case latency which has been shown in various works (e.g., see references).

## References
If you use this project please add the following [reference](https://doi.org/10.1016/j.vehcom.2025.100985)
> T. Salomon, L. Maile, P. Meyer, F. Korf, T. C. Schmidt, "Negotiating Strict Latency Limits for Dynamic Real-Time Services in Vehicular Time-Sensitive Networks," Vehicular Communications, Elsevier, 2025. (in press)
```bibtex
@Article{smmks-nslld-25,
  author = {Salomon, Timo and Maile, Lisa and Meyer, Philipp and Korf, Franz and Schmidt, Thomas C.},
  title  = {{Negotiating Strict Latency Limits for Dynamic Real-Time Services in Vehicular Time-Sensitive Networks}},
  journal = {Vehicular Communications},
  pages = {},
  volume = {},
  number = {},
  year = {2025},
  month = {},
  nope= "In Press",
  publisher = {Elsevier},
  doi   = {10.1016/j.vehcom.2025.100985},
}
```

Some formulas have been previously used in the [paper](https://doi.org/10.1145/3575757.3593644):
> L. Maile, D. Voitlein, A. Grigorjew, K.-S. Hielscher, and R. German, "On the Validity of Credit-Based Shaper Delay Guarantees in Decentralized Reservation Protocols," in 31st International Conference on Real-Time Networks and Systems (RTNS), in RTNS ’23. ACM, Jun. 2023, pp. 108–118. doi: 10.1145/3575757.3593644.
```bibtex
@InProceedings{maile_decentral_2023,
  author    = {Maile, Lisa and Voitlein, Dominik and Grigorjew, Alexej and Hielscher, Kai-Steffen and German, Reinhard},
  booktitle = {31st International Conference on Real-Time Networks and Systems (RTNS)},
  title     = {{On the Validity of Credit-Based Shaper Delay Guarantees in Decentralized Reservation Protocols}},
  year      = {2023},
  month     = jun,
  pages     = {108--118},
  publisher = {ACM},
  series    = {RTNS '23},
  doi       = {10.1145/3575757.3593644},
}
```

## Project
analysis/ contains generalized code to setup a network, flows, and queues, and to calculate worst-case latencies with different formulas.
scenarios/ contains scenarios, including specific network topology and flows to calculate their worst-case latencies.

## Authors
* Timo Salomon, for HAW Hamburg
* Thanks to Lisa Maile, FAU Erlangen-Nürnberg, for the initial implementation of some queue delay formulas.

## Status
The project has been tested on Ubuntu 22.04 (+WSL) and Windows 11. 

## License
LGPL v3.0 see LICENSE

## IMPORTANT
This framework is work in progress: new parts may be added, bugs are corrected, and so on. We cannot assert that the implementation will work fully according to the specifications. YOU ARE RESPONSIBLE YOURSELF TO MAKE SURE THAT THE MODELS YOU USE WORK CORRECTLY, AND YOU'RE GETTING VALID RESULTS.
