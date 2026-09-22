from ..models import Iteration, IterationStep

# insert new iteration object into the db so we can start the iteration 
# return the ID
def insertIteration(polynomial, num, maxIter, threshold):
    iteration = Iteration(
        polynomial=polynomial, 
        currentIteration=0, 
        maxIteration=int(maxIter),
        startValue=num,
        threshold=float(threshold),
        converged=False
    )

    iteration.save()
    return iteration.pk 


# Check the iteration count of a currently running iteration
def getCurrIteration(id):
    iteration = Iteration.objects.get(pk=id)

    if iteration == None:
        return 0
    
    return iteration.currentIteration

# Return the max iteration of a currently running iteration
def getMaxIteration(id):
    iteration = Iteration.objects.get(pk=id)

    if iteration == None:
        return 0
    
    return iteration.maxIteration

def getStartValue(id):
    iteration = Iteration.objects.get(pk=id)

    if iteration == None:
        return None
    
    return iteration.startValue 

def getAllIterations(id):
    print("trying id")
    print(id)
    iterations = IterationStep.objects.filter(iterationID_id=id)
    print(iterations)
    return iterations

# Return whether the current iteration has converged
def getConverged(id):
    iteration = Iteration.objects.get(pk=id)

    if iteration == None:
        return False
    
    return iteration.converged
