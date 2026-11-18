# Data

`raw/` holds 8 CSV files from the **Brazilian E-Commerce Public Dataset by Olist**
(Kaggle: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), published by Olist under the
**CC BY-NC-SA 4.0** licence (https://creativecommons.org/licenses/by-nc-sa/4.0/).

They are included unchanged so the project runs straight after cloning. Under the licence, this data
may be shared for non-commercial use with credit to Olist, and any shared copy keeps the same licence.

The geolocation file (`olist_geolocation_dataset.csv`, about 61 MB) is not used in this analysis and is
not included.

`processed/` is created by `src/01_clean.py` (or `python run_all.py`) and is not committed.
