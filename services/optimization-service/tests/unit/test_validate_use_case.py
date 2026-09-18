from app.application.validate_use_case import validate


def test_identical_text_gets_full_confidence() -> None:
    result = validate("same text", "same text")
    assert result.confidence == 1.0
    assert result.semantic_similarity == 1.0


def test_disjoint_text_gets_low_confidence() -> None:
    result = validate("apples bananas cherries", "xylophone zebra quokka")
    assert result.confidence == 0.0


def test_partial_overlap_scores_between_zero_and_one() -> None:
    result = validate("the quick brown fox", "the quick fox")
    assert 0.0 < result.confidence < 1.0
