import unittest

from succinct import tree

from test import (
    bitvector,
    encoding,
)

def getpos(n):
    return n if n is None else n.pos

class TreeTestCases(object):

    class TreeTests(unittest.TestCase):
        #                      1
        #                   /  |  \
        #                  2   7   8
        #                / | \     |
        #               3  4  5    9
        #                     |   / \
        #                     6  A   B
        #
        #       +--------------1-----------+
        #       |+-----2-----+   +----8---+|
        #       ||      +-5-+|   |+--9---+||
        #       || 3  4 | 6 || 7 || A  B |||
        TREE = '((( )( )(( )))( )((( )( ))))'.replace(' ', '')
        #  pos: 012 34 567 89AB CDEF GH IJKL
        #  exc: 123 23 234 3212 1234 34 3210

        PREORDER = [0, 1, 2, 4, 6, 7, 11, 13, 14, 15, 17]
        POSTORDER = [2, 4, 7, 6, 1, 11, 15, 17, 14, 13, 0]
        LEAFORDER = [2, 4, 7, 11, 15, 17]

        def construct(self, sequence):
            raise NotImplementedError()

        def test_root(self):
            t = self.construct(self.TREE)
            self.assertEqual(t.root().pos, 0)

        def test_getitem(self):
            t = self.construct(self.TREE)
            m = self.PREORDER[:]
            for idx, val in enumerate(m):
                self.assertEqual(t[idx].pos, val)
            self.assertEqual(t[-1].pos, m[-1])
            self.assertEqual([n.pos for n in t[:]], m[:])
            self.assertEqual([n.pos for n in t[1:3]], m[1:3])

        def test_iterate(self):
            t = self.construct(self.TREE)
            m = self.PREORDER[:]
            self.assertEqual(
                [n.pos for n in t],
                m
            )
            self.assertEqual(
                [n.pos for n in reversed(t)],
                list(reversed(m))
            )
            self.assertEqual(
                [n.pos for n in t[::-1]],
                m[::-1]
            )
            self.assertEqual(
                [n.pos for n in t.iterate(preorder=False)],
                self.POSTORDER,
            )
            self.assertEqual(
                [n.pos for n in t[2:]],
                m[2:]
            )

        def test_preorder(self):
            t = self.construct(self.TREE)
            m = self.PREORDER[:]
            for k, pos in enumerate(m):
                self.assertEqual(t.select(k), pos)
                self.assertEqual(t.rank(pos), k)

        def test_postorder(self):
            t = self.construct(self.TREE)
            m = self.POSTORDER[:]
            for k, pos in enumerate(m):
                self.assertEqual(t.postselect(k), pos)
                self.assertEqual(t.postrank(pos), k)

        def test_leaforder(self):
            t = self.construct(self.TREE)
            m = self.LEAFORDER[:]
            for k, pos in enumerate(m):
                self.assertEqual(t.leafselect(k), pos)
                self.assertEqual(t.leafrank(pos - 1), k - 1)
                self.assertEqual(t.leafrank(pos), k)

        def test_isleaf(self):
            t = self.construct(self.TREE)
            for k, n in enumerate(t, 1):
                self.assertEqual(
                    n.isleaf(),
                    k in (3, 4, 6, 7, 10, 11)
                )

        def test_isancestor(self):
            t = self.construct(self.TREE)
            m = (
                [True] * 11,
                [False] + [True] * 5 + [False] * 5,
                [False] * 2 + [True] + [False] * 8,
                [False] * 3 + [True] + [False] * 7,
                [False] * 4 + [True] * 2 + [False] * 5,
                [False] * 5 + [True] + [False] * 5,
                [False] * 6 + [True] + [False] * 4,
                [False] * 7 + [True] * 4,
                [False] * 8 + [True] * 3,
                [False] * 9 + [True] + [False],
                [False] * 10 + [True],
            )
            for k, n in enumerate(t):
                for x, val in zip(t, m[k]):
                    self.assertEqual(
                        n.isancestor(x),
                        val
                    )

        def test_depth(self):
            t = self.construct(self.TREE)
            m = (1, 2, 3, 3, 3, 4, 2, 2, 3, 4, 4)
            for n, d in zip(t, m):
                self.assertEqual(n.depth(), d)

        def test_height(self):
            t = self.construct(self.TREE)
            m = (3, 2, 0, 0, 1, 0, 0, 2, 1, 0, 0)
            for n, h in zip(t, m):
                self.assertEqual(n.height(), h)

        def test_parent(self):
            t = self.construct(self.TREE)
            m = (None, 0, 1, 1, 1, 6, 0, 0, 13, 14, 14)
            for n, pos in zip(t, m):
                self.assertEqual(getpos(n.parent()), pos)

        def test_degree(self):
            t = self.construct(self.TREE)
            m = (3, 3, 0, 0, 1, 0, 0, 1, 2, 0, 0)
            for n, d in zip(t, m):
                self.assertEqual(n.degree(), d)

        def test_size(self):
            t = self.construct(self.TREE)
            m = (11, 5, 1, 1, 2, 1, 1, 4, 3, 1, 1)
            for n, s in zip(t, m):
                self.assertEqual(n.size(), s)

        def test_numleaves(self):
            t = self.construct(self.TREE)
            m = (6, 3, 1, 1, 1, 1, 1, 2, 2, 1, 1)
            for n, cnt in zip(t, m):
                self.assertEqual(n.numleaves(), cnt)

        def test_children(self):
            t = self.construct(self.TREE)
            m = [
                [1, 11, 13],
                [2, 4, 6],
                [],
                [],
                [7],
                [],
                [],
                [14],
                [15, 17],
                [],
                []
            ]
            for k, n in enumerate(t):
                self.assertEqual(
                    [c.pos for c in n.children()],
                    m[k]
                )

        def test_nextsibling(self):
            t = self.construct(self.TREE)
            m = [None, 11, 4, 6, None, None, 13, None, None, 17, None]
            for n, nxt in zip(t, m):
                self.assertEqual(
                    getpos(n.nextsibling()),
                    nxt
                )

        def test_prevsibling(self):
            t = self.construct(self.TREE)
            m = [None, None, None, 2, 4, None, 1, 11, None, None, 15]
            for n, prv in zip(t, m):
                self.assertEqual(
                    getpos(n.prevsibling()),
                    prv
                )

        def test_ancestor(self):
            t = self.construct(self.TREE)
            m = [
                [(1, None), (0, 0)],
                [(2, None), (1, 0), (0, 1)],
                [(3, None), (2, 0), (1, 1), (0, 2)],
                [(3, None), (2, 0), (1, 1), (0, 4)],
                [(3, None), (2, 0), (1, 1), (0, 6)],
                [(4, None), (3, 0), (2, 1), (1, 6), (0, 7)],
                [(2, None), (1, 0), (0, 11)],
                [(2, None), (1, 0), (0, 13)],
                [(3, None), (2, 0), (1, 13), (0, 14)],
                [(4, None), (3, 0), (2, 13), (1, 14), (0, 15)],
                [(4, None), (3, 0), (2, 13), (1, 14), (0, 17)],
            ]
            for n, cases in zip(t, m):
                for d, pos in cases:
                    self.assertEqual(
                        getpos(n.ancestor(d)),
                        pos
                    )

        def test_lca(self):
            t = self.construct(self.TREE)
            m = {
                (0, 0): 0,
                (0, 1): 0,
                (0, 2): 0,
                (0, 3): 0,
                (0, 4): 0,
                (0, 5): 0,
                (0, 6): 0,
                (0, 7): 0,
                (0, 8): 0,
                (0, 9): 0,
                (0, 10): 0,
                (1, 0): 0,
                (1, 1): 1,
                (1, 2): 1,
                (1, 3): 1,
                (1, 4): 1,
                (1, 5): 1,
                (1, 6): 0,
                (1, 7): 0,
                (1, 8): 0,
                (1, 9): 0,
                (1, 10): 0,
                (2, 0): 0,
                (2, 1): 1,
                (2, 2): 2,
                (2, 3): 1,
                (2, 4): 1,
                (2, 5): 1,
                (2, 6): 0,
                (2, 7): 0,
                (2, 8): 0,
                (2, 9): 0,
                (2, 10): 0,
                (3, 0): 0,
                (3, 1): 1,
                (3, 2): 1,
                (3, 3): 3,
                (3, 4): 1,
                (3, 5): 1,
                (3, 6): 0,
                (3, 7): 0,
                (3, 8): 0,
                (3, 9): 0,
                (3, 10): 0,
                (4, 0): 0,
                (4, 1): 1,
                (4, 2): 1,
                (4, 3): 1,
                (4, 4): 4,
                (4, 5): 4,
                (4, 6): 0,
                (4, 7): 0,
                (4, 8): 0,
                (4, 9): 0,
                (4, 10): 0,
                (5, 0): 0,
                (5, 1): 1,
                (5, 2): 1,
                (5, 3): 1,
                (5, 4): 4,
                (5, 5): 5,
                (5, 6): 0,
                (5, 7): 0,
                (5, 8): 0,
                (5, 9): 0,
                (5, 10): 0,
                (6, 0): 0,
                (6, 1): 0,
                (6, 2): 0,
                (6, 3): 0,
                (6, 4): 0,
                (6, 5): 0,
                (6, 6): 6,
                (6, 7): 0,
                (6, 8): 0,
                (6, 9): 0,
                (6, 10): 0,
                (7, 0): 0,
                (7, 1): 0,
                (7, 2): 0,
                (7, 3): 0,
                (7, 4): 0,
                (7, 5): 0,
                (7, 6): 0,
                (7, 7): 7,
                (7, 8): 7,
                (7, 9): 7,
                (7, 10): 7,
                (8, 0): 0,
                (8, 1): 0,
                (8, 2): 0,
                (8, 3): 0,
                (8, 4): 0,
                (8, 5): 0,
                (8, 6): 0,
                (8, 7): 7,
                (8, 8): 8,
                (8, 9): 8,
                (8, 10): 8,
                (9, 0): 0,
                (9, 1): 0,
                (9, 2): 0,
                (9, 3): 0,
                (9, 4): 0,
                (9, 5): 0,
                (9, 6): 0,
                (9, 7): 0,
                (9, 8): 8,
                (9, 9): 9,
                (9, 10): 8,
                (10, 0): 0,
                (10, 1): 0,
                (10, 2): 0,
                (10, 3): 0,
                (10, 4): 0,
                (10, 5): 0,
                (10, 6): 0,
                (10, 7): 7,
                (10, 8): 7,
                (10, 9): 7,
                (10, 10): 10,
            }
            for i, n in enumerate(t):
                for j, o in enumerate(t[i:], i):
                    self.assertEqual(
                        n.lca(o).rank(),
                        m[(i, j)]
                    )
                    self.assertEqual(
                        o.lca(n).rank(),
                        m[(i, j)]
                    )

        def test_levelnext(self):
            t = self.construct(self.TREE)
            m = (None, 11, 4, 6, 14, 15, 13, None, None, 17, None)
            for n, pos in zip(t, m):
                self.assertEqual(
                    getpos(n.levelnext()),
                    pos
                )

        def test_levelprev(self):
            t = self.construct(self.TREE)
            m = (None, None, None, 2, 4, None, 1, 11, 6, 7, 15)
            for n, pos in zip(t, m):
                self.assertEqual(
                    getpos(n.levelprev()),
                    pos
                )

        def test_deepestnode(self):
            t = self.construct(self.TREE)
            m = (7, 7, None, None, 7, None, None, 15, 15, None, None)
            for n, pos in zip(t, m):
                self.assertEqual(
                    getpos(n.deepestnode()),
                    pos
                )

        def test_leftmostleaf(self):
            t = self.construct(self.TREE)
            m = (2, 2, None, None, 7, None, None, 15, 15, None, None)
            for n, pos in zip(t, m):
                self.assertEqual(
                    getpos(n.leftmostleaf()),
                    pos
                )

        def test_rightmostleaf(self):
            t = self.construct(self.TREE)
            m = (17, 7, None, None, 7, None, None, 17, 17, None, None)
            for n, pos in zip(t, m):
                self.assertEqual(
                    getpos(n.rightmostleaf()),
                    pos
                )

        def test_levelleftmost(self):
            t = self.construct(self.TREE)
            m = ((0, None), (1, 0), (2, 1), (3, 2), (4, 7), (5, None))
            for d, pos in (m):
                self.assertEqual(
                    getpos(t.levelleftmost(d)),
                    pos
                )

        def test_levelrightmost(self):
            t = self.construct(self.TREE)
            m = ((0, None), (1, 0), (2, 13), (3, 14), (4, 17), (5, None))
            for d, pos in (m):
                self.assertEqual(
                    getpos(t.levelrightmost(d)),
                    pos
                )

class TestTreeTests(TreeTestCases.TreeTests):

    def construct(self, sequence):
        return tree.Navigator(
            encoding.BalancedParentheses(
                bitvector.BitVector(
                    sequence.replace('(', '1').replace(')', '0')
                )
            )
        )
