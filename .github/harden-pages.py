from pathlib import Path
import re

CSP = (
    "default-src 'self'; "
    "base-uri 'self'; "
    "object-src 'none'; "
    "script-src 'self'; "
    "style-src 'self'; "
    "img-src 'self'; "
    "font-src 'self'; "
    "connect-src 'self'; "
    "form-action 'self'; "
    "frame-src 'none'; "
    "media-src 'self'; "
    "upgrade-insecure-requests"
)


def harden_page(path: str, css_href: str, js_href: str | None, print_button: bool = False) -> None:
    p = Path(path)
    html = p.read_text(encoding='utf-8')

    style_match = re.search(r'<style>(.*?)</style>', html, flags=re.S | re.I)
    if style_match:
        css_path = p.parent / css_href
        css_path.write_text(style_match.group(1).strip() + '\n', encoding='utf-8')
        html = html[:style_match.start()] + f'<link rel="stylesheet" href="{css_href}">' + html[style_match.end():]

    # Remove inline style attributes so style-src can stay nonce/hash-free and strict.
    html = html.replace('<p style="margin-top:22px">', '<p class="writing-link">')
    html = html.replace('<span style="color:var(--accent)">', '<span class="quote-highlight">')

    if path == 'index.html':
        css_path = p.parent / css_href
        css = css_path.read_text(encoding='utf-8')
        css += '\n.writing-link{margin-top:22px}\n.quote-highlight{color:var(--accent)}\n'
        css_path.write_text(css, encoding='utf-8')

    if print_button:
        html = html.replace(
            '<a class="btn primary" href="#" onclick="window.print();return false">Print / Save PDF</a>',
            '<a class="btn primary" href="#" id="print-resume">Print / Save PDF</a>'
        )

    if js_href:
        # Extract only executable inline scripts; JSON-LD scripts are left untouched.
        script_match = re.search(r'<script>\s*(.*?)\s*</script>', html, flags=re.S | re.I)
        if script_match:
            js_path = p.parent / js_href
            js_path.write_text(script_match.group(1).strip() + '\n', encoding='utf-8')
            html = html[:script_match.start()] + f'<script src="{js_href}" defer></script>' + html[script_match.end():]

    if print_button:
        js_path = p.parent / js_href
        js_path.write_text(
            "document.getElementById('print-resume')?.addEventListener('click', (event) => { event.preventDefault(); window.print(); });\n",
            encoding='utf-8'
        )

    if 'name="referrer"' not in html:
        html = html.replace('<meta name="robots"', '<meta name="referrer" content="strict-origin-when-cross-origin">\n<meta name="robots"', 1)

    if 'http-equiv="Content-Security-Policy"' not in html:
        csp = f'<meta http-equiv="Content-Security-Policy" content="{CSP}">'
        html = html.replace('<meta name="referrer" content="strict-origin-when-cross-origin">', '<meta name="referrer" content="strict-origin-when-cross-origin">\n' + csp, 1)

    p.write_text(html, encoding='utf-8')


harden_page('index.html', 'styles.css', 'site.js')
harden_page('resume/index.html', 'resume.css', 'resume.js', print_button=True)
