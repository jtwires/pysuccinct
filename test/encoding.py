import unittest

from succinct import encoding

from test import bitvector

def argmin(sequence):
    minidx, minval = None, None
    for idx, val in enumerate(sequence):
        if minval is None or val < minval:
            minidx, minval = idx, val
    if minidx is None:
        raise ValueError('empty sequence')
    return minidx

def argmax(sequence):
    maxidx, maxval = None, None
    for idx, val in enumerate(sequence):
        if maxval is None or val > maxval:
            maxidx, maxval = idx, val
    if maxidx is None:
        raise ValueError('empty sequence')
    return maxidx

class BalancedParentheses(encoding.BalancedParentheses):

    def _checkrange(self, i, j):
        if i < 0 or j < 0 or i >= len(self) or j >= len(self):
            raise IndexError('index out of range')
        if i > j:
            raise ValueError('{} > {}'.format(i, j))

    def fwdsearch(self, i, d):
        # allow i == -1 so we can scan the entire array
        tgt = d + (0 if i == -1 else self.excess(i))
        idx = next(
            (
                j
                for j in range(i + 1, len(self))
                if self.excess(j) == tgt
            ),
            None
        )
        if idx is None:
            raise ValueError('excess({}) not found after {}'.format(tgt, i))
        return idx

    def bwdsearch(self, i, d):
        # allow i == len(self) so we can scan entire array
        tgt = d + (0 if i == len(self) else self.excess(i))
        idx = next(
            (
                j
                for j in reversed(range(i))
                if self.excess(j) == tgt
            ),
            # special case: excess[-1] == 0
            -1 if tgt == 0 else None
        )
        if idx is None:
            raise ValueError('excess({}) not found before {}'.format(tgt, i))
        return idx

    def firstmin(self, i, j):
        self._checkrange(i, j)
        return i + argmin(self.excess(x) for x in range(i, j + 1))

    def firstmax(self, i, j):
        self._checkrange(i, j)
        return i + argmax(self.excess(x) for x in range(i, j + 1))

    def countmin(self, i, j):
        self._checkrange(i, j)
        e = [self.excess(x) for x in range(i, j + 1)]
        m = min(e)
        return sum(1 for x in e if x == m)

    def selectmin(self, i, j, k):
        self._checkrange(i, j)
        e = [self.excess(x) for x in range(i, j + 1)]
        m, cnt = min(e), k
        for x, val in enumerate(e, i):
            if m == val:
                cnt -= 1
                if cnt == 0:
                    return x
        raise ValueError('range has no minrank {}'.format(k))

