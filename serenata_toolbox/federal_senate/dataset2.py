#!/usr/bin/env python

import aiofiles
import aiohttp
import asyncio
import os
from datetime import date
import pandas as pd

from serenata_toolbox import log

URL = 'http://www.senado.gov.br/transparencia/LAI/verba/{}.csv'
AVAILABLE_YEARS = [year for year in range(2008, date.today().year + 1)]


class SenateDataset:
    def __init__(self, path='data', years=AVAILABLE_YEARS):
        if not os.path.isdir(path):
            os.mkdir(os.path.join(path))
        self.path = path
        self.years = years if isinstance(years, list) else [years]
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.main(loop))


    async def fetch(self, session, url):
        async with session.get(url) as response:
            f = 'federal-senate-{}'.format(os.path.basename(url))
            file_path = os.path.join(self.path, f)
            log.info('Downloading %s' % f)
            async with aiofiles.open(file_path, 'wb') as fd:
                while True:
                    chunk = await response.content.read(1024)
                    if not chunk:
                        break
                    await fd.write(chunk)
            log.info('Download finished for %s' % f)
            return await response.release()


    async def _translate(self):
        log.info('Translating %s' % filename)
        async with aiohttp.ClientSession(loop=loop) as session:
            tasks = [self.fetch(session, URL.format(year)) for year in self.years]
            await asyncio.gather(*tasks)
        f = 'federal-senate-{}'.format(os.path.basename(url))
        file_path = os.path.join(self.path, f)
        data = pd.read_csv(file_path,
                           sep=';',
                           encoding="ISO-8859-1",
                           skiprows=1)

    def translate(self):
        filenames = self._filename_generator('csv')
        not_found_files = []
        translated_files = []

        for filename in filenames:
            log.info('Translating %s' % filename)
            csv_path = os.path.join(self.path, filename)
            try:
                self._translate_file(csv_path)
            except FileNotFoundError as file_not_found_error:
                log.error("While translating, Seranata Toolbox didn't find file: {} \n{}".format(
                    csv_path,
                    file_not_found_error)
                )
                raise file_not_found_error
            else:
                translated_files.append(csv_path)

        return (translated_files, not_found_files)

    def clean(self):
        filenames = self._filename_generator('xz')

        merged_dataset = self._merge_files(filenames)

        cleaned_merged_dataset = self._cleanup_dataset(merged_dataset)

        reimbursement_path = os.path.join(self.path, 'federal-senate-reimbursements.xz')
        cleaned_merged_dataset.to_csv(reimbursement_path,
                                      compression='xz',
                                      index=False,
                                      encoding='utf-8')

        return reimbursement_path

    def _filename_generator(self, extension):
        return ['federal-senate-{}.{}'.format(year, extension) for year in self.years]

    @staticmethod
    def _cleanup_dataset(dataset):
        dataset['date'] = pd.to_datetime(dataset['date'], errors='coerce')
        dataset['cnpj_cpf'] = dataset['cnpj_cpf'].str.replace(r'\D', '')

        return dataset

    def _merge_files(self, filenames):
        dataset = pd.DataFrame()

        for filename in filenames:
            file_path = os.path.join(self.path, filename)
            data = pd.read_csv(file_path, encoding='utf-8')
            dataset = pd.concat([dataset, data])

        return dataset

    @staticmethod
    def _translate_file(csv_path):
        output_file_path = csv_path.replace('.csv', '.xz')

        data = pd.read_csv(csv_path,
                           sep=';',
                           encoding="ISO-8859-1",
                           skiprows=1)

        data.columns = [str.lower(column) for column in data.columns]

        data.rename(columns={
            'ano': 'year',
            'mes': 'month',
            'senador': 'congressperson_name',
            'tipo_despesa': 'expense_type',
            'cnpj_cpf': 'cnpj_cpf',
            'fornecedor': 'supplier',
            'documento': 'document_id',
            'data': 'date',
            'detalhamento': 'expense_details',
            'valor_reembolsado': 'reimbursement_value',
        }, inplace=True)

        data['expense_type'] = data['expense_type'].astype('category')

        data['expense_type'] = \
            data['expense_type'].astype('category')

        pt_categories = (
            'Aluguel de imóveis para escritório político, compreendendo despesas concernentes a eles.',
            ('Aquisição de material de consumo para uso no escritório político, inclusive aquisição ou locação'
                ' de software, despesas postais, aquisição de publicações, locação de móveis e de equipamentos. '),
            ('Contratação de consultorias, assessorias, pesquisas, trabalhos técnicos e outros serviços de '
                'apoio ao exercício do mandato parlamentar'),
            'Divulgação da atividade parlamentar',
            'Locomoção, hospedagem, alimentação, combustíveis e lubrificantes',
            'Passagens aéreas, aquáticas e terrestres nacionais',
            'Serviços de Segurança Privada'
        )
        en_categories = (
            'Rent of real estate for political office, comprising expenses concerning them',
            ('Acquisition of consumables for use in the political office, including acquisition or leasing of'
                ' software, postal expenses, acquisition of publications, rental of furniture and equipment'),
            ('Recruitment of consultancies, advisory services, research, technical work and other services'
                ' in support of the exercise of the parliamentary mandate'),
            'Publicity of parliamentary activity',
            'Locomotion, lodging, food, fuels and lubricants',
            'National air, water and land transport',
            'Private Security Services'
        )
        categories = dict(zip(pt_categories, en_categories))

        categories = [categories[cat] for cat in data['expense_type'].cat.categories]

        data['expense_type'].cat.rename_categories(categories, inplace=True)

        data.to_csv(output_file_path, compression='xz', index=False, encoding='utf-8')

        return output_file_path


    async def main(self, loop):
        async with aiohttp.ClientSession(loop=loop) as session:
            tasks = [self.fetch(session, URL.format(year)) for year in self.years]
            await asyncio.gather(*tasks)


if __name__ == '__main__':
    senate = SenateDataset()
    senate.translate()
    senate.clean()
