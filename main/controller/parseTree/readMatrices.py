from csv import reader
import math
import numpy as np
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


# Limits for uploaded batches. csvPoly creates a database row and a worker
# thread per line, so an unbounded file is a denial-of-service vector as well
# as a usability problem.
MAX_CSV_BYTES = 1024 * 1024
MAX_CSV_ROWS = 500
MAX_MATRIX_SIDE = 10


def validateCsvUpload(uploaded):
    """Check an uploaded CSV of flattened square matrices.

    Returns None when the file is usable, otherwise a message explaining the
    first problem found. csvToMatrices does no checking of its own: it reshapes
    whatever it is given, so a malformed row silently produces a wrong matrix.
    """
    if uploaded is None:
        return 'No file selected'

    name = (getattr(uploaded, 'name', '') or '').lower()
    if name and not name.endswith('.csv'):
        return 'File must be a .csv'

    size = getattr(uploaded, 'size', None)
    if size is not None and size > MAX_CSV_BYTES:
        return f'File is too large (limit {MAX_CSV_BYTES // 1024} KB)'

    try:
        raw = uploaded.read()
    finally:
        # The caller still needs to parse this file, so rewind it.
        if hasattr(uploaded, 'seek'):
            uploaded.seek(0)

    if isinstance(raw, bytes):
        try:
            raw = raw.decode('utf-8')
        except UnicodeDecodeError:
            return 'File must be UTF-8 encoded text'

    rows = [line for line in raw.replace('\r', '').split('\n') if line.strip()]

    if not rows:
        return 'File is empty'

    if len(rows) > MAX_CSV_ROWS:
        return f'Too many rows (limit {MAX_CSV_ROWS})'

    for number, line in enumerate(rows, start=1):
        values = [v.strip() for v in line.split(',')]

        for value in values:
            try:
                float(value)
            except ValueError:
                return f'Line {number}: "{value}" is not a number'

        side = math.isqrt(len(values))
        if side * side != len(values):
            return (
                f'Line {number}: {len(values)} values do not form a square '
                f'matrix'
            )

        if side > MAX_MATRIX_SIDE:
            return f'Line {number}: matrix is larger than {MAX_MATRIX_SIDE}x{MAX_MATRIX_SIDE}'

    return None
