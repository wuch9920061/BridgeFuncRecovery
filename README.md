# BridgeFuncRecovery
This project aims to probabilistically model the post-earthquake functional recovery of bridges. The source codes are programmed in Python.

### Reference
[1] Wu, C., Burton, H., Zsarnóczay, A., Chen. S., Xie. Y., Terzić, V., Günay, S., Padgett, J., Mieler, and M., Almufti, I. (2025). Modeling Post-earthquake Functional Recovery of Bridges. Earthquake Spectra. 

### Prerequisites
Python: version 3.6 or above.

Necessary Python packages: copy, numpy, pandas, os, scipy, sys, shutil, pathlib, re, time, pickle

### What is each file used for
*main_RunAnalysis.ipynb* inputs user-specified parameters, and performs the entire analysis. 

*utilities_FunRec.py* provides necessary auxiliary functions that is called from the main script *main_RunAnalysis.ipynb*. 

After running all cells in *main_RunAnalysis.ipynb*, a pickle file *Results.pkl* is stored that records model output data. 

*ResultPresent.ipynb* helps visualize the output data stored in *Results.pkl*. 


### User-specified inputs
All used-specified inputs should be provided by adjusting paramters  under the second cell (i.e., under the cell right below the markdown ##User Inputs) before running all follow-up cells to perform the analysis. 
