import numbers
import collections

from succinct import encoding

class Node(object):
    """models a tree node"""

    def __init__(self, nav, pos):
        assert isinstance(nav, Navigator)
        if nav.enc[pos] != '(':
            raise ValueError('no node at position {}'.format(pos))
        self.nav = nav
        self.pos = pos

    def __str__(self):
        return 'Node(pos={})'.format(self.pos)

    def isleaf(self):
        """return True iff this node is a leaf"""
        return self.nav.enc[self.pos + 1] == ')'

    def isancestor(self, n):
        """return True iff this node is an ancestor of node n"""
        assert isinstance(n, Node)
        return self.pos <= n.pos and n.pos < self.nav.enc.close(self.pos)

    def depth(self):
        """return this node's depth"""
        return self.nav.enc.excess(self.pos)

    def height(self):
        """return this node's height (distance to its deepest descendant)"""
        if self.isleaf():
            return 0
        return (
            self.nav.enc.excess(self.deepestnode().pos) -
            self.nav.enc.excess(self.pos)
        )

    def parent(self):
        """return this node's parent"""
        if self.pos == 0:
            return None
        return self.nav.node(self.nav.enc.enclose(self.pos))

    def degree(self):
        """return the number of children of this node"""
        if self.isleaf():
            return 0
        return self.nav.enc.countmin(
            self.pos + 1,
            self.nav.enc.close(self.pos) - 1
        )

    def size(self):
        """return the number of descendants of this node"""
        return (self.nav.enc.close(self.pos) - self.pos + 1) / 2

    def numleaves(self):
        """return the number of leaves descending from this node"""
        return (
            self.nav.leafrank(self.nav.enc.close(self.pos)) + 1 -
            (self.nav.leafrank(self.pos - 1) + 1 if self.pos else 0)
        )

    def child(self, k):
        """return this node's kth child"""
        if k < 0 or k >= self.degree():
            raise IndexError('index out of range')
        if k == 0:
            return self.nav.node(self.pos + 1)
        return self.nav.node(
            1 + self.nav.enc.selectmin(
                self.pos + 1,
                self.nav.enc.close(self.pos) - 1,
                k
            )
        )

    def children(self):
        """iterate the children of this node"""
        for k in xrange(self.degree()):
            yield self.child(k)

    def nextsibling(self):
        """return this node's next sibling"""
        if not self.pos:
            return None
        pos = self.nav.enc.close(self.pos) + 1
        if self.nav.enc[pos] == ')':
            return None
        return self.nav.node(pos)

    def prevsibling(self):
        """return this node's previous sibling"""
        if not self.pos:
            return None
        if self.nav.enc[self.pos - 1] != ')':
            return None
        return self.nav.node(self.nav.enc.open(self.pos - 1))

    def ancestor(self, d):
        """return the ancestor of this node d levels up"""
        if d < 0 or d >= self.depth():
            return None
        return self.nav.node(self.nav.enc.bwdsearch(self.pos, -d - 1) + 1)

    def lca(self, n):
        """return the lowest common ancestor of this node and node n"""
        assert isinstance(n, Node)
        if self.isancestor(n):
            return self
        if n.isancestor(self):
            return n
        return self.nav.node(
            1 + self.nav.enc.firstmin(
                min(self.pos, n.pos),
                max(self.pos, n.pos)
            )
        ).parent()

    def levelnext(self):
        """return the next node with the same depth as this one"""
        try:
            return self.nav.node(
                self.nav.enc.fwdsearch(
                    self.nav.enc.close(self.pos), 1
                )
            )
        except ValueError:
            return None

    def levelprev(self):
        """return the previous node with the same depth as this one"""
        try:
            return self.nav.node(
                self.nav.enc.open(
                    self.nav.enc.bwdsearch(self.pos, 0) + 1
                )
            )
        except ValueError:
            return None

    def deepestnode(self):
        """return the (first) deepest descendant of this node"""
        if self.isleaf():
            return None
        return self.nav.node(
            self.nav.enc.firstmax(
                self.pos,
                self.nav.enc.close(self.pos)
            )
        )

    def leftmostleaf(self):
        """return the leftmost leaf descending from this node"""
        if self.isleaf():
            return None
        return self.nav.node(
            self.nav.leafselect(
                1 + self.nav.leafrank(
                    self.pos - (1 if self.pos else 0)
                )
            )
        )

    def rightmostleaf(self):
        """return the rightmost leaf descending from this node"""
        if self.isleaf():
            return None
        return self.nav.node(
            self.nav.leafselect(
                self.nav.leafrank(
                    self.nav.enc.close(self.pos)
                )
            )
        )

    def rank(self):
        """return the preorder rank of this node"""
        return self.nav.rank(self.pos)

    def postrank(self):
        """return the postorder rank of this node"""
        return self.nav.postrank(self.pos)

    def leafrank(self):
        """return the number of leaves at or to the left of this node"""
        return self.nav.leafrank(self.pos)

    def childrank(self):
        """return the number of siblings at or to the left of this node"""
        return self.nav.childrank(self.pos)

