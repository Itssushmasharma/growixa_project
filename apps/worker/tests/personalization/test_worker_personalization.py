import pytest

from growixa_worker.personalization import (
    UnknownTokenError,
    extract_template_tokens,
    render_personalization,
    validate_template_tokens,
)


def test_worker_extract_template_tokens() -> None:
    template = (
        "Hello {{first_name}}, welcome to {{company_name}}! "
        'School: {{school_name | default:"Demo School"}}.'
    )
    tokens = extract_template_tokens(template)
    assert tokens == [
        ("first_name", None),
        ("company_name", None),
        ("school_name", "Demo School"),
    ]


def test_worker_render_tokens_and_html_escaping() -> None:
    subject = "Hello {{first_name}} from {{company_name}}"
    body_html = '<p>Prepared for {{school_name | default:"your school"}} by {{company_name}}</p>'

    recipient_data = {
        "first_name": "Alice & Bob",
        "school_name": "St. Jude's <Primary>",
    }
    account_data = {
        "company_name": "IITDEVELOPER",
    }

    rendered_subject = render_personalization(
        subject,
        recipient_data=recipient_data,
        account_data=account_data,
        allowed_custom_field_keys={"school_name"},
        is_html=False,
    )
    assert rendered_subject == "Hello Alice & Bob from IITDEVELOPER"

    rendered_html = render_personalization(
        body_html,
        recipient_data=recipient_data,
        account_data=account_data,
        allowed_custom_field_keys={"school_name"},
        is_html=True,
    )
    assert rendered_html == "<p>Prepared for St. Jude&#x27;s &lt;Primary&gt; by IITDEVELOPER</p>"


def test_worker_prohibited_fields_rejected() -> None:
    template = "Source: {{source}}"
    with pytest.raises(UnknownTokenError):
        validate_template_tokens(template)
