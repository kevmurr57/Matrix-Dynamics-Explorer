from django.test import TestCase, Client
from django.db import transaction
from .controller.parseTree.parseTree import ParseTree
import numpy as np
from .controller.parseTree.maxIteration import MaxIteration, decodeValue
from .controller.parseTree.readMatrices import readFile
from .controller.parseTree.outputCsv import toCsv
import json
from .models import Iteration, IterationStep
from django.core.files.uploadedfile import InMemoryUploadedFile, SimpleUploadedFile


class ParseTestCase(TestCase):

    # tests parse poly with a simple example
    def testParsePoly(self):
        poly = ParseTree()
        poly.parsePoly(poly='2x + 1')
        ans = poly.callPoly(11)
        self.assertEqual(ans, 23)

    # tests parse poly with parenthesis involved
    def testParsePolyParens(self):
        poly = ParseTree()
        poly.parsePoly(poly='((5 + 6) * x + 2)')
        ans = poly.callPoly(3)
        self.assertEqual(ans, 35)

    # tests parse poly with exponents involved
    def testParsePolyExponents(self):
        poly = ParseTree()
        poly.parsePoly(poly='2x^2 + x')
        ans = poly.callPoly(2)
        self.assertEqual(ans, 10)

    # tests parse poly with subtraction 
    def testParsePolySubtraction(self):
        poly = ParseTree()
        poly.parsePoly(poly='5x - x - 1')
        ans = poly.callPoly(3)
        self.assertEqual(ans, 11)

    # tests parse poly with matrix
    # For a matrix polynomial the constant term is c*I, not an elementwise
    # scalar add, which is what AdditionNode has always implemented. So
    # 2A + 1 over [[1,2],[3,4]] is [[2,4],[6,8]] + [[1,0],[0,1]].
    # This case previously asserted the elementwise result [[3,5],[7,9]].
    def testParsePolyMat(self):
        poly = ParseTree()
        poly.parsePoly(poly='2x + 1')
        ans = poly.callPoly(np.asarray(a=[[1, 2], [3, 4]]))
        self.assertTrue(np.array_equal(ans, np.asarray(a=[[3, 4], [6, 9]])))

    # tests parse poly with negative
    def testParsePolyMinus(self):
        poly = ParseTree()
        poly.parsePoly(poly='-4x + 1')
        ans = poly.callPoly(2)
        self.assertEqual(ans, -7)

    # test parse poly with more complex negatives
    def testParsePolyAdvanceMinus(self):
        poly = ParseTree()
        poly.parsePoly(poly='5 + -x')
        ans = poly.callPoly(3)
        self.assertEqual(ans, 2)

    # test poly with negative parenthesis
    def testParsePolyNegParen(self):
        poly = ParseTree()
        poly.parsePoly(poly='-(x + 1)')
        ans = poly.callPoly(3)
        self.assertEqual(ans, -4)

    # test poly with division
    def testParsePolyDivision(self):
        poly = ParseTree()
        poly.parsePoly(poly='x / 3')
        ans = poly.callPoly(3)
        self.assertEqual(ans, 1)

    # test poly with multiplication and division
    def testParsePolyMultDiv(self):
        poly = ParseTree()
        poly.parsePoly(poly='x / 3 * 2')
        ans = poly.callPoly(6)
        self.assertEqual(ans, 4)

    def testLastIteration(self):
        iteration = MaxIteration()
        iter = Iteration(polynomial="2x", maxIteration=5, startValue=str(1))
        iter.save()
        ending = iteration.allIterations(iter)[-1]
        self.assertEqual(ending, '32')

    def testFirstIteration(self):
        iteration = MaxIteration()
        iter = Iteration(polynomial="4x", maxIteration=5, startValue=str(1))
        iter.save()
        starting = iteration.allIterations(iter)[0]
        self.assertEqual(starting, '1')

    def testMaxIteration(self):
        iteration = MaxIteration()
        iter = Iteration(polynomial="3x-1", maxIteration=15, startValue=str(1))
        iter.save()
        final = iteration.allIterations(iter)[-1]
        self.assertEqual(final, '7174454')

    def testConvergeIteration(self):
        iteration = MaxIteration()
        iter = Iteration(polynomial="x^0.5", maxIteration=105, startValue=str(.7))
        iter.save()
        computations = iteration.allIterations(iter)
        for i in range(len(computations)):
            computations[i] = float(computations[i])
        doesDiverge = iteration.diverges(computations, .00001)
        self.assertFalse(doesDiverge)

    def testDivergeIteration(self):
        iteration = MaxIteration()
        iter = Iteration(polynomial="2x-1", maxIteration=12, startValue=str(2))
        iter.save()
        computations = iteration.allIterations(iter)
        for i in range(len(computations)):
            computations[i] = int(computations[i])
        doesDiverge = iteration.diverges(computations, 10)
        self.assertTrue(doesDiverge)

    def testMatrixFirstIteration(self):
        iteration = MaxIteration()
        startMatrix = [1,0,0,1]
        iter = Iteration(polynomial="2x", maxIteration=5, startValue=json.dumps(startMatrix))
        iter.save()
        starting = iteration.allIterations(iter)
        starting = json.loads(starting[0])
        self.assertEqual(starting, startMatrix)

    def testMatrixLastIteration(self):
        iteration = MaxIteration()
        startMatrix = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        last = 15
        iter = Iteration(polynomial="2x", maxIteration=last, startValue=json.dumps(startMatrix))
        iter.save()
        secondMatrix = [[2**last, 0.0, 0.0], [0.0, 2**last, 0.0], [0.0, 0.0, 2**last]]
        matrices = iteration.allIterations(iter)
        self.assertTrue(np.array_equal(json.loads(matrices[-1]), secondMatrix))

    def testFirstCsvFirstIteration(self):
        iteration = MaxIteration()
        matrices = readFile("testIdentities.csv")
        matrix = matrices[0].tolist()
        iter = Iteration(polynomial="x", maxIteration=1, startValue=json.dumps(matrix))
        iter.save()
        allMatrices = iteration.allIterations(iter)
        self.assertTrue(np.array_equal(json.loads(allMatrices[0]), np.asarray(matrix)))

    def testFirstCsvLastIteration(self):
        iteration = MaxIteration()
        matrices = readFile("testIdentities.csv")
        lastMatrix = [[float(4**5), 0.0, 0.0], [0.0, float(4**5), 0.0], [0.0, 0.0, float(4**5)]]
        matrix = matrices[0].tolist()
        last = 5
        iter = Iteration(polynomial="4x", maxIteration=last, startValue=json.dumps(matrix))
        iter.save()
        allMatrices = iteration.allIterations(iter)
        last = allMatrices[-1]
        last = json.loads(last)
        last = np.asarray(last)
        lastMatrix = np.asarray(lastMatrix)
        self.assertTrue(np.array_equal(last, lastMatrix))

    def testLastCsvLastIteration(self):
        iteration = MaxIteration()
        matrices = readFile("testIdentities.csv")
        last = 5
        lastMatrix = [[float(3*2**last), 0.0, 0.0], [0.0, float(3*2**last), 0.0], [0.0, 0.0, float(3*2**last)]]
        startMatrix = matrices[-1].tolist()
        iter = Iteration(polynomial="2x", maxIteration=last, startValue=json.dumps(startMatrix))
        iter.save()
        allMatrices = iteration.allIterations(iter)
        lastMatrix = np.asarray(lastMatrix)
        first = allMatrices[-1]
        first = json.loads(first)
        first = np.asarray(first)
        self.assertTrue(np.array_equal(first, lastMatrix))

    def testMatrixConverges(self):
        pass
        #iteration = MaxIteration()
        #startMatrix = [[.87, 0, 0], [0, .87, 0], [0, 0, .87]]
        #iter = Iteration(polynomial="x^0.5", maxIteration=15, startValue=json.dumps(startMatrix))
        #iter.save()
        #matrices = iteration.allIterations(iter)
        #doesDiverge = iteration.diverges(matrices, .00001)
        #self.assertFalse(doesDiverge.any())

    def testMatrixDiverges(self):
        pass
        #iteration = MaxIteration()
        #startMatrix = [[.87, .8, .93], [.65, .97, 1.04], [.99, .18, .9]]
        #iter = Iteration(polynomial="x^2", maxIteration=15, startValue=json.dumps(startMatrix))
        #iter.save()
        #matrices = iteration.allIterations(iter)
        #for i in range(len(matrices)):
            #matrices[i] = 
        #doesDiverge = iteration.diverges(matrices, 1)
        #self.assertTrue(doesDiverge.any())

    def testOutputToCsv(self):
        pass
        #iteration = MaxIteration()
        #startMatrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        #iter = Iteration(polynomial="2x", maxIteration=28, startValue=json.dumps(startMatrix))
        #iter.save()
        #allMatrices = iteration.allIterations(iter)
        #toCsv(allMatrices, "outputTest.csv")

    def testInputToCsv(self):
        iteration = MaxIteration()
        matrices = readFile("testIdentities.csv")
        values = []
        for matrix in matrices:
            iter = Iteration(polynomial="2x", maxIteration=5, startValue=json.dumps(matrix.tolist()))
            iter.save()
            allMatrices = iteration.allIterations(iter)
            values.append(allMatrices)
        toCsv(values, "bigOutputTest.csv")

