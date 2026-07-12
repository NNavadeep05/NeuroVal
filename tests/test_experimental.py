import pytest
from neuroval.data import ExperimentalData



def test_create_experimental_data():
    """ExperimentalData should store the supplied feature dictionary."""

    features = {
        "Spikecount": 12,
        "RestingPotential": -90,
    }

    experimental = ExperimentalData(features)

    assert experimental.features == features

def test_empty_dictionary():
    """ExperimentalData should reject an empty feature dictionary."""

    with pytest.raises(ValueError):
        ExperimentalData({})