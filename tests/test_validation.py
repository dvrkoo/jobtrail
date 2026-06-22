import pytest

from jobtrail.utils.validation import positive_int, valid_email


def test_validation_helpers() -> None:
    assert valid_email("name@example.com")
    assert not valid_email("not-an-email")
    assert positive_int(1) == 1
    with pytest.raises(ValueError):
        positive_int(0)
