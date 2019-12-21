import unittest
import collections

from succinct import wavelet

from test import bitvector

class WaveletTree(wavelet.WaveletTree):

    class Node(object):

        def __init__(self):
            self.bv = bitvector.BitVector('')
            self.parent = None
            self.children = {'0': None, '1': None}

        def __str__(self, indent=''):
            left, right = self.children['0'], self.children['1']
            s = str(self.bv)
            if left and left.bv:
                s += '\n{}L:{}'.format(indent, left.__str__(indent + '  '))
            if right and right.bv:
                s += '\n{}R:{}'.format(indent, right.__str__(indent + '  '))
            return s

    def __init__(self, text, codec=None):
        # pylint: disable=W0231
        self.codec = codec or wavelet.ASCIICodec()
        self.root = self.Node()

        for sym in text:
            code, node = self.codec.encode(sym), self.root
            for bit in code:
                node.bv.append(bit)
                child = node.children[bit]
                if not child:
                    child = self.Node()
                    child.parent = node
                    node.children[bit] = child
                node = child

    def __str__(self):
        return str(self.root)

    def __len__(self):
        return len(self.root.bv)

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return ''.join(self[i] for i in xrange(*idx.indices(len(self))))
        if idx < 0:
            idx += len(self)
        if idx < 0 or idx >= len(self):
            raise IndexError('index out of range')

        code, node = [], self.root

        while node.bv:
            bit = node.bv[idx]
            code.append(bit)
            idx = node.bv.rank(bit, idx) - 1
            node = node.children[bit]

        return self.codec.decode(int(''.join(code), 2))

    def rank(self, c, i):
        if i < 0 or i >= len(self.root.bv):
            raise IndexError('index out of range')

        idx, code, node = i, iter(self.codec.encode(c)), self.root

        while node.bv:
            bit = next(code)
            cnt = node.bv.rank(bit, idx)
            if not cnt:
                break
            idx = cnt - 1
            node = node.children[bit]

        return cnt

    def select(self, c, k):
        if k <= 0 or k > len(self.root.bv):
            raise ValueError('count out of range')

        cnt, code, node = k, self.codec.encode(c), self.root

        for bit in code:
            node = node.children[bit]
            if not node:
                raise ValueError("'{}' does not occur in text".format(c))

        for bit in reversed(code):
            node = node.parent
            try:
                idx = node.bv.select(bit, cnt)
            except ValueError:
                raise ValueError(
                    "'{}' occurs in text fewer than {} times".format(c, k)
                )
            cnt = idx + 1

        return idx

class CodecTestCases(object):

    class CodecTests(unittest.TestCase):

        def construct(self, text):
            raise NotImplementedError()

        def test_empty(self):
            self.construct('')

        def test_codec(self):
            text = 'this is the winter of our discontent'
            codec = self.construct(text)

            self.assertEqual(
                text,
                ''.join(codec.decode(codec.encode(sym)) for sym in text)
            )

class ASCIICodecTests(CodecTestCases.CodecTests):

    def construct(self, text):
        return wavelet.ASCIICodec()

class HuffmanCodecTests(CodecTestCases.CodecTests):

    def construct(self, text):
        return wavelet.HuffmanCodec(text)

    def test_compression(self):
        text = 'this is the winter of our discontent'
        codec = self.construct(text)

        frequencies = collections.defaultdict(int)
        for sym in text:
            frequencies[sym] += 1

        table = sorted(frequencies.items(), key=lambda item: item[1])
        for idx, (sym, cnt) in enumerate(table):
            code = codec.encode(sym)
            for nxt in table[idx:]:
                if cnt > nxt[1]:
                    self.assertLessEqual(len(code), len(codec.encode(nxt[0])))

class HuTuckerCodecTests(unittest.TestCase):

    def test_ht(self):
        codec = wavelet.HuTuckerCodec('AAABBCDDDDEEEEE')

class WaveletTreeTestCases(object):

    class WaveletTreeTests(unittest.TestCase):

        def construct(self, text):
            raise NotImplementedError()

        def test_access(self):
            text = 'to be or not to be'
            tree = self.construct(text)

            self.assertEqual(tree[0], text[0])
            self.assertEqual(tree[-1], text[-1])
            self.assertEqual(tree[1:3], text[1:3])
            self.assertEqual(tree[::-1], text[::-1])
            self.assertEqual(list(tree), list(text))

        def test_rank(self):
            text = 'to be or not to be'
            tree = self.construct(text)

            for c in text:
                for i in xrange(len(text)):
                    self.assertEqual(
                        tree.rank(c, i),
                        sum(1 for x in text[:i + 1] if x == c)
                    )

        def test_select(self):
            text = 'to be or not to be'
            tree = self.construct(text)

            for c in text:
                positions = (i for i, x in enumerate(text) if x == c)
                for cnt, pos in enumerate(positions, 1):
                    self.assertEqual(tree.select(c, cnt), pos)

        def test_boundaries(self):
            text = 'to be or not to be'
            tree = self.construct(text)

            with self.assertRaises(IndexError):
                self.assertEqual(tree[len(text)], None)
            with self.assertRaises(IndexError):
                self.assertEqual(tree[-len(text) - 1], None)

            with self.assertRaises(IndexError):
                self.assertEqual(tree.rank('t', -1), None)
            with self.assertRaises(IndexError):
                self.assertEqual(tree.rank('t', len(text)), None)
            self.assertEqual(tree.rank('x', len(text) - 1), 0)

            with self.assertRaises(ValueError):
                self.assertEqual(tree.select('t', 0), None)
            with self.assertRaises(ValueError):
                self.assertEqual(tree.select('t', 4), None)
            with self.assertRaises(ValueError):
                self.assertEqual(tree.select('x', 1), None)

class TestWaveletTreeTests(WaveletTreeTestCases.WaveletTreeTests):

    def construct(self, text):
        return WaveletTree(text)
