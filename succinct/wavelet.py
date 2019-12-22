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

import heapq
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
        return chr(int(code, 2))

class HuffmanCodec(Codec):
    """huffman code"""

    def __init__(self, text):
        self.syms = {}
        self.codes = {}

        if not text:
            return

        class Node(object):

            def __init__(self):
                self.cnt = 0
                self.sym = None
                self.left = None
                self.right = None

            def __lt__(self, other):
                return self.cnt < other.cnt

        heap, nodes = [], collections.defaultdict(Node)
        for sym in text:
            node = nodes[sym]
            node.cnt += 1
            if node.cnt == 1:
                node.sym = sym
                heap.append(node)
                nodes[sym] = node

        heapq.heapify(heap)
        while len(heap) > 1:
            node = Node()
            node.left, node.right = heapq.heappop(heap), heapq.heappop(heap)
            node.cnt = node.left.cnt + node.right.cnt
            heapq.heappush(heap, node)

        stack = [(heap[0], '')]
        while stack:
            node, code = stack.pop()
            if node.sym:
                self.syms[code] = node.sym
                self.codes[node.sym] = code
            else:
                stack.append((node.right, code + '1'))
                stack.append((node.left, code + '0'))

    def encode(self, sym):
        if sym not in self.codes:
            raise ValueError('invalid symbol {}'.format(sym))
        return self.codes[sym]

    def decode(self, code):
        if code not in self.syms:
            raise ValueError('invalid code {}'.format(code))
        return self.syms[code]

class HuTuckerCodec(Codec):
    """hu tucker code - a huffman code that preserves alphabet sort order"""

    def __init__(self, text):
        self.syms = {}
        self.codes = {}

        if not text:
            return

        class Node(object):

            def __init__(self, cnt=0):
                self.cnt = cnt
                self.sym = None
                self.left = None
                self.right = None

            def __str__(self):
                return '{}: {}'.format(self.sym, self.cnt)

        # calculate frequencies
        leaves = collections.defaultdict(Node)
        for sym in text:
            leaf = leaves[sym]
            leaf.cnt += 1
            if leaf.cnt == 1:
                leaf.sym = sym

        # build intermediary tree by merging nodes
        # according to the garsia-wachs algorithm
        alphabet = sorted(leaves)
        nodes = [leaves[sym] for sym in alphabet]
        while len(nodes) > 1:
            tgt = len(nodes) - 1
            for idx, node in enumerate(nodes):
                if idx <= 0 or idx >= len(nodes) - 1:
                    continue
                if nodes[idx - 1].cnt <= nodes[idx + 1].cnt:
                    tgt = idx
                    break
            left, right = nodes[tgt - 1], nodes[tgt]
            node = Node(cnt=left.cnt + right.cnt)
            node.left, node.right = left, right
            for ins in reversed(xrange(1, tgt)):
                if nodes[ins - 1].cnt >= node.cnt:
                    nodes.insert(ins, node)
                    break
            else:
                nodes.insert(0, node)
            nodes.remove(left)
            nodes.remove(right)

        # calculate depths of leaf nodes
        stack, depths = [(nodes[0], 0)], {}
        while stack:
            node, depth = stack.pop()
            if node.sym:
                depths[node.sym] = depth
            else:
                stack.append((node.right, depth + 1))
                stack.append((node.left, depth + 1))

        # build new tree with leaf nodes at same depth
        # but in alphabetic order
        root = Node()
        paths = [(root, 0)]
        for sym in alphabet:
            while True:
                node, depth = paths.pop()
                if depths[sym] == depth:
                    node.sym = sym
                    break
                if depths[sym] > depth:
                    node.left, node.right = Node(), Node()
                    paths.append((node.right, depth + 1))
                    paths.append((node.left, depth + 1))

        # generate codes
        stack = [(root, '')]
        while stack:
            node, code = stack.pop()
            if node.sym:
                self.syms[code] = node.sym
                self.codes[node.sym] = code
            else:
                stack.append((node.right, code + '1'))
                stack.append((node.left, code + '0'))

    def encode(self, sym):
        if sym not in self.codes:
            raise ValueError('invalid symbol {}'.format(sym))
        return self.codes[sym]

    def decode(self, code):
        if code not in self.syms:
            raise ValueError('invalid code {}'.format(code))
        return self.syms[code]

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
