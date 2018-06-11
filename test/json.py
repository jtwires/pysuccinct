from __future__ import absolute_import

import unittest
import json as pyjson

from succinct import json

class JSONTests(unittest.TestCase):

    def check(self, jq, obj, res):
        self.assertEqual(
            list(json.query(pyjson.dumps(obj), jq)),
            res
        )

    def test_comment(self):
        self.check('. # ignore this', [], [[]])

    def test_identity(self):
        self.check(
            '.',
            [0, 1, 2],
            [[0, 1, 2]],
        )
        self.check(
            '.',
            {'foo': 0, 'bar': 1},
            [{'foo': 0, 'bar': 1}],
        )
        self.check(
            '.',
            [{0: False, 1: [2, 3]}],
            [[{'0': False, '1': [2, 3]}]],
        )

    def test_properties(self):
        self.check(
            '.foo',
            {},
            [None],
        )
        self.check(
            '.foo',
            {'foo': 'val'},
            ['val'],
        )
        self.check(
            '.bar',
            {'foo': 'val'},
            [None],
        )
        self.check(
            '.foo.bar',
            {'foo': {'bar': [0, 1, 2]}},
            [[0, 1, 2]],
        )
        with self.assertRaises(TypeError):
            self.check(
                '.foo',
                [0, 1, 2],
                [],
            )
        self.check(
            '.foo?',
            [0, 1, 2],
            [],
        )
        self.check(
            '.bar, .foo',
            {'foo': True, 'bar': False},
            [False, True],
        )

    def test_indexer(self):
        self.check('.', {}, [{}])
        self.check(
            '.["foo"]',
            {'foo': 'val'},
            ['val'],
        )
        self.check(
            '.["bar"]',
            {'foo': 'val'},
            [None],
        )
        self.check(
            '.["foo"] | .["bar"]',
            {'foo': {'bar': [0, 1, 2]}},
            [[0, 1, 2]],
        )
        with self.assertRaises(TypeError):
            self.check(
                '.["foo"]',
                [0, 1, 2],
                [],
            )
        self.check(
            '.["foo"]?',
            [0, 1, 2],
            [],
        )
        self.check(
            '.["bar", "foo"]',
            {'foo': True, 'bar': False},
            [False, True],
        )
        self.check(
            '.["bar"], .["foo"]',
            {'foo': True, 'bar': False},
            [False, True],
        )

        self.check('.', [], [[]])
        self.check(
            '.[0]',
            [True, False, 10],
            [True],
        )
        self.check(
            '.[-1]',
            [True, False, 10],
            [10],
        )
        self.check(
            '.[:]',
            [True, False, 10],
            [[True, False, 10]],
        )
        self.check(
            '.[1:]',
            [True, False, 10],
            [[False, 10]],
        )
        self.check(
            '.[:2]',
            [True, False, 10],
            [[True, False]],
        )
        self.check(
            '.[1:-1]',
            [True, False, 10],
            [[False]],
        )
        with self.assertRaises(TypeError):
            self.check(
                '.[0]',
                {'foo': True},
                [],
            )
        self.check(
            '.[0]?',
            {'foo': True},
            [],
        )
        self.check(
            '.[1,0]',
            [0, 1, 2],
            [1, 0],
        )
        self.check(
            '.[1], .[0]',
            [0, 1, 2],
            [1, 0],
        )

    def test_iterator(self):
        self.check(
            '.[]',
            [0, 1, 2],
            [0, 1, 2],
        )
        self.check(
            '.[]',
            [[0, 1, 2], [3, 4, 5]],
            [[0, 1, 2], [3, 4, 5]],
        )
        self.check(
            '.[]',
            {'foo': True, 'bar': False},
            [True, False],
        )
        with self.assertRaises(TypeError):
            self.check(
                '.foo | .[]',
                {'foo': True},
                [],
            )
        self.check(
            '.foo | .[]?',
            {'foo': True},
            [],
        )

    def test_pipe(self):
        self.check(
            '. | .foo',
            {'foo': True},
            [True],
        )
        self.check(
            '.foo | .',
            {'foo': True},
            [True],
        )
        self.check(
            '.[] | .foo',
            [{'foo': 1}, {'foo': 2}],
            [1, 2],
        )
        self.check(
            '.foo | .[0]',
            {'foo': [0, 1, 2]},
            [0],
        )
        self.check(
            '.foo, .bar | .[-1]',
            {'foo': [0, 1, 2], 'bar': [3, 4, 5]},
            [2, 5],
        )
        self.check(
            '.[] | .foo, .bar',
            [{'foo': True}, {'bar': False}],
            [True, None, None, False],
        )
        self.check(
            '.[.bar, .foo]',
            {'foo': 'bar', 'bar': 'foo'},
            ['bar', 'foo'],
        )
