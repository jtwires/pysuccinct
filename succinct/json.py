"""succint json documents.

this module uses `semi-indexing` to efficiently deserialize elements
of json documents. it does this by combining a succint tree that
enables efficient navigation of the document with the `jq` query
language for specifying nodes within the document to deserialize.

for more details, see `"semi-indexing semi-structured data in tiny
space" <http://www.di.unipi.it/~ottavian/files/semi_index_cikm.pdf>`_.

"""

from __future__ import absolute_import

import sys
import numbers
import itertools
import collections
import json as pyjson

import lark

from succinct import (
    tree,
    encoding,
)

class Index(collections.Sequence):
    """a read-only mapping from json nodes to their original positions.

    succinct json documents encode the structure of json text as
    succinct trees. this index provides a mapping from the tree
    nodes back to their corresponding locations in the original text.

    """

    def __init__(self, src, enc):  # pylint: disable=W0231
        """instantiate a json semi-index.

        :param str src: the original json text
        :param encoding.EliasFano enc: a sequence giving the position
        of json nodes in the original text

        """
        assert isinstance(enc, encoding.EliasFano)
        self.src = src
        self.enc = enc

    def __len__(self):
        return len(self.enc) * 2

    def __str__(self):
        return str(self.enc)

    def __getitem__(self, idx):
        """return the json text corresponding to the given tree node.

        :param idx: the succint tree node index
        :type idx: ``int`` or ``slice``
        :returns: the json text

        """
        if not isinstance(idx, (slice, numbers.Integral)):
            raise ValueError('Index indices must be integers')
        if isinstance(idx, slice):
            if idx.step not in (None, 1):
                raise IndexError('Index does not support variable stepping')
            s, e = None, None
            if idx.start is not None:
                s = idx.start
                if s < 0:
                    s += len(self)
                s = self.lookup(s)
            if idx.stop is not None:
                e = idx.stop
                if e >= len(self):
                    e = None
                else:
                    e = self.lookup(e)
            idx = slice(s, e)
        else:
            idx = self.lookup(idx)
        return self.src[idx]

    def lookup(self, pos):
        """return the position in the json text corresponding to the tree node.

        :param int pos: the succinct tree node index
        :returns: the corresponding position in the json text

        """
        return self.enc[pos / 2] + (pos % 2)

class Document(object):
    """succinct representation of a json document.

    the json document is loaded lazily, and its members are only
    deserialized on access. this can save time when you only need to
    access a few nodes in very large documents.

    """

    def __init__(self, src):
        self._src = src
        self._nav = None
        self._idx = None

    @property
    def nav(self):
        """the succinct tree encoding the document structure"""
        if self._nav is None:
            self._loads()
        return self._nav

    @property
    def idx(self):
        """the index mapping tree nodes to their locations in the source"""
        if self._idx is None:
            self._loads()
        return self._idx

    def root(self):
        """return the root node of the document"""
        return self.render(self.nav.root())

    def render(self, node):
        """return a json node corresponding to the given tree node.

        :param tree.Node node: the tree node to render
        :return: the corresponding json node
        :rtype: Node

        """
        assert isinstance(node, tree.Node)
        idx = self.idx.lookup(node.pos)
        while idx < len(self._src) and self._src[idx].isspace():
            idx += 1
        c = self._src[idx]
        return (
            List(self, node)
            if c == '[' else
            Object(self, node)
            if c == '{' else
            Primitive(self, node)
        )

    def _loads(self):
        """construct the succinct tree and index"""
        from test.bitvector import BitVector
        from test.encoding import BalancedParentheses

        seq = iter(self._src)
        bv, pos = BitVector(''), BitVector('')
        while True:
            c = next(seq, None)
            if c is None:
                break
            if c in '[{':
                pos.append('1')
                bv.extend('11')
            elif c in '}]':
                pos.append('1')
                bv.extend('00')
            elif c in ':,':
                pos.append('1')
                bv.extend('01')
            elif c == '"':
                escaped = True
                while escaped or c != '"':
                    pos.append('0')
                    c = next(seq, None)
                    if c is None:
                        raise ValueError('malformed json')
                    escaped = c == '\\'
                pos.append('0')
            else:
                pos.append('0')

        if bv and (len(bv) < 2 or bv[-2:] != '00'):
            raise ValueError('malformed json')

        self._nav = tree.Navigator(BalancedParentheses(bv))
        self._idx = Index(self._src, encoding.EliasFano(pos))

