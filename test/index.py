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

    def __contains__(self, string):
        return self.count(string) > 0

    def count(self, string):
        start, end = self._search(string)
        return end - start + 1

    def index(self, string):
        try:
            return next(iter(sorted(self.indexes(string))))
        except StopIteration:
            raise ValueError()

    def indexes(self, string):
        start, end = self._search(string)
        for idx in range(start, end + 1):
            yield self.array[idx]

    def _search(self, string):
        m = len(string)
        sp, st = 0, len(self) - 1
        while sp < st:
            idx = (sp + st) // 2
            off = self.array[idx]
            if string > self.text[off:off + m]:
                sp = idx + 1
            else:
                st = idx
        ep, et = sp - 1, len(self) - 1
        while ep < et:
            idx = (ep + et) // 2 + ((ep + et) & 1)
            off = self.array[idx]
            if string == self.text[off:off + m]:
                ep = idx
            else:
                et = idx - 1
        return sp, ep

    @classmethod
    def build(cls, text):
        suffixes = ((text[i:], i) for i in range(len(text)))
        return cls(text, tuple(i for _, i in sorted(suffixes)))

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

        def validate(self, text):
            words, indexes = text.split(), collections.defaultdict(list)
            for word in words:
                if word in indexes:
                    continue
                for i in range(len(text)):
                    if word == text[i:i + len(word)]:
                        indexes[word].append(i)

            idx = self.construct(text)
            self.assertEqual(len(idx), len(text))

            for word in words + ['christmas']:
                self.assertEqual(
                    idx.count(word),
                    len(indexes[word]),
                )
                try:
                    self.assertEqual(
                        idx.index(word),
                        indexes[word][0],
                    )
                except ValueError:
                    self.assertFalse(word in idx)
                    self.assertFalse(word in text)
                self.assertEqual(
                    list(sorted(idx.indexes(word))),
                    indexes[word],
                )

        def test_small(self):
            self.validate(self.SMALL)

        def test_large(self):
            self.validate(self.LARGE)

class SATests(IndexTestCases.IndexTests):

    def construct(self, text):
        return SA.build(text)
