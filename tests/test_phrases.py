from jobtrail.services.phrases import phrase


def test_phrase_selection_is_deterministic_with_index() -> None:
    assert phrase("aggressive", index=0) == "Rejections are reps. Keep moving."
    assert phrase("missing", index=1) == "The goal is progress, not perfection."
