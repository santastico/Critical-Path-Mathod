"""
📌 Critical Path Method (CPM) Analyzer
Author: Gabriel Santos Pereira

This script implements the Critical Path Method (CPM).
It reads a CSV file containing tasks, their durations, and predecessors,
calculates the earliest and latest start/finish times, identifies slack,
and determines the critical path — the sequence of tasks that cannot be delayed
without affecting the overall project duration.

The code is applied to a real-world example from the company Vallourec, 
in the context of optimizing the production of seamless steel tubes.
"""

import pandas as pd
import numpy as np

# Print stars for section formatting
def stars(number):
    print("*" * number)

# Error message when a task code is not found
def errorCodeMsg(code):
    print(f"Error in input file : CODE - Code '{code}' not found")
    quit()

# Error message when an invalid predecessor is found
def errorPredMsg(pred):
    print(f"Error in input file : PREDECESSORS - Invalid predecessor '{pred}'")
    quit()

# Error message for duration issues
def errorDurMsg():
    print("Error in input file : DURATION ")
    quit()

# Get index of task by its code
def getTaskIndex(mydata, code):
    if pd.isna(code) or code == '':
        return None
    try:
        return mydata.index[mydata['COD'] == code.strip()][0]
    except IndexError:
        errorCodeMsg(code)

# FORWARD PASS: Calculate Earliest Start (ES) and Earliest Finish (EF)
def forwardPass(mydata):
    ntask = mydata.shape[0]
    ES = np.zeros(ntask, dtype=np.int32)
    EF = np.zeros(ntask, dtype=np.int32)
    changed = True

    while changed:
        changed = False
        for i in range(ntask):
            old_es = ES[i]
            predecessors = mydata['PRE'][i]
            if pd.isna(predecessors) or predecessors == '':
                ES[i] = 0
                EF[i] = mydata['DUR'][i]
            else:
                if isinstance(predecessors, str):
                    predecessors = [p.strip() for p in predecessors.split(',') if p.strip()]
                elif not isinstance(predecessors, list):
                    predecessors = [predecessors]
                max_ef = float('-inf')
                for pred in predecessors:
                    pred_idx = getTaskIndex(mydata, pred)
                    if pred_idx is not None:
                        max_ef = max(max_ef, EF[pred_idx])
                ES[i] = max_ef if max_ef != float('-inf') else 0
                EF[i] = ES[i] + mydata['DUR'][i]
            if ES[i] != old_es:
                changed = True

    mydata['ES'] = ES
    mydata['EF'] = EF
    return mydata

# BACKWARD PASS: Calculate Latest Start (LS) and Latest Finish (LF)
def backwardPass(mydata):
    ntask = mydata.shape[0]
    LS = np.zeros(ntask, dtype=np.int32)
    LF = np.zeros(ntask, dtype=np.int32)

    # Build successor list
    SUC = [[] for _ in range(ntask)]
    for i in range(ntask):
        preds = mydata['PRE'][i]
        if pd.isna(preds) or preds == '':
            continue
        preds = [p.strip() for p in preds.split(',') if p.strip()]
        for pred in preds:
            pred_idx = getTaskIndex(mydata, pred)
            if pred_idx is not None:
                SUC[pred_idx].append(mydata['COD'][i])

    # Initialize terminal tasks (those with no successors)
    for i in range(ntask):
        if len(SUC[i]) == 0:
            LF[i] = mydata['EF'][i]
            LS[i] = LF[i] - mydata['DUR'][i]

    # Iterative update for other tasks
    changed = True
    while changed:
        changed = False
        for i in range(ntask - 1, -1, -1):
            if len(SUC[i]) > 0:
                min_ls = float('inf')
                for succ_code in SUC[i]:
                    succ_idx = getTaskIndex(mydata, succ_code)
                    if LF[succ_idx] != 0:
                        min_ls = min(min_ls, LS[succ_idx])
                if min_ls != float('inf'):
                    new_lf = min_ls
                    new_ls = new_lf - mydata['DUR'][i]
                    if new_lf != LF[i] or new_ls != LS[i]:
                        LF[i] = new_lf
                        LS[i] = new_ls
                        changed = True

    mydata['LS'] = LS
    mydata['LF'] = LF
    return mydata

# Calculate slack (LS - ES)
def slack(mydata):
    mydata['SLACK'] = mydata['LS'] - mydata['ES']
    return mydata

# Build the critical path string based on zero-slack activities
def critical_path_string(mydata):
    critical_activities = mydata[mydata['SLACK'] == 0]
    critical_activities = critical_activities.sort_values(by='ES')
    path = ' -> '.join(critical_activities['COD'].tolist())
    return path

# Main wrapper function
def computeCPM(mydata):
    mydata = forwardPass(mydata)
    mydata = backwardPass(mydata)
    mydata = slack(mydata)
    return mydata

# Output formatting
def printTask(mydata):
    print("CRITICAL PATH METHOD CALCULATOR")
    stars(90)
    print("ES = Earliest Start; EF = Earliest Finish; LS = Latest Start; LF = Latest Finish")
    stars(90)
    print(mydata[['COD', 'PRE', 'DUR', 'ES', 'EF', 'LS', 'LF', 'SLACK']])
    print(f"Minimum project duration: {np.max(mydata['EF'])} days")
    print(f"Critical path: {path}")
    stars(90)

# Main execution block
if __name__ == "__main__":
    # Read tasks from CSV file
    try:
        mydata = pd.read_csv('tasks.csv')
    except FileNotFoundError:
        print("Error: 'tasks.csv' not found. Please create a CSV file with columns 'COD', 'PRE', and 'DUR'.")
        quit()
    except Exception as e:
        print(f"Error loading CSV: {e}")
        quit()

    # Run CPM calculation and display results
    result = computeCPM(mydata)
    path = critical_path_string(result)
    printTask(result)
