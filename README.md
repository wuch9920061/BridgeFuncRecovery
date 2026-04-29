# BridgeFuncRecovery
This project aims to probabilistically model the post-earthquake functional recovery of bridges. The source codes are programmed in Python.

### Reference
[1] Wu, C., Burton, H., Zsarnóczay, A., Chen. S., Xie. Y., Terzić, V., Günay, S., Padgett, J., Mieler, and M., Almufti, I. (2025). Modeling Post-earthquake Functional Recovery of Bridges. Earthquake Spectra. 

### Prerequisites
Python: version 3.6 or above.

Necessary Python packages: copy, numpy, pandas, os, scipy, sys, shutil, pathlib, re, time, pickle

### File Overview
*main_RunAnalysis.ipynb* takes user-specified parameters and performs the full analysis. 

*utilities_FunRec.py* provides auxiliary functions that are called from the main script *main.py*. 

*ResultPresent.ipynb* helps visualize the output data stored in *Results.pkl*. 

After running *main_RunAnalysis.ipynb*, a Results.pkl file is created that stores all model output data 



