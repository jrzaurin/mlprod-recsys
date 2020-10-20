import json

import luigi
import dask.bag as db

from utils import Mario, RAW_REVIEWS_PATH, RAW_METADATA_PATH
from datetime import datetime


class ParquetifyReviews(Mario, luigi.Task):
    """
    overall: double
    vote: string
    verified: bool
    reviewerID: string
    item: string
    style: list<item: list<item: string>>
      child 0, item: list<item: string>
          child 0, item: string
    reviewerName: string
    reviewText: string
    summary: string
    reviewDate: date32[day]
    """

    def output_dir(self):
        return 'raw_parquet/reviews'

    def _run(self):
        def fix_nested_dict(x):
            if 'style' in x:
                x['style'] = [[key, str(val)]
                              for key, val in x['style'].items()]
            return x

        def fix_date(x):
            x['reviewDate'] = datetime.fromtimestamp(
                x['unixReviewTime']).date()
            del x['reviewTime']
            del x['unixReviewTime']
            return x

        (
            db.read_text(RAW_REVIEWS_PATH)
            .map(json.loads)
            .map(fix_nested_dict)
            .map(fix_date)
            .to_dataframe()
            .rename(columns={'asin': 'item'})
            .to_parquet(self.full_output_dir())
        )


class ParquetifyMetadata(Mario, luigi.Task):
    """
    Schema: category: list<item: string>
      child 0, item: string
    tech1: string
    description: list<item: string>
      child 0, item: string
    fit: string
    title: string
    also_buy: list<item: string>
      child 0, item: string
    image: list<item: string>
      child 0, item: string
    tech2: string
    brand: string
    feature: list<item: string>
      child 0, item: string
    rank: list<item: string>
      child 0, item: string
    also_view: list<item: string>
      child 0, item: string
    details: list<item: list<item: string>>
      child 0, item: list<item: string>
          child 0, item: string
    main_cat: string
    similar_item: string
    date: string
    price: string
    item: string
    """

    def output_dir(self):
        return 'raw_parquet/metadata'

    def _run(self):
        def fix_rank_list(x):
            """
            the 'rank' field is sometimes a string and sometimes a list of strings
            """
            if 'rank' not in x:
                x['rank'] = []
            if not isinstance(x['rank'], list):
                x['rank'] = [x['rank']]
            return x

        def fix_details(x):
            x['details'] = [[key, str(val)]
                            for key, val in x['details'].items()]
            return x

        (
            db.read_text(RAW_METADATA_PATH)
            .map(json.loads)
            .map(fix_rank_list)
            .map(fix_details)
            .to_dataframe()
            .rename(columns={'asin': 'item'})
            .to_parquet(self.full_output_dir())
        )