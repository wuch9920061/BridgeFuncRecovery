# BridgeFuncRecovery
This project aims to probabilistically model the post-earthquake functional recovery of bridges. The source codes are programmed in Python.

### Reference
[1] Wu, C., Burton, H., Zsarnóczay, A., Chen. S., Xie. Y., Terzić, V., Günay, S., Padgett, J., Mieler, and M., Almufti, I. (2025). Modeling Post-earthquake Functional Recovery of Bridges. Earthquake Spectra. 

### Prerequisites
Python: version 3.6 or above.

Necessary Python packages: copy, numpy, pandas, os, scipy, sys, shutil, pathlib, re, time, pickle

### File Overview
*main.py* takes user-specified parameters and performs the full analysis. 

*utils.py* provides auxiliary functions that are called from the main script *main.py*. 

*result_anlaysis.py* helps visualize the output data stored in *Results.pkl*. 

After running *main.py* or calling *run()* programmatically, a Results.pkl file is created that stores all model output data 

### User-specified inputs for *run()*

The *run()* function requires the following inputs:

Required Arguments:
- *IM_fixed* (float): Evaluated intensity measure level.
- *num_span* (int): Number of bridge spans.
- *CompQty* (dict): A dictionary of quantities of bridge components. An example is shown below:
```python
"CompQty": {  # dict[str, int]
    'Col':3, 'Seat_ab':2, 'Super':1, 'ColFnd':2, 'AbFnd':2, 'Backwall':2, 
    'Bearing_ab':2,'Key_ab':2, 'ApproSlab':2, 'JointSeal_ab':4,
    'Seat_super':1, 'Bearing_super':0, 'Key_super':0, 'JointSeal_super': 0
}
```

- *WorkerAllo_percrew* (dict): A dictionary listing allocated workers that constitute a worker crew to perform repairs for each bridge component. An example is shown below:
```python
"WorkerAllo_percrew": {  # dict[str, int]
    'Col': 3, 'Seat_ab': 4, 'Super': 5, 'ColFnd': 4, 'AbFnd': 4, 'Backwall': 4, 
    'Bearing_ab': 3, 'Key_ab': 3, 'ApproSlab': 5, 'JointSeal_ab': 5,
    'Seat_super':4, 'Bearing_super':2, 'Key_super':4, 'JointSeal_super': 4
}
```

- *Worker_Replace* (int): Number of workers to perform bridge replacement. 


Optional Arguments:
- *num_rlz* (int, default = 1000): Number of Monte Carlo realizations.
- *w* (list of float, default = [0, 0, 1]): A weighing scheme specifying how correlations are considered in bridge component damage sampling. The first entry is correlation shared for all components; the second entry is shared for components in a smaller family, and the third entry is independent portion. [0,0,1] means all components’ damage are sampled independently. [1,0,0] means all damages are perfectly correlated. For more details, see “A model for partially dependent component damage fragilities in seismic risk analysis” (Baker et al. 2023).
- *height* (float, default = 35): Bridge height.
- *num_lanes_before* (int, default = 4): Number of available bridge lanes under normal operations.
- *ColSuperMatType_dict* (dict, default = {'Col': 'concrete', 'Super': 'concrete'}): Bridge materials used in columns and superstructures. Possible entries: ‘Concrete’ or ‘Steel’.
- *NumCrew_percomp* (dict): A dictionary specifying number of worker crews per component. Default shown below:

```python
"NumCrew_percomp": {  # dict[str, int]
    'Col': 1, 'Seat_ab': 1, 'Super': 1, 'ColFnd': 1, 'AbFnd': 1, 'Backwall': 1,
    'Bearing_ab': 1, 'Key_ab': 1, 'ApproSlab': 1, 'JointSeal_ab': 1,
    'Seat_super': 1, 'Bearing_super': 1, 'Key_super': 1, 'JointSeal_super': 1
}
```

