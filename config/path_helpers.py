from pathlib import Path

DATA_LOCATION = Path.home() / 'unitx_data'
CONFIG_LOCATION = Path.home() / 'unitx_data' / 'config'
DATA_DB = DATA_LOCATION / 'db'
OPTIX_DB_PATH = DATA_DB / 'perception.db'
DATA_LOGS = DATA_LOCATION / 'logs'
PROD_LOG_PATH = f"{DATA_LOGS}/prod.log"

PROD_OUTPUT = DATA_LOCATION / 'data' / 'production' / 'output'
LEGACY_PROD_OUTPUT = DATA_LOCATION / 'production' / 'output'
TEST_IMAGE_LOCATION = DATA_LOCATION / 'test_images'
FAKE_IMAGE_PATH = DATA_LOCATION / 'fake_images'

PROD_ROOT_LOCATION = Path.home() / 'prod'
PROD_LOCATION = Path.home() / 'prod' / 'production_src'
OPTIX_LOCATION = Path.home() / 'optix' / 'optix_src'
CORTEX_LOCATION = Path.home() / 'cortex' / 'cortex_src'

PROD_START_LOCATION = PROD_LOCATION / 'start_everything.sh'
OPTIX_START_LOCATION = OPTIX_LOCATION / 'start_everything.sh'
CORTEX_START_LOCATION = CORTEX_LOCATION / 'start_everything.sh'

TEST_DATA_BUCKET = 's3://unitx-test-data'
DATASET_LOCATION = Path(Path.home() / 'test_datasets')
CUSTOM_CONFIG_LOCATION = DATA_LOCATION / 'config' / 'production.toml'
PRODUCTION_PY_LOCATION = DATA_LOCATION / 'config' / 'production.py'
GLOBAL_CONFIG_LOCATION = DATA_LOCATION / 'config' / 'global.toml'