class PolynomialValidationTestCase(TestCase):
    """verifyPoly() is the only guard in front of the parser, so anything it
    calls 'Valid' must actually parse. These cases previously passed
    validation and then crashed the parser with an IndexError, which surfaced
    as an unhandled 500."""

    # parentheses were validated by counting only, so ")(" had one of each
    # and was accepted even though the order is nonsense
    def testRejectsReversedParens(self):
        self.assertNotEqual(ParseTree().verifyPoly(')('), 'Valid')

    def testRejectsUnorderedParens(self):
        self.assertNotEqual(ParseTree().verifyPoly('(()))('), 'Valid')

    def testRejectsEmptyParenPair(self):
        self.assertNotEqual(ParseTree().verifyPoly('x+()'), 'Valid')

    def testRejectsUnclosedParen(self):
        self.assertNotEqual(ParseTree().verifyPoly('((x+1)'), 'Valid')

    def testRejectsUnopenedParen(self):
        self.assertNotEqual(ParseTree().verifyPoly('x+1)'), 'Valid')

    # a leading '-' is a unary sign and cleanPoly rewrites it as "-1*x",
    # so the validator must not reject it as a dangling operator
    def testAcceptsLeadingNegative(self):
        self.assertEqual(ParseTree().verifyPoly('-x+3'), 'Valid')

    def testAcceptsLeadingNegativeCoefficient(self):
        self.assertEqual(ParseTree().verifyPoly('-5x^2'), 'Valid')

    def testAcceptsLeadingNegativeParen(self):
        self.assertEqual(ParseTree().verifyPoly('-(x+1)'), 'Valid')

    # ...but a bare sign has no term after it
    def testRejectsBareMinus(self):
        self.assertNotEqual(ParseTree().verifyPoly('-'), 'Valid')

    def testRejectsLeadingPlus(self):
        self.assertNotEqual(ParseTree().verifyPoly('+x'), 'Valid')

    # the contract that matters: validator and parser must agree
    def testEverythingValidActuallyParses(self):
        candidates = [
            'x^2+1', '(x+1)*(x-1)', '5x', '((x))', '2*(x^2-4)/2',
            '-x+3', '-5x^2', '-(x+1)', 'x/2', '3x^2-2x+1',
            ')(', '(()))(', 'x+()', '((x+1)', 'x+1)', '', '-', '+x',
            'x^^2', '5//x', 'x+', '*x',
        ]
        for poly in candidates:
            tree = ParseTree()
            if tree.verifyPoly(poly) != 'Valid':
                continue
            try:
                ParseTree().parsePoly(poly)
            except Exception as exc:
                self.fail(
                    f"verifyPoly accepted {poly!r} but parsePoly raised "
                    f"{type(exc).__name__}: {exc}"
                )


