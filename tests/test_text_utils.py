from jobtrail.utils.text import company_from_sender, normalize_key, normalize_text, role_from_text


def test_normalize_utils() -> None:
    assert normalize_text(" Hello\nWorld ") == "hello world"
    assert normalize_key("Acme, Inc.") == "acmeinc"
    assert company_from_sender("Acme Jobs <jobs@acme.example>") == "Acme"
    assert company_from_sender("jobs@big-co.example") == "Big Co"
    assert role_from_text("Application for Backend Engineer", "") == "Backend Engineer"