class Null(object):
    """null json node"""

    def __str__(self):
        return 'null'

    __repr__ = __str__

class Node(collections.Sized):
    """node in a json document"""

    def __init__(self, doc, node=None):  # pylint: disable=W0231
        node = node or doc.nav.root()
        assert isinstance(doc, Document)
        assert isinstance(node, tree.Node)
        self.doc = doc
        self.node = node

    def __len__(self):
        return self.node.degree()

    def __str__(self):
        return self.doc.idx[
            self.node.pos:self.doc.nav.enc.close(self.node.pos)
        ].strip()

    __repr__ = __str__

class Primitive(Node):
    """json primitive node (i.e., string, number, or boolean)"""

    pass

class Container(Node):
    """json container node"""

    def __init__(self, doc, node):
        # odd indices are commas -- skip them
        node.pos += node.pos % 2
        super(Container, self).__init__(doc, node)

class List(collections.Sequence, Container):
    """json list node"""

    def __getitem__(self, item):
        if isinstance(item, slice):
            return [self[i] for i in range(*item.indices(len(self)))]
        if not isinstance(item, numbers.Integral):
            raise TypeError(
                'list indices must be integers, not {}'.format(
                    type(item)
                )
            )
        if item < 0:
            item += len(self)
        return self.doc.render(self.node.child(item))

class Object(collections.Mapping, Container):
    """json object node"""

    def _items(self):
        itr = iter(self.node.children())
        while True:
            key = next(itr, None)
            if not key:
                break
            yield key, next(itr)

    def _key(self, node):
        return self.doc.idx[
            node.pos:self.doc.nav.enc.close(node.pos)
        ].strip()[1:-1]

    def _val(self, node):
        return self.doc.render(node)

    def __iter__(self):
        for key, _ in self._items():
            yield self._key(key)

    def __getitem__(self, item):
        if not isinstance(item, basestring):
            raise TypeError('key must be a string')
        for key, val in self._items():
            if self._key(key) == item:
                return self._val(val)
        raise KeyError(item)

def loads(src):
    """deserialize a string to a succint json document.

    :param str src: the json text
    :returns: the json document root
    :rtype: Node

    """
    return Document(src).root()