class IterationValueTestCase(TestCase):
    """Stored iteration values are text, so they must be classified correctly
    on the way back in. The old str.isdigit() sniffing only recognised plain
    digits, so negatives and scientific notation fell through to the matrix
    branch and became 0-d numpy arrays, which crash on x.shape[0]."""

    def testDecodesPlainInteger(self):
        self.assertEqual(decodeValue('5'), 5)

    def testDecodesDecimal(self):
        self.assertAlmostEqual(decodeValue('0.125'), 0.125)

    def testDecodesNegative(self):
        self.assertAlmostEqual(decodeValue('-1.5'), -1.5)

    def testDecodesScientificNotation(self):
        self.assertAlmostEqual(decodeValue('6.103515625e-05'), 6.103515625e-05)

    def testDecodesLargeScientificNotation(self):
        self.assertAlmostEqual(decodeValue('1.2676506002282294e+30'), 1.2676506002282294e+30)

    def testScalarsNeverBecomeZeroDimArrays(self):
        for raw in ['5', '0.125', '-1.5', '6.1e-05', '1.26e+30']:
            value = decodeValue(raw)
            self.assertNotIsInstance(value, np.ndarray, f'{raw!r} decoded to an array')

    def testDecodesMatrix(self):
        value = decodeValue('[[1, 2], [3, 4]]')
        self.assertIsInstance(value, np.ndarray)
        self.assertEqual(value.shape, (2, 2))

    # a sequence converging toward zero reaches scientific notation around
    # step 15 and used to crash there
    def testConvergingScalarRunCompletes(self):
        iteration = Iteration(polynomial='0.5x', maxIteration=40,
                              startValue='2.0', threshold=1e-9)
        iteration.save()
        results = MaxIteration().allIterations(iteration)
        self.assertEqual(len(results), 40)

    # negative values failed isdigit() immediately
    def testNegativeScalarRunCompletes(self):
        iteration = Iteration(polynomial='x-1', maxIteration=20,
                              startValue='3.0', threshold=1e-9)
        iteration.save()
        results = MaxIteration().allIterations(iteration)
        self.assertEqual(len(results), 20)

    # growth past 1e16 also renders in scientific notation
    def testDivergingScalarRunCompletes(self):
        iteration = Iteration(polynomial='2x', maxIteration=80,
                              startValue='1.0', threshold=1e-9)
        iteration.save()
        results = MaxIteration().allIterations(iteration)
        self.assertEqual(len(results), 80)


