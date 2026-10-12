import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.utils.llm_pick import pick_llm
from app.utils.etl_tools import ETL