class Query(object):
    """query engine for succinct json documents.

    supports all basic `jq filters
    <https://stedolan.github.io/jq/manual/#Basicfilters>`_:
      * **Identity**: `.`
      * **Object Identifier Index**: `.foo`, `.foo.bar`
      * **Optional Object Identifier Index**: `.foo?`
      * **Generic Object Index**: `.[<string>]`
      * **Array Index**: `.[2]`
      * **Array/String Slice**: `.[10:15]`
      * **Array/Object Value Iterator**: `.[]`
      * **Optional Array/Object Value Iterator**: `.[]?`
      * **Comma**: `,`
      * **Pipe**: `|`

    """

    PARSER = lark.Lark(
        r"""
        query: pipeline
        pipeline: expression ("|" expression)*
        expression: identity
                  | primitive
                  | properties
                  | indexer
                  | iterator
                  | concatenator
        identity: "."
        primitive: null | number | boolean | string
        properties: ("." property)+
        property: (cname | string) [optional]
        indexer: ".[" (string|number|cname|slice|expression) "]" [optional]
        iterator: ".[" "]" [optional]
        concatenator: expression ("," expression)+
        slice: [start] ":" [end]
        start: number
        end: number
        optional: "?"
        null: "null"
        ?number: integer | float
        boolean: "true" | "false"
        cname: CNAME
        float: SIGNED_FLOAT
        integer: SIGNED_INT
        string: ESCAPED_STRING

        COMMENT: "#"/[^\n]/*

        %import common.ESCAPED_STRING
        %import common.SIGNED_FLOAT
        %import common.SIGNED_INT
        %import common.CNAME
        %import common.WS

        %ignore COMMENT
        %ignore WS
        """,
        start='query',
    )

    def __init__(self, jq):
        """compile a new jq query.

        :param str jq: the query to compile

        """
        self.jq = jq
        self.tree = self.PARSER.parse(self.jq)

    def __str__(self):
        return self.jq

    def execute(self, root):
        """execute the query over a succint json tree.

        :param Node root: the succint json tree root.
        :returns: a sequence of query results.

        """
        assert isinstance(root, Node)

        null = Null()

        def optional(expression):
            """return True iff expression is optional"""
            return any(e.data == 'optional' for e in expression.children)

        def concatenate(expression, stream):
            """evaluate query expressions and concatenate results"""
            # fork the stream for each subexpression
            streams = itertools.tee(stream, len(expression.children))
            return itertools.chain.from_iterable(
                evaluate(expression, stream)
                for expression, stream in zip(expression.children, streams)
            )

        def iterate(expression, stream):
            """iterate over json stream"""
            for node in stream:
                itr = (
                    iter(node)
                    if isinstance(node, List) else
                    iter(node.values())
                    if isinstance(node, Object) else
                    iter([])
                    if optional(expression) else
                    None
                )
                if not itr:
                    raise TypeError(
                        'cannot iterate over {}'.format(
                            node.__class__.__name__
                        )
                    )
                for child in itr:
                    yield child

        def indexer(expression, stream):
            """extract elements from json containers"""
            def throw(node, item):
                raise TypeError(
                    'cannot index {} with {}'.format(
                        node.__class__.__name__,
                        item.__class__.__name__,
                    )
                )

            def mkint(expression):
                if expression.data == 'integer':
                    return int(expression.children[0])
                elif expression.data == 'float':
                    idx = float(expression.children[0])
                    if not idx.is_integer():
                        idx = int(idx) + 1
                    return idx
                else:
                    assert False, 'bad number expression {}'.format(
                        expression
                    )

            def mkslice(expression):
                s, e = None, None
                for idx in expression.children:
                    if idx.data == 'start':
                        s = mkint(idx.children[0])
                    elif idx.data == 'end':
                        e = mkint(idx.children[0])
                yield slice(s, e)

            def mkindex(expression):
                if expression.data == 'expression':
                    return evaluate(expression, stream)
                elif expression.data == 'slice':
                    return mkslice(expression)
                elif expression.data == 'cname':
                    return expression.children
                elif expression.data == 'string':
                    return [expression.children[0][1:-1]]
                elif expression.data in ('integer', 'float'):
                    return [mkint(expression)]
                else:
                    assert False, 'bad index expression {}'.format(expression)

            for item in mkindex(expression.children[0]):
                for node in stream:
                    if isinstance(node, Object):
                        if isinstance(item, Primitive):
                            item = str(item)[1:-1]
                        if isinstance(item, basestring):
                            yield node.get(item, null)
                            continue

                    if isinstance(node, List):
                        if isinstance(item, Primitive):
                            item = int(str(item))
                        if isinstance(item, (int, slice)):
                            try:
                                yield node[item]
                            except IndexError:
                                yield null
                            continue

                    if not optional(expression):
                        throw(node, item)

        def properties(expression, stream):
            """extract values from json objects"""
            def index(expression, stream):
                item = expression.children[0].children[0]
                for node in stream:
                    if isinstance(node, Object):
                        yield node.get(item, null)
                    elif not optional(expression):
                        itype = expression.children[0].data
                        if itype == 'cname':
                            itype = 'string'
                        raise TypeError(
                            'cannot index {} with {}'.format(
                                node.__class__.__name__, itype
                            )
                        )

            for expression in expression.children:
                stream = index(expression, stream)

            for node in stream:
                yield node

        def primitive(expression):
            """return a primitive type"""
            expression = expression.children[0]
            if expression.data == 'null':
                return null
            elif expression.data == 'boolean':
                return expression.children[0] == 'true'
            elif expression.data == 'string':
                return expression.children[0][1:-1]
            elif expression.data == 'integer':
                return int(expression.children[0])
            elif expression.data == 'float':
                return float(expression.children[0])
            assert False, 'bad primitive {}'.format(expression)

        def evaluate(expression, stream):
            """evaluate query expression over json stream"""
            assert expression.data == 'expression', expression
            assert len(expression.children) == 1

            expression = expression.children[0]

            if expression.data == 'identity':
                for node in stream:
                    yield node

            elif expression.data == 'primitive':
                yield primitive(expression)

            elif expression.data == 'properties':
                for node in properties(expression, stream):
                    yield node

            elif expression.data == 'indexer':
                for node in indexer(expression, stream):
                    yield node

            elif expression.data == 'iterator':
                for node in iterate(expression, stream):
                    yield node

            elif expression.data == 'concatenator':
                for node in concatenate(expression, stream):
                    yield node

            else:
                assert False, 'bad expression {}'.format(expression)

        stream, pipeline = [root], self.tree.children[0]
        for expression in pipeline.children:
            stream = evaluate(expression, stream)

        for result in stream:
            yield result

