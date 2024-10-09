import pytest
import os
from pathlib import Path
import pandas as pd
import sys
sys.path.append(str(Path(__file__).parent.parent))

from DownloadPolicy import get_versions, download_version, extract_cab, extract_zip, get_latest_version


@pytest.fixture(scope="module")
def versions_df():
    return get_versions()


def test_get_versions(versions_df):
    assert isinstance(versions_df, pd.DataFrame)
    assert not versions_df.empty
    assert versions_df['PolicyURL'].map(lambda x: type(x) is str and x.startswith('http')).any()


def test_get_latest_version(versions_df):
    latest_version = get_latest_version(versions_df)

    assert isinstance(latest_version, dict)
    assert 'stable' in latest_version
