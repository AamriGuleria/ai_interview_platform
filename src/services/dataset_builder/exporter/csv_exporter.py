import pandas as pd
from sqlalchemy import create_engine
from pathlib import Path
from core.config import config

def load_csv_with_pandas(csv_file, database_url, table_name):
    """Load CSV using pandas - fastest for large files"""
    try:
        df = pd.read_csv(csv_file)
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        engine = create_engine(database_url)
        df.to_sql(table_name, engine, if_exists='append', index=False)
    
    except Exception as e:
        raise


DATASETS_DIR = Path(__file__).parent.parent / "datasets"
DATABASE_URL = config.DATABASE_URL

load_csv_with_pandas(str(DATASETS_DIR / 'enriched_500_qa.csv'), DATABASE_URL, 'questions')
load_csv_with_pandas(str(DATASETS_DIR / 'enriched_hundred_qa.csv'), DATABASE_URL, 'questions')