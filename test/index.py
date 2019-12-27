import textwrap
import unittest
import collections

from succinct import index

class SA(index.Index):
    """naive suffix array implementation"""

    def __init__(self, text, array):
        super(SA, self).__init__()
        self.text = text
        self.array = array

    def __len__(self):
        return len(self.text)

    def __getitem__(self, idx):
        return self.text[idx]

    def count(self, value):
        start, end = self._search(value)
        return end - start + 1

    def index(self, value):
        try:
            return next(iter(sorted(self.indexes(value))))
        except StopIteration:
            raise ValueError()

    def indexes(self, value):
        start, end = self._search(value)
        for idx in range(start, end + 1):
            yield self.array[idx]

    def _search(self, value):
        # binary search for first and last suffix containing @string
        if not value:
            # match behavior for string.count
            return 0, len(self) + 1
        m = len(value)
        sp, st = 0, len(self) - 1
        while sp < st:
            idx = (sp + st) // 2
            off = self.array[idx]
            if value > self.text[off:off + m]:
                sp = idx + 1
            else:
                st = idx
        ep, et = sp - 1, len(self) - 1
        while ep < et:
            idx = (ep + et) // 2 + ((ep + et) & 1)
            off = self.array[idx]
            if value == self.text[off:off + m]:
                ep = idx
            else:
                et = idx - 1
        return sp, ep

    @classmethod
    def build(cls, text):
        suffixes = ((text[i:], i) for i in range(len(text)))
        return cls(text, tuple(i for _, i in sorted(suffixes)))

class CSA(index.Index):
    """naive compressed suffix array implementation"""

    def __init__(self, offsets, predecessors):
        super(CSA, self).__init__()
        self.offsets = offsets
        self.predecessors = predecessors

    def __len__(self):
        return len(self.predecessors)

    def __getitem__(self, idx):
        raise NotImplementedError()

    def index(self, value):
        raise NotImplementedError()

    def indexes(self, value):
        raise NotImplementedError()

    def count(self, value):
        # `backward search` to count suffixes containing @string
        if not value:
            # match behavior for string.count
            return len(self.predecessors) + 1
        s, e, soff, eoff = 1, 0, 0, 0
        for idx in reversed(range(len(value))):
            c, p = value[idx], '' if not idx else value[idx - 1]
            try:
                s, e = self.offsets[c]
            except KeyError:
                return 0
            s += soff
            e -= eoff
            soff = sum(1 for x in self.predecessors[:s] if x == p)
            eoff = sum(1 for x in self.predecessors[e:] if x == p)
        return e - s

    @classmethod
    def build(cls, text):
        suffixes = ((text[i:], i) for i in range(len(text)))

        offsets, predecessors, n, p = {}, [], len(text), None
        for idx, (sfx, off) in enumerate(sorted(suffixes)):
            predecessors.append('' if not off else text[off - 1])
            c = '' if not sfx else sfx[0]
            if c != p:
                prv = offsets.get(p)
                if prv:
                    offsets[p] = prv[0], idx
                p, offsets[c] = c, (idx, n)

        return cls(offsets, predecessors)

class IndexTestCases(object):

    class IndexTests(unittest.TestCase):

        SMALL = textwrap.dedent(
            """

            The mass of men lead lives of quiet desperation. What is
            called resignation is confirmed desperation.

            """
        )

        LARGE = textwrap.dedent(
            """

            I went to the woods because I wished to live deliberately,
            to front only the essential facts of life, and see if I
            could not learn what it had to teach, and not, when I came
            to die, discover that I had not lived. I did not wish to
            live what was not life, living is so dear; nor did I wish
            to practise resignation, unless it was quite necessary. I
            wanted to live deep and suck out all the marrow of life,
            to live so sturdily and Spartan-like as to put to rout all
            that was not life, to cut a broad swath and shave close,
            to drive life into a corner, and reduce it to its lowest
            terms, and, if it proved to be mean, why then to get the
            whole and genuine meanness of it, and publish its meanness
            to the world; or if it were sublime, to know it by
            experience, and be able to give a true account of it in my
            next excursion.

            """
        )

        def construct(self, text):
            raise NotImplementedError()

        def index(self, text):
            lookup = collections.defaultdict(list)
            for word in text.split():
                if word in lookup:
                    continue
                for i in range(len(text)):
                    if word == text[i:i + len(word)]:
                        lookup[word].append(i)
            return lookup

        def validate(self, text):
            lookup = self.index(text)

            idx = self.construct(text)
            self.assertEqual(len(idx), len(text))

            for word in list(lookup) + ['christmas']:
                self.assertEqual(
                    idx.count(word),
                    len(lookup[word]),
                )
                try:
                    self.assertEqual(
                        idx.index(word),
                        lookup[word][0],
                    )
                except ValueError:
                    self.assertFalse(word in idx)
                    self.assertFalse(word in text)
                self.assertEqual(
                    list(sorted(idx.indexes(word))),
                    lookup[word],
                )

        def test_index_empty(self):
            idx = self.construct('')
            self.assertIn('', idx)
            self.assertNotIn('foo', idx)

        def test_match_empty(self):
            self.assertIn('', self.construct('foo'))

        def test_match_all(self):
            self.assertIn('foo', self.construct('foo'))

        def test_match_first(self):
            self.assertIn('foo', self.construct('foo bar'))

        def test_match_last(self):
            self.assertIn('foo', self.construct('bar foo'))

        def test_match_boundaries(self):
            self.assertEqual(self.construct('foo bar foo').count('foo'), 2)

        def test_small(self):
            self.validate(self.SMALL)

        def test_large(self):
            self.validate(self.LARGE)

class SATests(IndexTestCases.IndexTests):

    def construct(self, text):
        return SA.build(text)

class CSATests(IndexTestCases.IndexTests):

    def construct(self, text):
        return CSA.build(text)

    def validate(self, text):
        lookup = self.index(text)

        idx = self.construct(text)
        self.assertEqual(len(idx), len(text))

        for word in list(lookup) + ['christmas']:
            self.assertEqual(
                idx.count(word),
                len(lookup[word]),
                word
            )
