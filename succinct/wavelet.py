"""wavelet tree and binary codes.

wavelet trees [1, 2] are succinct data structures that provide access,
rank, and select queries over texts of arbitrary alphabets. when
combined with hu-tucker codes [3], they can store a text S with
alphabet of size sigma in nH(S) + O(n log log n / log_sigma n) bits,
where H(S) is the zeroth-order entropy of the text. all queries are
answered in in O(log sigma) time.

[1] Grossi, Roberto, Ankur Gupta, and Jeffrey Scott
Vitter. "High-order entropy-compressed text indexes." Proceedings of
the fourteenth annual ACM-SIAM symposium on Discrete
algorithms. Society for Industrial and Applied Mathematics, 2003.

[2] Navarro, Gonzalo, and Veli Makinen. "Compressed full-text
indexes." ACM Computing Surveys (CSUR) 39.1 (2007): 2.

[3] Hu, Te C., and Alan C. Tucker. "Optimal computer search trees and
variable-length alphabetical codes." SIAM Journal on Applied
Mathematics 21.4 (1971): 514-532.

"""

import collections

class Codec(object):
    """maps alphabet symbols to their binary encodings"""

    def encode(self, sym):
        """return the binary encoding of @sym"""
        raise NotImplementedError()

    def decode(self, code):
        """return the symbol corresponding to @code"""
        raise NotImplementedError()

class ASCIICodec(Codec):
    """standard ASCII code"""

    def encode(self, sym):
        return bin(ord(sym))[2:].zfill(7)

    def decode(self, code):
        return chr(code)

class WaveletTree(collections.Sequence):
    # pylint: disable=W0232

    def __nonzero__(self):
        return len(self) > 0

    def rank(self, c, i):
        """return the number of times symbol c occurs at or before index i"""
        raise NotImplementedError()

    def select(self, c, k):
        """return the index of the kth occurrence of symbol c"""
        raise NotImplementedError()
