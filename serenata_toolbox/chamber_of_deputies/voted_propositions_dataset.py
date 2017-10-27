import urllib
import xml.etree.ElementTree as ET
from datetime import datetime

import pandas as pd

from serenata_toolbox.datasets.helpers import (
    save_to_csv,
    translate_column,
    xml_extract_text,
)


class VotedPropositionsDataset:

    URL = (
        'http://www.camara.leg.br/SitCamaraWS/Proposicoes.asmx/ListarProposicoesVotadasEmPlenario'
        '?ano={year}&tipo='
    )

    def fetch(self, start_year=1991, end_year=None):
        """
        Fetches the list of voted propostions in especified years.
        """
        if not end_year:
            end_year = datetime.now().year

        years = list(range(start_year, end_year + 1))
        records = self._fetch_years_propositions(years)

        df = pd.DataFrame(records, columns=(
            'proposition_id',
            'proposition_name',
            'vote_date',
        ))
        df.vote_date = pd.to_datetime(df.vote_date, errors="coerce", infer_datetime_format=True)
        return df

    def _fetch_years_propositions(self, years):
        for year in years:
            year_records = self._fetch_proposition_by_year(year)
            yield from year_records

    def _fetch_proposition_by_year(self, year):
        url = self.URL.format(year=year)
        xml = urllib.request.urlopen(url)

        tree = ET.ElementTree(file=xml)
        records = self._parse_propositions(tree.getroot())
        yield from records

    @staticmethod
    def _parse_propositions(root):
        for proposition in root:
            yield (
                xml_extract_text(proposition, 'codProposicao'),
                xml_extract_text(proposition, 'nomeProposicao'),
                xml_extract_text(proposition, 'dataVotacao'),
            )


def fetch_voted_propositions(data_dir):
    """
    :param data_dir: (str) directory in which the output file will be saved
    """
    propositions = VotedPropositionsDataset()
    df = propositions.fetch()
    save_to_csv(df, data_dir, "voted_propositions")
    return df