class BPTestCases(object):

    class BPTests(unittest.TestCase):

        def construct(self, sequence):
            raise NotImplementedError()

        def test_unbalanced(self):
            strings = (
                '(',
                ')',
                ')(',
                '(()',
                '())',
                '(())('
                '(())))',
                '(())(('
            )
            for string in strings:
                with self.assertRaises(ValueError):
                    self.construct(string)

        def test_excess(self):
            enc = self.construct('(((()))())')
            for idx in range(len(enc)):
                o = sum(1 for c in enc[:idx + 1] if c == '(')
                c = sum(1 for c in enc[:idx + 1] if c == ')')
                self.assertEqual(enc.excess(idx), o - c)

        def test_fwdsearch(self):
            enc = self.construct('(((()))())')
            for i in range(len(enc)):
                excess, deltas = enc.excess(i), {}
                for j in range(i + 1, len(enc)):
                    delta = enc.excess(j) - excess
                    if delta not in deltas:
                        deltas[delta] = j
                with self.assertRaises(ValueError):
                    enc.fwdsearch(i, min(deltas) - 1)
                with self.assertRaises(ValueError):
                    enc.fwdsearch(i, max(deltas) + 1)
                for d, tgt in deltas.items():
                    self.assertEqual(enc.fwdsearch(i, d), tgt)

        def test_bwdsearch(self):
            enc = self.construct('(((()))())')
            for i in range(1, len(enc)):
                excess, deltas = enc.excess(i), {}
                for j in reversed(range(i)):
                    delta = enc.excess(j) - excess
                    if delta not in deltas:
                        deltas[delta] = j
                with self.assertRaises(ValueError):
                    enc.bwdsearch(i, min(deltas) - 2)
                with self.assertRaises(ValueError):
                    enc.bwdsearch(i, max(deltas) + 1)
                self.assertEqual(enc.bwdsearch(i, min(deltas) - 1), -1)
                for d, tgt in deltas.items():
                    self.assertEqual(enc.bwdsearch(i, d), tgt)

        def test_firstmin(self):
            enc = self.construct('(((()))())')

            pairs = (
                (-1, 0),
                (0, -1),
                (len(enc), 0),
                (0, len(enc)),
            )
            for i, j in pairs:
                with self.assertRaises(IndexError):
                    enc.firstmin(i, j)
            with self.assertRaises(ValueError):
                enc.firstmin(1, 0)

            for i in range(len(enc)):
                for j in range(i + 1, len(enc)):
                    self.assertEqual(
                        enc.firstmin(i, j),
                        i + argmin(enc.excess(x) for x in range(i, j + 1))
                    )

        def test_firstmax(self):
            enc = self.construct('(((()))())')

            pairs = (
                (-1, 0),
                (0, -1),
                (len(enc), 0),
                (0, len(enc)),
            )
            for i, j in pairs:
                with self.assertRaises(IndexError):
                    enc.firstmin(i, j)
            with self.assertRaises(ValueError):
                enc.firstmin(1, 0)

            for i in range(len(enc)):
                for j in range(i + 1, len(enc)):
                    self.assertEqual(
                        enc.firstmax(i, j),
                        i + argmax(enc.excess(x) for x in range(i, j + 1))
                    )

        def test_countmin(self):
            enc = self.construct('(((()))())')

            for i in range(len(enc)):
                for j in range(i + 1, len(enc)):
                    e = [enc.excess(x) for x in range(i, j + 1)]
                    self.assertEqual(
                        enc.countmin(i, j),
                        sum(1 for x in e if x == min(e))
                    )

        def test_selectmin(self):
            enc = self.construct('(((()))())')

            for i in range(len(enc)):
                for j in range(i + 1, len(enc)):
                    e = [enc.excess(x) for x in range(i, j + 1)]
                    m = [idx for idx, val in enumerate(e, i) if val == min(e)]

                    for k in (-1, 0, len(m) + 1):
                        with self.assertRaises(ValueError):
                            enc.selectmin(i, j, k)

                    for k, idx in enumerate(m, 1):
                        self.assertEqual(
                            enc.selectmin(i, j, k),
                            idx
                        )

        def test_open(self):
            enc = self.construct('(((()))())')
            for idx in range(len(enc)):
                if enc[idx] == '(':
                    with self.assertRaises(ValueError):
                        enc.open(idx)
                    continue
                c, cnt = None, 1
                for c in reversed(range(idx)):
                    if enc[c] == '(':
                        cnt -= 1
                    else:
                        cnt += 1
                    if cnt == 0:
                        break
                self.assertEqual(cnt, 0)
                self.assertEqual(enc.open(idx), c)

        def test_close(self):
            enc = self.construct('(((()))())')
            for idx in range(len(enc)):
                if enc[idx] == ')':
                    with self.assertRaises(ValueError):
                        enc.close(idx)
                    continue
                c, cnt = None, 1
                for c in range(idx + 1, len(enc)):
                    if enc[c] == ')':
                        cnt -= 1
                    else:
                        cnt += 1
                    if cnt == 0:
                        break
                self.assertEqual(cnt, 0)
                self.assertEqual(enc.close(idx), c)

        def test_enclose(self):
            enc = self.construct('(((()))())')
            for idx in range(len(enc)):
                if idx == 0 or idx == len(enc) - 1:
                    with self.assertRaises(ValueError):
                        enc.enclose(idx)
                    continue
                c, stack = None, []
                if enc[idx] == ')':
                    stack.append(')')
                for c in reversed(range(idx)):
                    if enc[c] == '(':
                        if not stack:
                            break
                        else:
                            stack.pop()
                    else:
                        stack.append(')')
                self.assertFalse(stack)
                self.assertEqual(enc.enclose(idx), c)

class TestBPTests(BPTestCases.BPTests):

    def construct(self, sequence):
        return BalancedParentheses(
            bitvector.BitVector(
                encoding.tobits(sequence)
            )
        )
