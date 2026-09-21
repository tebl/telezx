import unittest, tempfile, string, random
from pathlib import Path
from lib import utilities, ZXRegistry, ZXRegistryEntry

class TestZXDocument(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(prefix='telezx-registry-')
        self.registry_path = Path(self.temp_dir.name) / f'telezx{ZXRegistry.FILE_EXTENSION}'
        self.registry = ZXRegistry.create_file(document_path=self.registry_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def debug_contents(self):
        with open(self.registry_path, 'r') as file:
            print(file.read())

    def test_sync_record(self):
        self.registry.sync_record(0x1000, 'This is a test', 'Test', ['test_tag', 'test_tag2'])
        record = self.registry.lookup(0x1000)
        self.assertIsNotNone(record)
        self.assertEqual(record.description, 'This is a test')
        self.assertEqual(self.registry.lookup_abbreviation(0x1000), 'Test')
        self.assertIsNotNone(self.registry.lookup_tag('test_tag'))
        self.assertTrue(self.registry.save())

    def test_sync_tag(self):
        self.registry.sync_tag(name='test_tag', export_description='This is a test', export_id=0x9999)
        tag = self.registry.lookup_tag('test_tag')
        self.assertIsNotNone(tag)
        self.assertEqual(tag.export_description, 'This is a test')
        self.assertEqual(tag.export_id, 0x9999)
        self.assertTrue(self.registry.save())

    def test_set_ignored(self):
        self.registry.sync_record(0x1000, 'This is a test', 'Test', ['test_tag', 'test_tag2'])
        self.assertIsNotNone(self.registry.lookup(0x1000))
        self.registry.set_ignored(0x1000, True)
        self.assertTrue(0x1000 in self.registry.ignored)
        self.assertIsNone(self.registry.lookup(0x1000))

        self.registry.set_ignored(0x1000, False)
        self.assertTrue(0x1000 not in self.registry.ignored)

        self.registry.sync_record(0x1000, 'This is a test', 'Test', ['test_tag', 'test_tag2'])
        record = self.registry.lookup(0x1000)
        self.assertIsNotNone(record)

        self.assertTrue(self.registry.save())

    def test_tag_records(self):
        # Sync record then ensure partial tag record exists
        self.registry.sync_record(0x1000, 'This is a test', 'Test', ['test_tag', 'test_tag2'])
        record = self.registry.lookup(0x1000)
        self.assertIsNotNone(record)
        self.assertIsNotNone(self.registry.lookup_tag('test_tag'))
        self.assertIsNotNone(self.registry.lookup_tag('test_tag2'))

        # Supplement tag information
        self.registry.sync_tag(name='test_tag', export_description='This is a test', export_id=0x9999)
        tag = self.registry.lookup_tag('test_tag')
        self.assertIsNotNone(tag)
        self.assertEqual(tag.export_description, 'This is a test')
        self.assertEqual(tag.export_id, 0x9999)

        # Ensure that the record got added to the tag
        self.assertTrue(record in tag.entries)

        self.assertTrue(self.registry.save())

    def test_tag_membership_changes(self):
        self.registry.sync_record(0x1000, 'This is a test', 'Test', ['test_tag', 'test_tag2'])
        record: ZXRegistryEntry = self.registry.lookup(0x1000)
        self.assertIsNotNone(record)
        self.assertIsNotNone(self.registry.lookup_tag('test_tag'))
        self.assertIsNotNone(self.registry.lookup_tag('test_tag2'))

        # Ensure that record is associated with the tag
        tag = self.registry.lookup_tag('test_tag')
        self.assertIsNotNone(tag)
        self.assertTrue(record in tag.entries)

        # Add new tag and ensure that the object reference is the same
        self.registry.sync_record(0x1000, 'This is a test', 'Test', ['test_tag', 'test_tag2', 'test_tag3'])
        self.assertIsNotNone(self.registry.lookup_tag('test_tag3'))
        self.assertEqual(record, self.registry.lookup(0x1000))

        # Ensure that removing a tag removes both reference and the name from
        # record tag list
        self.registry.sync_record(0x1000, 'This is a test', 'Test', ['test_tag3'])
        self.assertEqual(record.tags, ['test_tag3'])
        self.assertTrue(record not in tag.entries)
        self.assertTrue(self.registry.save())

    def test_record_persistence(self):
        self.registry.sync_record(0x1000, 'This is a test', 'Test', ['test_tag', 'test_tag2'], include_toc=False)
        record: ZXRegistryEntry = self.registry.lookup(0x1000)
        self.assertIsNotNone(record)
        self.assertIsNotNone(self.registry.lookup_tag('test_tag'))
        self.assertIsNotNone(self.registry.lookup_tag('test_tag2'))
        self.assertFalse(record.include_toc)
        self.assertTrue(self.registry.save())

        self.registry = ZXRegistry.from_file(document_path=self.registry_path, allow_create=False)
        record: ZXRegistryEntry = self.registry.lookup(0x1000)
        self.assertIsNotNone(record)
        self.assertIsNotNone(self.registry.lookup_tag('test_tag'))
        self.assertIsNotNone(self.registry.lookup_tag('test_tag2'))
        self.assertFalse(record.include_toc)

        tag = self.registry.lookup_tag('test_tag')
        self.assertIsNotNone(tag)
        self.assertTrue(record in tag.entries)
        self.assertTrue(self.registry.save())

    def test_tag_persistence(self):
        self.registry.sync_tag('test_tag', 
                               tag_group='parent_tag', 
                               export_id=0x1000,
                               export_description='description',
                               export_abbreviation='abbreviation',
                               export_link_a=0x1001,
                               export_link_a_txt='LNK_A',
                               export_link_b=0x1002,
                               export_link_b_txt='LNK_B',
                               export_link_c=0x1003,
                               export_link_c_txt='LNK_C',
                               export_include_toc=True)
        self.registry.sync_tag('exclude_toc', 
                               tag_group='parent_tag', 
                               export_id=0x1000,
                               export_description='description',
                               export_abbreviation='abbreviation',
                               export_link_a=0x1001,
                               export_link_a_txt='LNK_A',
                               export_link_b=0x1002,
                               export_link_b_txt='LNK_B',
                               export_link_c=0x1003,
                               export_link_c_txt='LNK_C',
                               export_include_toc=False)
        self.assertTrue(self.registry.save())

        # Reload from file
        self.registry = ZXRegistry.from_file(document_path=self.registry_path, allow_create=False)
        tag = self.registry.lookup_tag('test_tag')
        self.assertIsNotNone(tag)
        self.assertEqual(tag.name, 'test_tag')
        self.assertEqual(tag.tag_group, 'parent_tag')
        self.assertEqual(tag.export_description, 'description')
        self.assertEqual(tag.export_link_a, 0x1001)
        self.assertEqual(tag.export_link_a_txt, 'LNK_A')
        self.assertEqual(tag.export_link_b, 0x1002)
        self.assertEqual(tag.export_link_b_txt, 'LNK_B')
        self.assertEqual(tag.export_link_c, 0x1003)
        self.assertEqual(tag.export_link_c_txt, 'LNK_C')
        self.assertTrue(tag.export_include_toc)

        tag = self.registry.lookup_tag('exclude_toc')
        self.assertFalse(tag.export_include_toc)

    def test_random_toc(self):
        allowed_letters = string.ascii_uppercase + '#'
        characters = string.ascii_lowercase + string.digits
        for doc_id in range(0x1000, 0x1000 + 100):
            name = ''.join(random.choices(characters, k=random.randint(4, 10)))
            self.registry.sync_record(doc_id, name, name[0:4])
        for letter, entries in self.registry.generate_TOC_AZ().items():
            self.assertTrue(letter in allowed_letters)
            for entry_name, entry_link in entries:
                pass

    def test_toc_generation(self):
        self.registry.sync_record(0x0004, 'Page 4', 'p4')
        self.registry.sync_record(0x1000, 'An article', 'aaaa')
        self.registry.sync_record(0x1001, 'Believe', 'truth')
        self.registry.sync_record(0x1002, 'Bozo the clown', 'bozo')

        toc = self.registry.generate_TOC_AZ()
        self.assertEqual(len(toc['A']), 1)
        self.assertEqual(len(toc['B']), 2)
        self.assertEqual(len(toc['C']), 0)

    def test_tag_alphabetical(self):
        self.registry.sync_record(0x0004, 'Page 3', 'p3', tags=['the_sun'])
        self.registry.sync_record(0x1000, 'An article', 'aaaa', tags=['test_tag'])
        self.registry.sync_record(0x0002, 'Bzzzz', 'Bzzz', tags=['test_tag'])
        self.registry.sync_record(0x1001, 'Believe', 'truth', tags=['test_tag'])
        self.registry.sync_record(0x1002, 'Bozo the clown', 'bozo', tags=['test_tag'])

        toc = self.registry.generate_tag_AZ('test_tag')
        self.assertEqual(len(toc['B']), 3)
        self.assertEqual(toc['B'][0], ['Believe', 0x1001])
        self.assertEqual(toc['B'][1], ['Bozo the clown', 0x1002])

    def test_tag_dependency_sequence(self):
        id = iter(range(0x1000))
        self.registry.sync_tag(name='genres', export_description='Genres')
        self.registry.sync_tag(name='genre_action', export_description='Games: Action', export_id=next(id), tag_group='genres')
        self.registry.sync_tag(name='genre_adventure', export_description='Games: Adventure', export_id=next(id), tag_group='genres')
        self.registry.sync_tag(name='genre_shooter', export_description='Games: Shooter', export_id=next(id), tag_group='genre_action')
        self.registry.sync_tag(name='genre_scrolling', export_description='Games: Shoot\'em up', export_id=next(id), tag_group='genre_action')
        self.registry.sync_tag(name='genre_platformer', export_description='Games: Platformer', export_id=next(id), tag_group='genre_adventure')

        # Dependency trees should be processed in the opposite order, this is
        # because processing the ends of the trees may cause information to
        # trickle up (a subcategory gets added to a main category).
        self.assertEqual(self.registry.get_tag_dependency_tree(only_exportable=False), 
                         ['genre_platformer', 'genre_adventure', 'genre_shooter', 'genre_scrolling', 'genre_action', 'genres']
        )

        # Top entry lacks the export_id, so it should disappear from the end
        # of the list.
        self.assertEqual(self.registry.get_tag_dependency_tree(only_exportable=True), 
                         ['genre_platformer', 'genre_adventure', 'genre_shooter', 'genre_scrolling', 'genre_action']
        )

    def test_include_toc(self):
        self.registry.sync_record(0x0004, 'Page 3', 'p3', tags=['the_sun'], include_toc=True)
        toc: dict = self.registry.generate_TOC_AZ()
        self.assertEqual(len(toc['P']), 1)

        self.registry.sync_record(0x0004, 'Page 3', 'p3', tags=['the_sun'], include_toc=False)
        toc: dict = self.registry.generate_TOC_AZ()
        self.assertEqual(len(toc['P']), 0)
