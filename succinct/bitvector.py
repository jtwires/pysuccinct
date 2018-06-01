import collections

class BitVector(collections.Sequence):
    """models a static bit vector supporting rank/select operations.

    note that the following conditions hold:

    * rank('0', i) + rank('1', i) == i
    * rank(select(x, i)) == i
    * select(rank(x, i)) <= i

    """
    # pylint: disable=W0232

    def rank(self, p, i):
        """return the number of substrings p starting at or before i"""
        raise NotImplementedError()

    def select(self, p, k):
        """return the index of the kth instance of substring p"""
        raise NotImplementedError()
