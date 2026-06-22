from jobtrail.utils.text import company_from_sender, role_from_text


def test_improved_role_patterns() -> None:
    assert role_from_text("Your application to Daon for Data Scientist role", "") == "Data Scientist"
    assert role_from_text("invitation for ML Engineer interview", "") == "ML Engineer"
    assert role_from_text("next steps for Computer Vision PhD", "") == "Computer Vision PhD"


def test_company_cleanup_and_ats_fallback() -> None:
    assert company_from_sender("Acme Careers <jobs@acme.example>") == "Acme"
    assert company_from_sender("Greenhouse <no-reply@greenhouse.io>", "Your application to Daon for ML Engineer role", "") == "Daon"
