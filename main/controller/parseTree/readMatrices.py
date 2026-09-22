from csv import reader
import math
import numpy as np
import pandas as pd
import json

# Returns true if value is a perfect square
def checkSquare(length):
    return (math.sqrt(length) * math.sqrt(length)) == length

# Reshape a flat set of values into a square numpy matrix.
# Accepts either a comma-separated string ("1,0,0,1") or an already-split
# sequence (["1", "0", "0", "1"]); readFile passes the latter.
def convert(matrix):
    if isinstance(matrix, (str, bytes)):
        text = matrix.decode() if isinstance(matrix, bytes) else matrix
        values = [v for v in text.split(',') if v.strip() != '']
    else:
        values = [v for v in matrix if str(v).strip() != '']

    flat = np.asarray([float(v) for v in values], dtype=float)

    side = math.isqrt(len(flat))
    if side * side != len(flat):
        raise ValueError(
            f"expected a square matrix, got {len(flat)} values"
        )

    return flat.reshape(side, side)

# Takes a filename and returns list of all matrices
# Return type is numpy array of integers
def readFile(fileName):
    with open(fileName, 'r') as file:
        csv_reader = reader(file)
        matrices = []
        current = 0
        for matrix in csv_reader:
            current += 1
            validLength = checkSquare(len(matrix))
            if validLength:
                longMatrix = convert(matrix)
                matrices.append(np.asarray(longMatrix))
            else:
                #Placeholder to throw error
                print("Not valid matrix size on line" + str(current))
        return matrices
    
def csvToMatrices(csv):
    matrices = []
    for line in csv.file:
        line_str = line.decode('utf-8')
        line_str = line_str.replace('\r', '')
        line_str = line_str.replace('\n', '')
        line_list = line_str.split(',')  
        matrix = []
        for i in range(0, len(line_list), int(math.sqrt(len(line_list)))):
            temp = []
            for j in range(i, i+int(math.sqrt(len(line_list)))):
                temp.append(line_list[j])

            matrix.append(temp)
        
        matrices.append(json.dumps(matrix))
    
    return matrices


