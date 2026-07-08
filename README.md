# fr4Bridge (Functional Recovery assessment For Bridge)
A Python-based Monte Carlo simulation framework for assessing the post-earthquake functional recovery of highway bridges. The framework integrates bridge-specific seismic fragility, system functionality, impeding factors, and repair/replacement processes to estimate bridge recovery trajectories following a seismic event.

### Reference
[1] Wu, C., Burton, H., Zsarnóczay, A., Chen. S., Xie. Y., Terzić, V., Günay, S., Padgett, J., Mieler, and M., Almufti, I. (2025). Modeling Post-earthquake Functional Recovery of Bridges. Earthquake Spectra, 41(3), pp.2089-2122.

### Prerequisites
Python: version 3.6 or above.
Necessary Python packages: copy, numpy, pandas, os, scipy, sys, shutil, pathlib, re, time, pickle

### Workflow
This framework estimates the recovery process of an individual bridge subjected to a specified earthquake intensity measure (IM) which currently only support spectral acceraltion at 1s (Sa(1s)). For each Monte Carlo realization, the workflow:

1. Samples correlated component damage states using bridge-specific fragility functions.
2. Determines bridge-level repair class and system damage state.
3. Assigns immediate post-earthquake functionality.
4. Samples impeding factors (e.g., inspections, financing, permitting).
5. Samples repair or replacement duration.
6. Determines reopening functionality during recovery.
7. Computes the overall functional recovery timeline.

### File Overview

*main_RunAnalysis.ipynb* serves as the primary analysis script. It accepts user-defined bridge characteristics, analysis settings, and recovery assumptions, then performs the complete Monte Carlo simulation to evaluate the post-earthquake functional recovery process of a bridge.

*utilities_FunRec.py* contains the auxiliary functions called by *main_RunAnalysis.ipynb*. These functions implement bridge classification, fragility assignment, correlated damage sampling, functionality assessment, impeding-factor simulation, repair and replacement duration modeling, and recovery sequencing.

*FRA_LIB.pkl* stores the bridge fragility library. Based on the user-specified bridge class, the corresponding component fragility functions are automatically retrieved and incorporated into the recovery analysis.

After running *main_RunAnalysis.ipynb*, a `Results.pkl` file is generated that stores all simulation outputs, including sampled component damage states, functionality states, impeding factors, repair/replacement durations, and bridge recovery trajectories. These outputs can subsequently be visualized and post-processed using *ResultPresent.ipynb*.


## Supported Bridge Classes

The framework supports multiple bridge classes using the following naming convention:

```text
Era-Span-Bent-ColumnShape-Abutment
```

For example,

```text
E3-S3P-C3P-O-S
```

represents a post-1990 bridge with more than two spans, more than two columns per bent, oblong columns, and seat-type abutments.

The meaning of each field is summarized below.

| Field | Options | Description |
| :--- | :--- | :--- |
| **Era** | `E1`, `E2`, `E3` | Bridge design era (`E1`: pre-1970, `E2`: 1970–1990, `E3`: post-1990) |
| **Span** | `S1`, `S2`, `S3P` | Number of spans (`S3P` = more than two spans) |
| **Bent** | `NA`, `C1`, `C2`, `C3P` | Number of columns per bent (`NA` for single-span bridges) |
| **Column Shape** | `NA`, `C`, `O`, `R` | Column geometry (`C`: circular, `O`: oblong, `R`: rectangular; `NA` for single-span bridges) |
| **Abutment** | `S`, `D` | Abutment type (`S`: seat-type, `D`: diaphragm-type) |

Based on the specified bridge class, the framework automatically retrieves the corresponding component fragility functions from the bridge fragility library (`FRA_LIB.pkl`) and constructs the component-level fragility models required for the Monte Carlo simulation.
