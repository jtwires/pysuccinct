import unittest

from succinct import bitvector

class BitVector(bitvector.BitVector):

    def __init__(self, bits):
        # pylint: disable=W0231
        assert isinstance(bits, basestring) and all(b in '01' for b in bits)
        self.bits = bits

    def _checkindex(self, i):
        if i < 0 or i >= len(self):
            raise IndexError('index out of range')

    def _checkcount(self, k):
        if k <= 0 or k > len(self):
            raise ValueError('count out of range')

    def _checkpattern(self, p):
        if not isinstance(p, basestring) or not all(b in '01' for b in p):
            raise ValueError('pattern must be a string of 0s and 1s')

    def __str__(self):
        return self.bits

    def __len__(self):
        return len(self.bits)

    def __getitem__(self, i):
        return self.bits[i]

    def append(self, bit):
        assert bit in '01'
        self.bits += bit

    def rank(self, p, i):
        self._checkindex(i)
        self._checkpattern(p)

        return sum(
            1
            for idx in range(i + 1)
            if self[idx:idx + len(p)] == p
        )

    def select(self, p, k):
        self._checkcount(k)
        self._checkpattern(p)

        cnt = k
        for idx in range(len(self)):
            if p == self[idx:idx + len(p)]:
                cnt -= 1
                if cnt == 0:
                    return idx
        raise ValueError('vector has {} {}s (not {})'.format(k - cnt, p, k))

class BitVectorTestCases(object):

    class BitVectorTests(unittest.TestCase):

        def construct(self, bits):
            raise NotImplementedError()

        def test_rank_boundaries(self):
            bv = self.construct('0')

            self.assertEqual(bv.rank('0', 0), 1)

            for p in ('0', '1', '10'):
                with self.assertRaises(IndexError):
                    bv.rank(p, 0 - 1)
                with self.assertRaises(IndexError):
                    bv.rank(p, 0 + 1)

        def test_select_boundaries(self):
            bv = self.construct('0')

            self.assertEqual(bv.select('0', 1), 0)
            with self.assertRaises(ValueError):
                bv.select('0', 2)

            for p in ('1', '10'):
                with self.assertRaises(ValueError):
                    bv.select(p, 1)

        def test_rank(self):
            bv = self.construct('010110')

            for i, v in zip(range(len(bv)), [1, 1, 2, 2, 2, 3]):
                self.assertEqual(bv.rank('0', i), v)

            for i, v in zip(range(len(bv)), [0, 1, 1, 2, 3, 3]):
                self.assertEqual(bv.rank('1', i), v)

            for i, v in zip(range(len(bv)), [0, 1, 1, 1, 2, 2]):
                self.assertEqual(bv.rank('10', i), v)

        def test_select(self):
            bv = self.construct('010110')

            for k, v in zip(range(1, 4), [0, 2, 5]):
                self.assertEqual(bv.select('0', k), v)

            for k, v in zip(range(1, 4), [1, 3, 4]):
                self.assertEqual(bv.select('1', k), v)

            for k, v in zip(range(1, 2), [1, 4]):
                self.assertEqual(bv.select('10', k), v)

class TestBitVectorTests(BitVectorTestCases.BitVectorTests):

    def construct(self, bits):
        return BitVector(bits)
