import unittest, tempfile, string, random
from pathlib import Path
from lib import ZXRegistryEntry, NameTreeResolver

class DataItem:
    name: str
    parent: str|None

    def __init__(self, name: str, parent: str|None=None):
        self.name = name
        self.parent = parent

    @classmethod
    def resolver_name(cls, item) -> str:
        return item.name

    @classmethod
    def resolver_parent(cls, item) -> str|None:
        return item.parent

class TestNameTreeResolver(unittest.TestCase):
    def setUp(self):
        self.resolver = NameTreeResolver(name_func=DataItem.resolver_name, parent_func=DataItem.resolver_parent)

    def test_resolver(self):
        self.resolver.add_resolver_item(DataItem('child2', 'child1'))
        self.resolver.add_resolver_item(DataItem('child1', 'test'))
        self.resolver.add_resolver_item(DataItem('test'))
        self.resolver.add_resolver_item(DataItem('test2'))

        self.assertEqual([ key for (key, item) in self.resolver.ordered() ],
                         [ 'test', 'child1', 'child2', 'test2'])
        self.assertEqual([ key for (key, item) in self.resolver.reverse_order() ],
                         [ 'test2', 'child2', 'child1', 'test' ])

    def test_missing_parent(self):
        self.resolver.add_resolver_item(DataItem('test'))
        self.resolver.add_resolver_item(DataItem('child1', 'test2'))

        with self.assertRaises(ValueError) as context:
            self.resolver.ordered()

        # Disable raising errors, then assure that resolving now includes the
        # element that was missing its parent (preferring impartial data over
        # lost data).
        self.resolver._raise_on_errors = False
        self.resolver.resolve()
        self.assertEqual([ key for (key, item) in self.resolver.ordered()],
                         ['child1', 'test'])

    def test_mutability(self):
        self.resolver.add_resolver_item(DataItem('test'))
        self.assertEqual(len(self.resolver.ordered()), 1)

        # Assigning new item with the same should not increase count
        self.resolver.add_resolver_item(DataItem('test'))
        self.assertEqual(len(self.resolver.ordered()), 1)

        # Ensure that we now end up with two
        self.resolver.add_resolver_item(DataItem('test2'))
        self.assertEqual(len(self.resolver.ordered()), 2)