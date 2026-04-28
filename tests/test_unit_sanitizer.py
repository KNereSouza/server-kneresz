from app.services.sanitizer import sanitize_markdown


def test_sanitize_allows_safe_html():
    html = "<p><strong>bold</strong> and <em>italic</em></p>"
    assert sanitize_markdown(html) == html


def test_sanitize_strips_script_tags():
    html = '<script>alert("xss")</script><p>safe</p>'
    result = sanitize_markdown(html)
    assert "<script>" not in result
    assert "<p>safe</p>" in result


def test_sanitize_strips_onclick():
    html = '<p onclick="evil()">text</p>'
    result = sanitize_markdown(html)
    assert "onclick" not in result
    assert "<p>text</p>" in result


def test_sanitize_allows_links_with_href():
    html = '<a href="https://example.com" title="link">click</a>'
    result = sanitize_markdown(html)
    assert 'href="https://example.com"' in result
    assert 'target="_blank"' in result
    assert 'rel="noopener noreferrer"' in result


def test_sanitize_linkifies_plain_urls_with_safe_attrs():
    result = sanitize_markdown("see https://example.com for more")
    assert 'href="https://example.com"' in result
    assert 'target="_blank"' in result
    assert 'rel="noopener noreferrer"' in result


def test_sanitize_does_not_linkify_inside_code():
    result = sanitize_markdown("<code>https://example.com</code>")
    assert "<a " not in result


def test_sanitize_allows_img_with_src_alt():
    html = '<img src="https://example.com/img.png" alt="photo" title="t">'
    result = sanitize_markdown(html)
    assert 'src="https://example.com/img.png"' in result
    assert 'alt="photo"' in result


def test_sanitize_strips_style_tag():
    html = "<style>body{color:red}</style><p>text</p>"
    result = sanitize_markdown(html)
    assert "<style>" not in result
    assert "<p>text</p>" in result