def query(src, jq):
    """render python objects from json text.

    >>> query('{"foo": [0, 1, 2], "bar": [3, 4, 5]}', '.bar | .[:-1]')
    [3, 4]
    >>> query('[{"foo": True}, {"bar": False}]', '.[] | .[]')
    [True, False]

    :param str src: the json text
    :param str jq: a jq query describing the objects to render
    :returns: a sequence of python objects

    """
    for res in Query(jq).execute(loads(src)):
        if isinstance(res, (Null, Node)):
            yield pyjson.loads(str(res))
        else:
            yield [pyjson.loads(str(item)) for item in res]

def main():
    import argparse
    import textwrap

    p = argparse.ArgumentParser(
        description='json query engine',
        epilog=textwrap.dedent(
            """

            this utility supports the basic filters of the jq query
            langage. filters accept json as input and produce query
            results as output. the supported filters are:

            `.`: produce the input as the output.

            `.foo`: produce the value of a json object at the key
            "foo", or null if the key is not present. if the key
            contains special characters, it must be enclosed in double
            quotes: `."foo$"`.

            `.foo|.bar`: equivalent to `.foo | .bar`.

            `.foo?`: like `.foo`, but does not produce an error, even
            when `.` is not an object.

            `.["foo"]`: produce the value of a json object at the key
            "foo", or null if the key is not present. `.foo` is a
            shorthand version of `.["foo"]`, but only for
            identifier-like strings.

            `.[2]`: produce the list element at the given index,
            starting from zero (so `.[2]` produces the third element).

            `.[10:15]`: return the list slice starting at index 10
            (inclusive) and ending at index 15 (exclusive).

            `.[]`: return all the elements of a list, or all the
            values of an object.

            `.[]?`: like `.[]`, but does not produce an error, even
            when `.` is not a list or object.

            `,`: concatenate the output of two filters, in order. for
            instance, `.foo, .bar` produces the "foo" field followed
            by the "bar" field.

            """
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        'query',
        help='jq query',
    )
    p.add_argument(
        'files',
        nargs='*',
        type=argparse.FileType('r'),
        help='files to query (defaults to stdin)',
    )

    def dumps(node):
        return pyjson.dumps(pyjson.loads(str(node)), indent=2)

    args = p.parse_args()

    jq = Query(args.query)
    for fp in args.files or [sys.stdin]:
        for res in jq.execute(loads(fp.read())):
            if isinstance(res, (Null, Node)):
                print dumps(res)
            else:
                for item in res:
                    print dumps(item)

if __name__ == '__main__':
    sys.exit(main())
