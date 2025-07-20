import pandas as pd
import numpy as np

# Print stars for formatting
def stars(number):
    print("*" * number)

# Error messages with debug
def errorCodeMsg(code):
    print(f"Error in input file : CODE - Code '{code}' not found")
    quit()

def errorPredMsg(pred):
    print(f"Error in input file : PREDECESSORS - Invalid predecessor '{pred}'")
    quit()

def errorDurMsg():
    print("Error in input file : DURATION ")
    quit()

# Scans if the code in predecessors is in the list of task codes
def getTaskIndex(mydata, code):
    if pd.isna(code) or code == '':
        return None
    try:
        return mydata.index[mydata['COD'] == code.strip()][0]
    except IndexError:
        errorCodeMsg(code)

# Critical Path Method Forward Pass
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

# Critical Path Method Backward Pass
def backwardPass(mydata):
    ntask = mydata.shape[0]
    LS = np.zeros(ntask, dtype=np.int32)
    LF = np.zeros(ntask, dtype=np.int32)

    # Cria lista de sucessores
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

    # Inicializa tarefas finais (sem sucessores)
    for i in range(ntask):
        if len(SUC[i]) == 0:
            LF[i] = mydata['EF'][i]
            LS[i] = LF[i] - mydata['DUR'][i]

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

def slack(mydata):
    mydata['SLACK'] = mydata['LS'] - mydata['ES']
    return mydata

def critical_path_string(mydata):
    # Filtra atividades com slack = 0
    critical_activities = mydata[mydata['SLACK'] == 0]
    
    # Ordena pela coluna ES (início mais cedo)
    critical_activities = critical_activities.sort_values(by='ES')
    
    # Concatena os códigos
    path = ' -> '.join(critical_activities['COD'].tolist())
    return path

# Wrapper function
def computeCPM(mydata):
    mydata = forwardPass(mydata)
    mydata = backwardPass(mydata)
    mydata = slack(mydata)
    return mydata

# Print function (adjusted for ES and EF only)
def printTask(mydata):
    print("CRITICAL PATH METHOD CALCULATOR")
    stars(90)
    print("ES = Earliest Start; EF = Earliest Finish; LS = Latest Start; LF = Latest Finish")
    stars(90)
    print(mydata[['COD', 'PRE', 'DUR', 'ES', 'EF', 'LS', 'LF', 'SLACK']])
    print(f"Tempo mínimo do projeto: {np.max(mydata['EF'])} dias")
    print(f"Caminho crítico: {path}")
    stars(90)

# Main execution
if __name__ == "__main__":
    # Load data from CSV
    try:
        mydata = pd.read_csv('tasks.csv')
    except FileNotFoundError:
        print("Error: 'tasks.csv' not found. Please create a CSV file with columns 'COD', 'PRE', and 'DUR'.")
        quit()
    except Exception as e:
        print(f"Error loading CSV: {e}")
        quit()

    # Compute and print CPM
    result = computeCPM(mydata)
    path = critical_path_string(result)
    printTask(result)