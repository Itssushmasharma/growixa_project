import pytest

from growixa_api.personalization.renderer import (
    PROHIBITED_FIELDS,
    MissingTokenValueError,
    UnknownTokenError,
    extract_template_tokens,
    render_personalization,
    validate_template_tokens,
)


def test_extract_template_tokens() -> None:
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


def test_render_standard_recipient_and_account_tokens() -> None:
    subject = "Hello {{first_name}} from {{company_name}}"
    body_html = (
        "<p>Hi {{first_name}} {{last_name}},</p>"
        "<p>Visit us at {{website_url}} or contact {{sender_name}}.</p>"
    )
    body_text = "Hi {{first_name}}, visit {{website_url}}"

    recipient_data = {
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice@example.com",
        "phone": "+1234567890",
    }
    account_data = {
        "company_name": "Growixa Inc",
        "website_url": "https://growixa.com",
        "sender_name": "Alex Sender",
    }

    rendered_subject = render_personalization(
        subject,
        recipient_data=recipient_data,
        account_data=account_data,
        is_html=False,
    )
    assert rendered_subject == "Hello Alice from Growixa Inc"

    rendered_html = render_personalization(
        body_html,
        recipient_data=recipient_data,
        account_data=account_data,
        is_html=True,
    )
    assert (
        rendered_html
        == "<p>Hi Alice Smith,</p><p>Visit us at https://growixa.com or contact Alex Sender.</p>"
    )

    rendered_text = render_personalization(
        body_text,
        recipient_data=recipient_data,
        account_data=account_data,
        is_html=False,
    )
    assert rendered_text == "Hi Alice, visit https://growixa.com"


def test_render_custom_fields_allowed_and_blocked() -> None:
    template = 'Welcome to {{school_name | default:"our academy"}} in {{city}}!'
    allowed_custom = {"school_name", "city"}

    recipient_data = {
        "school_name": "Springfield High",
        "city": "Springfield",
    }

    rendered = render_personalization(
        template,
        recipient_data=recipient_data,
        allowed_custom_field_keys=allowed_custom,
        is_html=False,
    )
    assert rendered == "Welcome to Springfield High in Springfield!"

    # Unusable/unauthorized custom field raises UnknownTokenError
    with pytest.raises(UnknownTokenError) as exc_info:
        render_personalization(
            template,
            recipient_data=recipient_data,
            allowed_custom_field_keys={"school_name"},  # city not allowed
            is_html=False,
        )
    assert "city" in str(exc_info.value)


def test_default_fallback_filter() -> None:
    template = 'Dear {{first_name | default:"Valued Partner"}}, thanks from {{company_name}}.'
    recipient_data = {"first_name": None}
    account_data = {"company_name": "IITDEVELOPER"}

    rendered = render_personalization(
        template,
        recipient_data=recipient_data,
        account_data=account_data,
        is_html=False,
    )
    assert rendered == "Dear Valued Partner, thanks from IITDEVELOPER."


def test_missing_token_value_without_default_raises_error() -> None:
    template = "Dear {{first_name}}, thanks from {{company_name}}."
    recipient_data = {"first_name": None, "email": "test@example.com"}
    account_data = {"company_name": "Growixa"}

    with pytest.raises(MissingTokenValueError) as exc_info:
        render_personalization(
            template,
            recipient_data=recipient_data,
            account_data=account_data,
            is_html=False,
        )
    assert "first_name" in str(exc_info.value)
    assert "test@example.com" in str(exc_info.value)


def test_html_escaping_for_untrusted_input() -> None:
    template = "<p>Hello {{first_name}}, from {{school_name}}</p>"
    recipient_data = {
        "first_name": "Alice <script>alert(1)</script>",
        "school_name": "Smith & Jones Academy",
    }
    allowed_custom = {"school_name"}

    rendered = render_personalization(
        template,
        recipient_data=recipient_data,
        allowed_custom_field_keys=allowed_custom,
        is_html=True,
    )
    expected = (
        "<p>Hello Alice &lt;script&gt;alert(1)&lt;/script&gt;, from Smith &amp; Jones Academy</p>"
    )
    assert rendered == expected


def test_prohibited_internal_fields_strictly_refused() -> None:
    for forbidden in PROHIBITED_FIELDS:
        template = f"Internal data: {{{{ {forbidden} }}}}"
        with pytest.raises(UnknownTokenError) as exc_info:
            validate_template_tokens(template)
        assert forbidden in str(exc_info.value)

        with pytest.raises(UnknownTokenError):
            render_personalization(
                template,
                recipient_data={"first_name": "Alice", forbidden: "leaked_val"},
                is_html=False,
            )


def test_broadcast_channel_blocks_recipient_tokens() -> None:
    template = "Check out our latest update at {{website_url}}! Personalized for {{first_name}}"
    with pytest.raises(UnknownTokenError) as exc_info:
        validate_template_tokens(template, is_broadcast=True)
    assert "first_name" in str(exc_info.value)
    assert "broadcast" in str(exc_info.value)


def test_unknown_typo_token_blocks_validation() -> None:
    template = "Hello {{shcool_name}}"
    with pytest.raises(UnknownTokenError) as exc_info:
        validate_template_tokens(template, allowed_custom_field_keys={"school_name"})
    assert "shcool_name" in str(exc_info.value)