class DivergenceClassificationTestCase(TestCase):
    """The outcome label must match what the numbers actually do. The old
    check only asked whether any value repeated, so a run that simply had not
    reached the threshold was reported as diverging to infinity."""

    def setUp(self):
        self.iterator = MaxIteration()

    # 0.5x from 2.0 converges toward zero
    def testConvergingSequenceIsNotInfinite(self):
        values = [str(2.0 * 0.5 ** n) for n in range(30)]
        self.assertFalse(self.iterator.isInfiniteDivergenceNum(values))

    def testConvergingSequenceHasNoCycle(self):
        values = [str(2.0 * 0.5 ** n) for n in range(30)]
        self.assertFalse(self.iterator.hasCycleNum(values))

    # 2x from 1.0 genuinely runs away
    def testGrowingSequenceIsInfinite(self):
        values = [str(2.0 ** n) for n in range(40)]
        self.assertTrue(self.iterator.isInfiniteDivergenceNum(values))

    def testRepeatingSequenceIsACycle(self):
        values = ['1.0', '2.0', '1.0', '2.0']
        self.assertTrue(self.iterator.hasCycleNum(values))

    def testRepeatingSequenceIsNotInfinite(self):
        values = ['1.0', '2.0', '1.0', '2.0']
        self.assertFalse(self.iterator.isInfiniteDivergenceNum(values))

    # ndarray.tostring() was removed in numpy 2; this used to raise
    def testMatrixHelpersRunOnNumpy2(self):
        matrices = [np.array([[1.0, 0.0], [0.0, 1.0]]) * (2 ** n) for n in range(6)]
        self.assertFalse(self.iterator.hasCycle(matrices))
        self.assertIsInstance(self.iterator.isInfiniteDivergence(matrices), bool)

    def testMatrixCycleDetected(self):
        a = np.array([[1.0, 0.0], [0.0, 1.0]])
        self.assertTrue(self.iterator.hasCycle([a, a * 2, a]))


