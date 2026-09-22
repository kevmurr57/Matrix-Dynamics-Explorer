from .parseTree import ParseTree
from ...models import Iteration, IterationStep
import json
import numpy as np
from django.core.exceptions import ObjectDoesNotExist


def decodeValue(raw):
    """Turn a stored iteration value back into a number or a numpy matrix.

    Values are persisted as text, so they have to be classified on the way
    back in. This previously sniffed the string with str.isdigit(), which
    only recognises plain digits: it rejected negative numbers ("-1.0") and
    scientific notation ("6.1e-05"), both of which a scalar run produces
    almost immediately. Those fell through to the matrix branch and became
    0-d numpy arrays, which blow up on x.shape[0].

    Try to read it as a number first, and only treat it as a matrix if that
    genuinely fails.
    """
    if not isinstance(raw, str):
        return raw

    text = raw.strip()

    try:
        return int(text)
    except ValueError:
        pass

    try:
        return float(text)
    except ValueError:
        pass

    decoded = np.asarray(json.loads(text))

    # json.loads("1e-5") yields a scalar, which np.asarray makes 0-d;
    # unwrap it rather than handing a shapeless array to the matrix path.
    if decoded.ndim == 0:
        return decoded.item()

    return decoded

class MaxIteration():

    def __init__(self):
        self.root = None

    # Takes polynomial, max number of iterations, and starting value
    def allIterations(self, iteration):
        res = [iteration.startValue]
        i = 1
        poly = ParseTree()
        poly.parsePoly(poly=iteration.polynomial)

        # insert first iteration step
        startValue = decodeValue(iteration.startValue)
        if isinstance(startValue, np.ndarray):
            startValue = startValue.astype('float32')

        value = poly.callPoly(startValue)

        if type(value) == float or type(value) == int:
            first = IterationStep(iterationID=iteration, value=value, step=0)
        else:
            print(value)
            value = value.tolist()
            first = IterationStep(iterationID=iteration, value=json.dumps(value), step=0)
        
        first.save()

        # The previous step is already in hand from the last pass, so keep it in
        # memory instead of re-reading it from the database every iteration.
        prevStored = first.value

        # Progress is polled by the browser, so it has to be written to the
        # database — but not on every single step. One write per iteration
        # meant a 1,000-step run issued 1,000 progress writes on top of its
        # 1,000 result writes, which is what makes SQLite lock up.
        PROGRESS_EVERY = 25

        while i < iteration.maxIteration:
            if i % PROGRESS_EVERY == 0:
                iteration.currentIteration = i
                iteration.save(update_fields=['currentIteration'])

            prevValue = decodeValue(prevStored)

            newValue = poly.callPoly(prevValue)
            if type(newValue) == int or type(newValue) == float:
                newStep = IterationStep(iterationID=iteration, value=str(newValue), step=i)

            else:
                newValue = newValue.tolist()
                newValue = json.dumps(newValue)
                newStep = IterationStep(iterationID=iteration, value=newValue, step=i)
            
            res.append(newStep.value)
            newStep.save()
            prevStored = newStep.value
            i += 1
        
        iteration.currentIteration = i
        iteration.converged = not self.diverges(res, iteration.threshold)
        iteration.save()
    
        return res
    
    # Based on results checks to see if threshold is reached
    def diverges(self, results, threshold):
        # Scalar runs compare magnitudes. The difference is taken in absolute
        # value: without it a rapidly decreasing sequence produced a negative
        # difference, which is always below the threshold and so was
        # misreported as converged.
        firstValue = decodeValue(results[0])
        if isinstance(firstValue, (int, float)):
            return abs(float(decodeValue(results[-1])) - float(decodeValue(results[-2]))) > threshold
        # NOTE: this was `type(results[0] == str)`, which takes the type of the
        # comparison's result and is therefore always truthy. The branch ran
        # unconditionally and called json.loads() on values that were already
        # ndarrays. Only decode entries that are genuinely still strings.
        # A delta needs two samples. The original code indexed
        # results[len(results)-2], which for a single result wrapped around to
        # the same element and reported a difference of zero; keep that
        # "not diverged" outcome explicit rather than relying on the wrap.
        if len(results) < 2:
            return False

        last, prev = results[-1], results[-2]

        last = decodeValue(last)
        prev = decodeValue(prev)

        return abs(np.linalg.norm(last) - np.linalg.norm(prev)) > threshold
    
    def showIteration(current, end):
        ## Line below is placeholder until we have frontend working
        print(current + "/" + end)

    # Only needed if allIterations doesn't work for matrices, so far it isnt used
    def matrixIterations(self, polynomial, maxVal, startMatrix):
        i = 0
        results = [0 for x in range(maxVal+1)]
        poly = ParseTree()
        poly.parsePoly(poly=polynomial)
        results[0] = startMatrix
        while i < maxVal:
            i += 1
            ## showIteration(i, maxVal)
            results[i] = poly.callPoly(results[i-1])
        return results
    
    # returns the value the matrix converged on given an id
    def getConvergeValue(self, id):
        iteration = Iteration.objects.get(pk=id)

        if iteration == None:
            return None
        
        iterationSteps = IterationStep.objects.filter(iterationID=id)
        try:
            iterationStep = iterationSteps.get(step=iteration.currentIteration - 1)
        except ObjectDoesNotExist:
            return None
        
        return iterationStep.value
    
    # starts the iteration when given an id
    def startIteration(self, id):
        iteration = Iteration.objects.get(pk=id)

        if iteration == None:
            return
        
        self.allIterations(iteration)

    # Returns the norm for each iteration step
    def getNorms(self, matrices): 
        res = []
        for i in range(len(matrices)):
            matrices[i] = json.loads(matrices[i])
            matrices[i] = np.asarray(matrices[i])

            matrices[i] = matrices[i].astype(float)

            if i > 0:
                res.append(abs(np.linalg.norm(matrices[i] - matrices[i-1])))

        return res
    
    # Returns the eigenvalues for each matrix
    def getEigenvalues(self, matrices):
        res = []
        for i in range(len(matrices)):
            res.append(np.linalg.eigvals(matrices[i]))

        return res
    
    # Returns whether the divergence approaches infinity or repeats
    def isInfiniteDivergence(self, matrices):
        visited = set()
        for matrix in matrices:
            mstr = matrix.tostring()
            if mstr in visited:
                return False

            visited.add(mstr)

        return True
    
    # Returns the difference for a number iteration
    def getDifference(self, numbers):
        res = []
        for i in range(1, len(numbers)):
            res.append(float(numbers[i]) - float(numbers[i-1]))
        
        return res
    
    # Returns whether the divergence approaches infinity or repeats
    def isInfiniteDivergenceNum(self, numbers):
        visited = set()
        for num in numbers:
            if num in visited:
                return False

            visited.add(num)

        return True