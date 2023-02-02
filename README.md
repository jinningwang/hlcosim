# Hardware Testbed and Large-scale Testbed Co-simulation based Hardware in Loop Simulation

## Overview

**H**ardware **T**est**B**ed and **L**arge-scale **T**est**B**ed Co-Simulation (HLTB Co-Sim) is a real-time hybrid EMT-phasor simulation for Hardware in Loop (HIL) Simulation.

## Background

**H**ardware **T**est**B**ed (HTB) is a power electronic-based power system emulators[^1], and **L**arge-scale **T**est**B**ed (LTB) [^2][^3][^4] is a large-scale power system simulation that can be used as virtual grid or digital twin of a real power grid.

## HTB-LTB Co-Simulation Operation Procedure

The LTB part should be started first:

1. In an Anaconda Terminal (windows start menu), change the path to the LTB path (``cd $HOME:\hlcosim\ltb``)
1. Activate the ANDES environment by ``conda activate andes``
1. Open Jupyter Notebook by ``jupyter notebook``
1. In the Jupyter Notebook (usually hosted in a web browser), open the code file ``htb.ipynb``
1. Click the "Cell" button in the menu bar, then click ``Run all`` and wait unitl LTB is ready
1. Then the HTB part is good to go

Stop LTB:

Click the "Kernel" button in the menu bar, then click ``Interrupt`` to stop the running code.

Restart LTB:

To restart the program for another test, click ``Restart and run all``

[^1]: L. M. Tolbert et al., "Reconfigurable Real-Time Power Grid Emulator for Systems With High Penetration of Renewables," in IEEE Open Access Journal of Power and Energy, vol. 7, pp. 489-500, 2020, doi: [10.1109/OAJPE.2020.3030219](https://ieeexplore.ieee.org/document/9220900).

[^2]: F. Li, K. Tomsovic and H. Cui, "A Large-Scale Testbed as a Virtual Power Grid: For Closed-Loop Controls in Research and Testing," in IEEE Power and Energy Magazine, vol. 18, no. 2, pp. 60-68, March-April 2020, doi: [10.1109/MPE.2019.2959054](https://ieeexplore.ieee.org/document/9007798).

[^3]: H. Cui, F. Li and K. Tomsovic, "Hybrid Symbolic-Numeric Framework for Power System Modeling and Analysis," in IEEE Transactions on Power Systems, vol. 36, no. 2, pp. 1373-1384, March 2021, doi: [10.1109/TPWRS.2020.3017019](https://ieeexplore.ieee.org/document/9169830).

[^4]: Parsly, N., Wang, J., West, N., Zhang, Q., Cui, H., & Li, F. (2022). "DiME and AGVIS A Distributed Messaging Environment and Geographical Visualizer for Large-scale Power System Simulation". arXiv 2022, doi: [arXiv:2211.11990](https://arxiv.org/abs/2211.11990)