class Navigator(collections.Sequence):
    """models an ordinal tree given a balanced parentheses encoding.

    this class captures the structure of static trees. a tree's
    structure comprises the child, parent, and sibling relationships
    of its nodes but does *not* represent satellite data associated
    with said nodes; for this functionality, see the Tree or
    SearchTree classes.

    the tree is indexed by preorder node rank. in other words, node 0
    corresponds to the first node in the preorder enumeration of the
    tree.

    """
    # pylint: disable=W0231

    def __init__(self, enc, nodecls=Node):
        assert isinstance(enc, encoding.BalancedParentheses)
        self.enc = enc
        self._node = nodecls

    def __len__(self):
        return len(self.enc) / 2

    def __nonzero__(self):
        return len(self) > 0

    def __getitem__(self, n):
        """return the position of the nth node"""
        if isinstance(n, slice):
            return list(self.iterate(idx=n))
        if n < 0:
            n += len(self)
        if n < 0 or n >= len(self):
            raise IndexError('index out of range')
        return self.node(self.select(n))

    def __reversed__(self):
        """iterate the tree in reverse preorder"""
        return self.iterate(idx=slice(None, None, -1))

    def root(self):
        """return the root node"""
        return self.node(0)

    def iterate(self, idx=None, preorder=True):
        """iterate the tree in pre- or post-order.

        idx can be a starting offset, or a slice giving start, stop,
        and stride.

        """
        zlice = (
            idx
            if isinstance(idx, slice) else
            slice(idx, None)
            if isinstance(idx, numbers.Integral) else
            slice(None)
        )
        nodes = xrange(*zlice.indices(len(self)))
        select = self.select if preorder else self.postselect

        for n in nodes:
            yield self.node(select(n))

    def node(self, pos):
        """return the node at position pos"""
        if self.enc[pos] != '(':
            raise ValueError('no node at position {}'.format(pos))
        return self._node(self, pos)

    def select(self, k):
        """return the position of node k"""
        return self.enc.select('(', k + 1)

    def postselect(self, k):
        """return the position of postorder node n"""
        return self.enc.open(self.enc.select(')', k + 1))

    def leafselect(self, k):
        """return the position of the kth leaf node"""
        return self.enc.select('()', k + 1)

    def rank(self, pos):
        """return the preorder rank at pos"""
        return self.enc.rank('(', pos) - 1

    def postrank(self, pos):
        """return the postorder rank at pos"""
        return self.enc.rank(')', self.enc.close(pos)) - 1

    def leafrank(self, pos):
        """return the number of leaves at or to the left of pos"""
        return self.enc.rank('()', pos) - 1

    def childrank(self, pos):
        """return the number of siblings at or to the left of pos"""
        if pos == 0 or self.enc[pos - 1] == '(':
            return 1
        return self.enc.countmin(self.node(pos).parent().pos + 1, pos) + 1

    def levelleftmost(self, d):
        """return the leftmost node with depth d"""
        if d < 1 or d > self.root().height() + 1:
            return None
        return self.node(self.enc.fwdsearch(-1, d))

    def levelrightmost(self, d):
        """return the rightmost node with depth d"""
        if d < 1 or d > self.root().height() + 1:
            return None
        return self.node(
            self.enc.open(
                self.enc.bwdsearch(
                    len(self.enc), d - 1
                )
            )
        )
