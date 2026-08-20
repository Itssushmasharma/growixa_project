"""Unit tests for the shared branded transactional layout (GRX-USER-003). Pure
rendering -- no DB, no SMTP -- so these are plain unit tests, unlike the delivery tests
in test_notifications_email.py which need real Postgres for the provider-resolution
order."""

from growixa_api.notifications.layout import EmailContent, render


def _content(**overrides: object) -> EmailContent:
    base: dict[str, object] = {
        "subject": "Subject line",
        "preheader": "Preview text",
        "heading": "Heading",
        "paragraphs": ("First paragraph.", "Second paragraph."),
    }
    base.update(overrides)
    return EmailContent(**base)  # type: ignore[arg-type]


def test_renders_brand_chrome_and_all_paragraphs_in_both_parts() -> None:
    rendered = render(_content())

    assert rendered.subject == "Subject line"
    assert "Growixa" in rendered.html
    assert "BY IITDEVELOPER" in rendered.html
    assert "Preview text" in rendered.html
    for part in (rendered.html, rendered.text):
        assert "Heading" in part
        assert "First paragraph." in part
        assert "Second paragraph." in part


def test_action_renders_a_button_and_a_copyable_fallback_link() -> None:
    """The URL must appear in the plain-text part too: a text-only client shows no
    button at all, so without it the message would have no way to act on."""
    url = "https://app.example.com/verify-email?token=abc123"
    rendered = render(_content(action_label="Verify my email", action_url=url))

    # Three occurrences: the button's href, the fallback link's href, and the fallback
    # link's visible text (the URL is shown, not hidden behind a label).
    assert rendered.html.count(url) == 3
    assert "Verify my email" in rendered.html
    assert "Or paste this link into your browser:" in rendered.html
    assert url in rendered.text


def test_omits_action_markup_entirely_when_no_action_is_given() -> None:
    rendered = render(_content())

    assert "Or paste this link" not in rendered.html
    assert "<a href" not in rendered.html


def test_escapes_user_controlled_text_instead_of_injecting_markup() -> None:
    """`full_name` reaches the heading straight from registration input. Before the
    shared layout each sender interpolated it into an f-string of raw HTML, so a display
    name containing markup was injected verbatim into the mail body."""
    rendered = render(
        _content(
            heading="Welcome, <img src=x onerror=alert(1)>",
            paragraphs=("Signed up as <b>admin</b> & co.",),
        )
    )

    assert "<img src=x" not in rendered.html
    assert "&lt;img src=x" in rendered.html
    assert "<b>admin</b>" not in rendered.html
    assert "&amp; co." in rendered.html
    # The text part is never parsed as markup, so it keeps the original characters.
    assert "<b>admin</b>" in rendered.text


def test_escapes_a_quote_bearing_url_so_it_cannot_break_out_of_the_href() -> None:
    rendered = render(
        _content(action_label="Go", action_url='https://example.com/?t=a"><script>x</script>')
    )

    assert "<script>" not in rendered.html
    assert "&quot;" in rendered.html


def test_footer_note_appears_in_both_parts() -> None:
    rendered = render(_content(footer_note="This link expires in 30 minutes."))

    assert "This link expires in 30 minutes." in rendered.html
    assert "This link expires in 30 minutes." in rendered.text


def test_text_part_carries_no_html_tags() -> None:
    rendered = render(
        _content(action_label="Verify", action_url="https://app.example.com/verify?token=t")
    )

    assert "<table" not in rendered.text
    assert "style=" not in rendered.text
