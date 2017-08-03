import os
import glob
import pandas as pd
from datetime import date
from tempfile import mkdtemp
from shutil import rmtree
from unittest import main, TestCase
from unittest.mock import patch
from shutil import copy

from serenata_toolbox.chamber_of_deputies.dataset import Dataset

class TestChamberOfDeputiesDataset(TestCase):

    def setUp(self):
        self.path = mkdtemp(prefix='serenata-')
        print(self.path)
        self.subject = Dataset(self.path, [2017])
        self.years = [2017]


    def tearDown(self):
        rmtree(self.path, ignore_errors=True)

    @patch('serenata_toolbox.chamber_of_deputies.dataset.urlretrieve')
    def test_fetch_chambers_of_deputies_datasets(self, mocked_urlretrieve):
        copy('tests/fixtures/chamber_of_deputies/Ano-2017.zip', self.path)
        copy('tests/fixtures/chamber_of_deputies/datasets-format.html', self.path)
        files = ['Ano-2017.csv', 'datasets-format.html']

        self.subject.fetch()

        self.assertEqual(len(files), 2)
        for name in files:
            file_path = os.path.join(self.path, name)
            self.assertTrue(os.path.exists(file_path))

    # self.subject.translate()
    # for name in ["reimbursements-{}.xz".format(n) for n in self.years]:
    #     file_path = os.path.join(self.path, name)
    #     assert(os.path.exists(file_path))

    # self.subject.clean()
    # file_path = os.path.join(self.path, 'reimbursements.xz')
    # assert(os.path.exists(file_path))

    # # test for subquota translation
    # dataset = pd.read_csv(file_path, compression='xz')
    # all_subquotas = ['Maintenance of office supporting parliamentary activity',
    #                 'Locomotion, meal and lodging',
    #                 'Fuels and lubricants',
    #                 'Consultancy, research and technical work',
    #                 'Publicity of parliamentary activity',
    #                 'Purchase of office supplies',
    #                 'Software purchase or renting; Postal services; Subscriptions',
    #                 'Security service provided by specialized company',
    #                 'Flight tickets',
    #                 'Telecommunication',
    #                 'Postal services',
    #                 'Publication subscriptions',
    #                 'Congressperson meal',
    #                 'Lodging, except for congressperson from Distrito Federal',
    #                 'Automotive vehicle renting or watercraft charter',
    #                 'Aircraft renting or charter of aircraft',
    #                 'Automotive vehicle renting or charter',
    #                 'Watercraft renting or charter',
    #                 'Taxi, toll and parking',
    #                 'Terrestrial, maritime and fluvial tickets',
    #                 'Participation in course, talk or similar event',
    #                 'Flight ticket issue']

    # present_subquotas = pd.unique(dataset['subquota_description'])
    # for subquota in present_subquotas:
    #     assert(subquota in all_subquotas)
