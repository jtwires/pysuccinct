import numbers
import collections

from succinct import bitvector

def tobits(p):
    """convert parentheses to bits"""
    return p.replace('(', '1').replace(')', '0')

def toparens(b):
    """convert bits to parentheses"""
    return b.replace('1', '(').replace('0', ')')

class BalancedParentheses(collections.Sequence):
    """models an ordinal tree as a sequence of balanced parantheses.

    given a tree with N nodes, each node is represented by a matching
    pair of opening/closing parentheses (encoded as 1/0, respectively,
    in a bitvector of size 2N).

    excess(i) gives the number of opening parentheses minus the
    number of closing parentheses up to and including index i. the
    following properties hold for all BalancedParentheses encodings:

    * excess(i) = rank('1', i) - rank('0', i) = 2 * rank('1', i) - i
    * all(abs(excess(i) - excess(i - 1)) == 1 for i in range(1, N))
    * all(excess(i) >= 0 for i in range(N))
    * excess(2N) == 0

    """
    # pylint: disable=W0231

    def __init__(self, bv):
        assert isinstance(bv, bitvector.BitVector)
        self.bv = bv

        if not self._balanced():
            raise ValueError("encoding '{}' not balanced".format(self))

    def _balanced(self):
        """return True iff parentheses are balanced"""
        ok = len(self) and len(self) % 2 == 0
        ok = ok and self[0] == '(' and self[-1] == ')'
        ok = ok and all(self.excess(i) >= 0 for i in range(len(self)))
        ok = ok and self.excess(len(self) - 1) == 0
        ok = ok and all(
            abs(self.excess(i) - self.excess(i - 1)) == 1
            for i in range(1, len(self))
        )
        for i in range(len(self)):
            if not ok:
                break
            if self[i] != '(':
                continue
            close = self.close(i)
            ok = ok and close > i
            ok = ok and self.excess(close) == self.excess(i) - 1
            for m in range(i + 1, close):
                if not ok:
                    break
                if self[m] != '(':
                    continue
                ok = ok and self.close(m) < close
                ok = ok and self.excess(m) >= self.excess(i)
        return ok

    def __str__(self):
        return toparens(str(self.bv))

    def __len__(self):
        return len(self.bv)

    def __nonzero__(self):
        return len(self) > 0

    def __getitem__(self, i):
        return toparens(self.bv[i])

    def rank(self, p, i):
        """return the number of substrings p starting at or before i"""
        return self.bv.rank(tobits(p), i)

    def select(self, p, k):
        """return the index of the kth instance of substring p"""
        return self.bv.select(tobits(p), k)

    def excess(self, i):
        """return number of '('s minus number of ')'s up to i"""
        return 2 * self.rank('(', i) - (i + 1)

    def open(self, i):
        """return max{j < i, excess(j - 1) = excess(i)}"""
        if self[i] != ')':
            raise ValueError("open({}) called on '('".format(i))
        return self.bwdsearch(i, 0) + 1

    def close(self, i):
        """return min{j > i, excess(j) = excess(i) - 1}"""
        if self[i] != '(':
            raise ValueError("close({} called on ')'".format(i))
        return self.fwdsearch(i, -1)

    def enclose(self, i):
        """return max{j < i, excess(j - 1) = excess(i) - 2}"""
        if i == 0 or i == len(self) - 1:
            raise ValueError("no node encloses the root")
        if self[i] == ')':
            i = self.open(i)
        return self.bwdsearch(i, -2) + 1

    def fwdsearch(self, i, d):
        """return min{j > i, excess(j) = excess(i) + d}"""
        raise NotImplementedError()

    def bwdsearch(self, i, d):
        """return max{j < i, excess(j) = excess(i) + d}"""
        raise NotImplementedError()

    def firstmin(self, i, j):
        """return position of first minimum in excess(i) ... excess(j)"""
        raise NotImplementedError()

    def firstmax(self, i, j):
        """return position of first maximum in excess(i) ... excess(j)"""
        raise NotImplementedError()

    def countmin(self, i, j):
        """return the number of occurrences of the minimum excess"""
        raise NotImplementedError()

    def selectmin(self, i, j, k):
        """return the position of the kth minimum excess"""
        raise NotImplementedError()

class EliasFano(collections.Sequence):

    def __init__(self, data):  # pylint: disable=W0231
        if isinstance(data, bitvector.BitVector):
            data = [idx for idx, val in enumerate(data) if val == '1']
        assert all(isinstance(val, numbers.Integral) for val in data)
        self.data = data

    def __nonzero__(self):
        return len(self) > 0

    def __len__(self):
        return len(self.data)

    def __str__(self):
        return str(list(self))

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return [self[i] for i in range(*idx.indices(len(self)))]
        if not isinstance(idx, numbers.Integral):
            raise TypeError('indices must be integers')
        if idx < 0:
            idx += len(self)
        if idx < 0 or idx >= len(self):
            raise IndexError('index out of range')
        return self.data[idx]