- *WorkHour_repairable* (int, default = 8): Worker-hour per day used to repair bridge components.
- *WorkHour_replacement* (int, default = 8): Worker-hour per day used to replace a bridge.
- *num_concrete_pour_replacement* (int, default = 1): How many pours of concrete are considered when replacing a bridge.
- *dispersion_assigned* (float, default = 0.3): Dispersion considered in repair duration sampling. 


Example call:
```python
from BridgeFuncRecovery import run

results = run(
    IM_fixed=0.23,
    num_span=2,
    CompQty={'Col':3, 'Seat_ab':2, ...},
    WorkerAllo_percrew={'Col':3, 'Seat_ab':4, ...},
    Worker_Replace=30
)
```
This returns a results dictionary and saves it to *Results.pkl*


### Analyzing the Results
The functions in *result_analysis.py* help interpret and visualize output data from the main analysis. Available functions include:
- *plot_fs_initial(data)*
- *plot_fs_reopening(data)*
- *plot_total_impeding_ccdf(data)*
- *plot_total_repair_ccdf(data)*
- *print_impeding_medians(data)*
- *print_repair_durations(data)*
- *plot_repair_class_distribution_single(data, comp_name)*
- *plot_all_repair_class_distributions(data)*
- *plot_closed_lane_initial(data)*
- *show_all_results(data)*

Example usage:
```python
from BridgeFuncRecovery import run, plot_repair_class_distribution_single

# Run the analysis
results = run(IM_fixed=0.23, num_span=2, CompQty={...}, WorkerAllo_percrew={...}, Worker_Replace=30)

# Plot the Repair Class distribution for columns
plot_repair_class_distribution_single(results, 'Col')
```

This saves results to *Results.pkl* and displays a figure visualizing Repair Class (RC) distribution for columns.

### Full Example

Below is a full working example with realistic parameter values:

```python
input_dictionary = {
    # Required inputs:
    "IM_fixed": 0.23,  # float
    "num_span": 2,  # int
    "CompQty": {  # dict[str, int]
        'Col':3, 'Seat_ab':2, 'Super':1, 'ColFnd':2, 'AbFnd':2, 'Backwall':2, 
        'Bearing_ab':2,'Key_ab':2, 'ApproSlab':2, 'JointSeal_ab':4,
        'Seat_super':1, 'Bearing_super':0, 'Key_super':0, 'JointSeal_super': 0
    },
    "WorkerAllo_percrew": {  # dict[str, int]
        'Col': 3, 'Seat_ab': 4, 'Super': 5, 'ColFnd': 4, 'AbFnd': 4, 'Backwall': 4, 
        'Bearing_ab': 3, 'Key_ab': 3, 'ApproSlab': 5, 'JointSeal_ab': 5,
        'Seat_super':4, 'Bearing_super':2, 'Key_super':4, 'JointSeal_super': 4
    },
    "Worker_Replace": 30,  # int
    
    # Optional inputs:
    "num_rlz": 100,  # int
    "w": [0, 0, 1],  # list of ints
    "height": 35,  # int, in ft
    "num_lanes_before": 4,  # int
    "ColSuperMatType_dict": {  # dict[str, str]
        'Col': 'steel', 'Super': 'concrete'
    },
    "NumCrew_percomp": {  # dict[str, int]
        'Col': 1, 'Seat_ab': 1, 'Super': 1, 'ColFnd': 1, 'AbFnd': 1, 'Backwall': 1,
        'Bearing_ab': 2, 'Key_ab': 2, 'ApproSlab': 1, 'JointSeal_ab': 1,
        'Seat_super':1, 'Bearing_super':2, 'Key_super':1, 'JointSeal_super': 1
    },
    "WorkHour_repairable": 10,  # int
    "WorkHour_replacement": 10,  # int
    "num_concrete_pour_replacement": 1,  # int
    "dispersion_assigned" = 0.3 # float
}

from BridgeFuncRecovery import run, show_all_results
# Run analysis
results = run(**input_dictionary, return_data=True)

# Show all the results
show_all_results(results)
```
