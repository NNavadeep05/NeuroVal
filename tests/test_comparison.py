from neuroval.validation import FeatureComparator


def test_compare_features():
    """FeatureComparator should compare two feature dictionaries."""

    comparator = FeatureComparator()

    experimental = {
        "Spikecount": 12,
    }

    simulated = {
        "Spikecount": 13,
    }

    comparison = comparator.compare(
        experimental,
        simulated,
    )

    assert comparison["Spikecount"]["experimental"] == 12
    assert comparison["Spikecount"]["simulated"] == 13
    assert comparison["Spikecount"]["absolute_error"] == 1
    assert comparison["Spikecount"]["relative_error"] == 8.33
    