class ViewsTestCase(TestCase):

    # test whether Views can return the index page
    def testGetIndex(self):
        c = Client()
        response = c.get('')
        self.assertEqual(response.status_code, 200)

    # test whether Views can successfully validate a correctly formatted polynomial
    def testValidatePoly(self):
        c = Client()
        response = c.get('/verifyPoly/?polynomial=x%20%2B%203')
        content = response.content.decode('utf-8')
        content = json.loads(content)
        self.assertEqual(content['message'], 'Valid')

    # test whether Views can successfully identify an empty poly
    def testEmptyPoly(self):
        c = Client()
        response = c.get('/verifyPoly/?polynomial=')
        content = response.content.decode('utf-8')
        content = json.loads(content)
        self.assertEqual(content['message'], 'Polynomial Cannot be Empty')

    # test whether Views can successfully spot a poly with an invalid token
    def testInvalidToken(self):
        c = Client()
        response = c.get('/verifyPoly/?polynomial=y%20%2B%203')
        content = response.content.decode('utf-8')
        content = json.loads(content)
        self.assertEqual(content['message'], 'Invalid Token Error')

    # test whether Views can successfully spot an invalid operation 
    def testInvalidOperation(self):
        c = Client()
        response = c.get('/verifyPoly/?polynomial=x%20%2B%20^%203')
        content = response.content.decode('utf-8')
        content = json.loads(content)
        self.assertEqual(content['message'], 'Invalid Operation Error')

    # test whether views can insert a Poly into the db and return loading page
    def testInsertPoly(self):
        c = Client()
        response = c.get('/numberPoly/?polynomial=x%20%2B%203&num=1&maxIter=100&threshold=0.1')
        self.assertEqual(response.status_code, 200)

    # test whether we can start an iteration for an inserted polynomial
    @transaction.atomic
    def testStartIteration(self):
        # insert a poly
        c = Client()
        response = c.get('/numberPoly/?polynomial=x%20%2B%203&num=1&maxIter=100&threshold=0.1')

        # get id from response
        response_str = response.content.decode()
        response_id_index = response_str.index('let id = ')
        id_str = ""
        reached_quote = False 
        while response_id_index < len(response_str):
            if reached_quote and response_str[response_id_index] == '"':
                break
            elif response_str[response_id_index] == '"':
                reached_quote = True
            elif reached_quote:
                id_str += response_str[response_id_index]

            response_id_index += 1

        response = c.post('/startIteration/', json.dumps({'id': id_str}), content_type='application/json')
        status = response.status_code
        print("my status:")
        print(status)
        self.assertEqual(status, 202)

    def testCsvPoly(self):
        c = Client()
        with open('testIdentities.csv', 'r') as f:
            postResponse = c.post('/csvPoly/',
                {
                    'polynomial': '5x',
                    'maxIter': '10',
                    'threshold': '.2',
                    'csv': InMemoryUploadedFile(f, "file_content", 'testIdentities.csv', 'csv', 5000, 0),
                }
            )
        self.assertEqual(postResponse.status_code, 200)

    def testMatrixPoly(self):
        c = Client()
        #response = c.get('/matrixPoly/?polynomial=x%20%2B%203&MATRIX&maxIter=100&threshold=0.1')
        getResponse = c.get('/matrixPoly/',
                {
                    'polynomial': '5x',
                    'maxIter': '10',
                    'threshold': '.2',
                    '00': '1',
                    '01': '0',
                    '10': '0',
                    '11': '1'
                })
        self.assertEqual(getResponse.status_code, 200)

    def testFetchNumber(self):
        c = Client()
        Iteration.objects.create(polynomial='x+1', startValue=3, converged=True)
        i = Iteration.objects.get(polynomial='x+1')
        IterationStep.objects.create(iterationID=i, value=5, step=0)
        IterationStep.objects.create(iterationID=i, value=7, step=1)

        getResponse = c.generic('GET', '/fetchNumber/', json.dumps({'id': i.id}), content_type='application/json')

        self.assertEqual(getResponse.status_code, 200)

    def testOutputnumber(self):
        c = Client()
        Iteration.objects.create(polynomial='x+1', startValue=3, converged=True)
        i = Iteration.objects.get(polynomial='x+1')

        getResponse = c.get('/outputnumber/', {
            'id': i.id
        })

        self.assertEqual(getResponse.status_code, 200)








