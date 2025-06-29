"""Test configuration and fixtures for USHCN Heat Island Analysis tests."""

import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def data_dir(project_root):
    """Return the data directory path."""
    return project_root / "data"


@pytest.fixture(scope="session")
def output_dir(tmp_path_factory):
    """Create a temporary output directory for tests."""
    return tmp_path_factory.mktemp("test_output")


@pytest.fixture
def sample_baseline_period():
    """Return a sample baseline period for testing."""
    return (1951, 1980)


@pytest.fixture
def sample_current_period():
    """Return a sample current period for testing."""
    return (1981, 2010)