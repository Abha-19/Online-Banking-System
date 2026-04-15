from __future__ import annotations

import html
import re
import shutil
from pathlib import Path


ROOT = Path(r"C:\Users\abhar\OneDrive\Desktop\bank")
PROJECT = ROOT / "Online banking system"
ASSETS = ROOT / "report_assets"
SOURCE_HTML = ROOT / "FINAL_YEAR_PROJECT_REPORT_FINAL.html"
OUTPUT_HTML = ROOT / "FINAL_YEAR_PROJECT_REPORT_NORMAL.html"
OUTPUT_PDF = ROOT / "FINAL_YEAR_PROJECT_REPORT_NORMAL.pdf"


CODE_FILES = [
    ("app.py", PROJECT / "app.py", "app_py.svg", "This file contains the Flask application logic, routing, validation rules, session handling, database access, and customer-admin workflow control."),
    ("Procfile", PROJECT / "Procfile", "Procfile.svg", "This file defines the deployment start command used to launch the Flask application through Gunicorn in hosting environments."),
    ("README.md", PROJECT / "README.md", "README_md.svg", "This file provides the project overview, feature summary, and the main instructions required to understand and run the application."),
    ("requirements.txt", PROJECT / "requirements.txt", "requirements_txt.svg", "This file lists the Python dependencies required to install and execute the banking application successfully."),
    ("static/css/style.css", PROJECT / "static" / "css" / "style.css", "style_css.svg", "This stylesheet manages the premium visual presentation of the application, including layout, buttons, cards, forms, and responsive banking theme components."),
    ("templates/base.html", PROJECT / "templates" / "base.html", "base_html.svg", "This base template defines the shared page shell, navigation bar, footer area, flash message region, and reusable layout blocks."),
    ("templates/index.html", PROJECT / "templates" / "index.html", "index_html.svg", "This file implements the landing page and introduces the digital banking platform, feature highlights, and access actions."),
    ("templates/login.html", PROJECT / "templates" / "login.html", "login_html.svg", "This file contains the secure sign-in interface used for authenticating users and administrative accounts."),
    ("templates/register.html", PROJECT / "templates" / "register.html", "register_html.svg", "This file provides the new-account registration form and presents account opening in a structured interface."),
    ("templates/dashboard.html", PROJECT / "templates" / "dashboard.html", "dashboard_html.svg", "This template renders the main customer dashboard, showing balances, transaction metrics, recent activity, and quick actions."),
    ("templates/profile.html", PROJECT / "templates" / "profile.html", "profile_html.svg", "This file displays customer identity details, account insights, statement access, and security controls."),
    ("templates/change_password.html", PROJECT / "templates" / "change_password.html", "change_password_html.svg", "This file implements the password update form and supports secure credential maintenance."),
    ("templates/deposit.html", PROJECT / "templates" / "deposit.html", "deposit_html.svg", "This file defines the deposit transaction form and associated guidance for adding funds to the account."),
    ("templates/withdraw.html", PROJECT / "templates" / "withdraw.html", "withdraw_html.svg", "This file handles the withdrawal workflow and presents rules for controlled deduction of account balance."),
    ("templates/transfer.html", PROJECT / "templates" / "transfer.html", "transfer_html.svg", "This file contains the internal transfer form for moving funds between registered customer accounts."),
    ("templates/history.html", PROJECT / "templates" / "history.html", "history_html.svg", "This file shows the searchable transaction history table and supports review and export of account records."),
    ("templates/admin.html", PROJECT / "templates" / "admin.html", "admin_html.svg", "This file renders the administrator dashboard for customer review, portfolio monitoring, and activity inspection."),
]

APP_SCREENSHOTS: list[tuple[str, Path, str, str]] = []

ER_DIAGRAM = """<div class="diagram-block diagram-centered"><h4>Figure 4: Entity Relationship Diagram</h4><svg viewBox="0 0 980 520" xmlns="http://www.w3.org/2000/svg">
<rect x="70" y="90" width="340" height="280" fill="#eef3fb" stroke="#222" stroke-width="2"/>
<text x="100" y="128" font-size="22" font-weight="700">USERS</text>
<text x="100" y="170" font-size="18">PK id</text>
<text x="100" y="202" font-size="18">full_name</text>
<text x="100" y="234" font-size="18">account_number</text>
<text x="100" y="266" font-size="18">username</text>
<text x="100" y="298" font-size="18">password</text>
<text x="100" y="330" font-size="18">balance</text>
<text x="100" y="362" font-size="18">is_admin</text>
<rect x="570" y="90" width="340" height="280" fill="#eefaf5" stroke="#222" stroke-width="2"/>
<text x="600" y="128" font-size="22" font-weight="700">TRANSACTIONS</text>
<text x="600" y="170" font-size="18">PK id</text>
<text x="600" y="202" font-size="18">FK user_id</text>
<text x="600" y="234" font-size="18">action</text>
<text x="600" y="266" font-size="18">amount</text>
<text x="600" y="298" font-size="18">details</text>
<text x="600" y="330" font-size="18">created_at</text>
<line x1="410" y1="230" x2="570" y2="230" stroke="#222" stroke-width="3"/>
<text x="490" y="214" text-anchor="middle" font-size="18" font-weight="700">1 : Many</text>
</svg></div>"""


def wrap_line(text: str, width: int = 82) -> list[str]:
    if not text:
        return [""]
    out: list[str] = []
    current = text
    while len(current) > width:
        cut = current.rfind(" ", 0, width)
        if cut < max(10, width // 2):
            cut = width
        out.append(current[:cut])
        current = current[cut:].lstrip()
    out.append(current)
    return out


def render_code_svg(title: str, source: Path, out_path: Path) -> None:
    lines = source.read_text(encoding="utf-8").splitlines()
    rendered: list[tuple[str, str]] = []
    for idx, line in enumerate(lines[:60], start=1):
        for part in wrap_line(line.expandtabs(4)):
            rendered.append((f"{idx:>3}" if part == wrap_line(line.expandtabs(4))[0] else "   ", part))
    if len(lines) > 60:
        rendered.append(("...", "... file continues ..."))

    line_height = 24
    top = 64
    height = top + len(rendered) * line_height + 28
    width = 1280

    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" rx="18" fill="#f6f8fc"/>',
        '<rect x="18" y="18" width="1244" height="42" rx="12" fill="#25213f"/>',
        f'<text x="40" y="45" font-family="Consolas, monospace" font-size="20" font-weight="700" fill="#ffffff">{html.escape(title)}</text>',
        '<rect x="18" y="72" width="1244" height="{}" rx="14" fill="#ffffff" stroke="#d8dcef"/>'.format(height - 90),
    ]

    y = 104
    for number, content in rendered:
        svg_lines.append(f'<text x="44" y="{y}" font-family="Consolas, monospace" font-size="16" fill="#8a90a8">{html.escape(number)}</text>')
        svg_lines.append(f'<text x="98" y="{y}" font-family="Consolas, monospace" font-size="16" fill="#2e3255">{html.escape(content)}</text>')
        y += line_height

    svg_lines.append("</svg>")
    out_path.write_text("\n".join(svg_lines), encoding="utf-8")


def build_file_structure() -> str:
    return """<pre>
Online banking system/
|-- app.py
|-- bank.db
|-- Procfile
|-- README.md
|-- requirements.txt
|-- static/
|   |-- css/
|       |-- style.css
|-- templates/
|   |-- base.html
|   |-- index.html
|   |-- login.html
|   |-- register.html
|   |-- dashboard.html
|   |-- profile.html
|   |-- change_password.html
|   |-- deposit.html
|   |-- withdraw.html
|   |-- transfer.html
|   |-- history.html
|   |-- admin.html
</pre>"""


def build_highlights() -> str:
    return """<ul>
<li>Starter balance for newly created customer accounts.</li>
<li>Secure password hashing and protected user sessions.</li>
<li>Searchable transaction history with downloadable statement support.</li>
<li>Professional landing page, dashboard, and transaction workflow design.</li>
<li>Customer profile management and password update module.</li>
<li>Administrator dashboard with customer summaries and recent activity review.</li>
<li>Render-ready deployment support through Gunicorn and Procfile configuration.</li>
</ul>"""


def build_interface_section() -> str:
    return ""


def build_code_section() -> str:
    parts = [
        '<h2 class="page-break">22.6 Source File Screenshots and Brief Explanation</h2>',
        '<p>This section contains ordered code screenshots from the latest version of the project files. The screenshots are arranged continuously so each page is filled with code visuals before moving to the next page.</p>',
    ]
    for idx, (label, _, asset_name, desc) in enumerate(CODE_FILES, start=1):
        parts.append(f'<h3 class="page-break-tight">22.6.{idx} {html.escape(label)}</h3>')
        parts.append(f'<div class="shot-block"><h4>Code Screenshot: {html.escape(label)}</h4><img src="report_assets/{asset_name}" alt="{html.escape(label)} screenshot"></div>')
        parts.append(f'<p>{html.escape(desc)}</p>')
    return "\n".join(parts)


def tighten_layout(report: str) -> str:
    report = report.replace('@page { size: A4; margin: 0.34in; }', '@page { size: A4; margin: 0.24in 0.28in; }')
    report = report.replace('  line-height: 1.46;', '  line-height: 1.34;')
    report = report.replace('  width: 8.27in;\n  margin: 0.25in auto;', '  width: 8.27in;\n  margin: 0.12in auto;')
    report = report.replace('  padding: 0.12in 0.18in;', '  padding: 0.08in 0.1in;')
    report = report.replace('h1.chapter-title {\n  font-size: 20pt;\n  text-align: center;\n  text-transform: uppercase;\n  page-break-before: always;\n  margin-top: 0.2em;\n}', 'h1.chapter-title {\n  font-size: 20pt;\n  text-align: center;\n  text-transform: uppercase;\n  page-break-before: always;\n  page-break-after: avoid;\n  break-after: avoid-page;\n  margin-top: 0.08em;\n  margin-bottom: 0.35em;\n}')
    report = report.replace('h2.front-title {\n  font-size: 18pt;\n  text-align: center;\n  page-break-before: always;\n}', 'h2.front-title {\n  font-size: 18pt;\n  text-align: center;\n  page-break-before: always;\n  margin-top: 0.1em;\n  margin-bottom: 0.35em;\n}')
    report = report.replace('p, li, td, th { font-size: 11.5pt; text-align: justify; }', 'p, li, td, th { font-size: 11pt; text-align: justify; }')
    report = report.replace('ul, ol { margin-top: 0.35em; margin-bottom: 0.7em; }', 'ul, ol { margin-top: 0.22em; margin-bottom: 0.52em; }')
    report = report.replace('table { width: 100%; border-collapse: collapse; margin: 0.8em 0 1em; }', 'table { width: 100%; border-collapse: collapse; margin: 0.55em 0 0.75em; }')
    report = report.replace('.diagram-block, .shot-block {\n  margin: 0.8em auto 1em;\n  padding: 10px;\n  border: 1px solid #777;\n  background: #fcfcfc;\n  break-inside: avoid;\n  page-break-inside: avoid;\n  text-align: center;\n}', '.diagram-block, .shot-block {\n  margin: 0.5em auto 0.7em;\n  padding: 8px;\n  border: 1px solid #777;\n  background: #fcfcfc;\n  break-inside: avoid;\n  page-break-inside: avoid;\n  text-align: center;\n}')
    report = report.replace('.diagram-block svg,\n.shot-block img { width: 100%; height: auto; break-inside: avoid; page-break-inside: avoid; }', '.diagram-block svg,\n.shot-block img { width: 100%; height: auto; break-inside: avoid; page-break-inside: avoid; }\n.diagram-centered { max-width: 92%; }\n.keep-with-next { page-break-after: avoid; break-after: avoid-page; }\n.compact-gap { margin-top: 0.25em; margin-bottom: 0.35em; }\n.page-break-tight { page-break-before: auto; margin-top: 0.55em; margin-bottom: 0.22em; }\n.shot-block { margin: 0.28em auto 0.35em; padding: 6px; }\n.shot-block h4 { margin-bottom: 0.2em; font-size: 11.5pt; }\n.shot-block img { max-height: 8.35in; object-fit: contain; }\n.shot-block + p { margin-top: 0.18em; margin-bottom: 0.35em; }')
    report = report.replace('<hr>', '')
    return report


def improve_structure(report: str) -> str:
    report = report.replace('<h1 class="chapter-title">CHAPTER 8: SYSTEM ANALYSIS AND DESIGN</h1>\n\n<div class="diagram-block"><h4>Figure 1: System Overview Flowchart</h4>', '<h1 class="chapter-title keep-with-next">CHAPTER 8: SYSTEM ANALYSIS AND DESIGN</h1>\n<div class="diagram-block diagram-centered"><h4>Figure 1: System Overview Flowchart</h4>')
    report = report.replace('<h1 class="chapter-title">CHAPTER 10: DATABASE DESIGN</h1>\n\n<div class="diagram-block"><h4>Figure 4: Entity Relationship Diagram</h4><svg viewBox="0 0 980 520" xmlns="http://www.w3.org/2000/svg"><rect x="90" y="100" width="330" height="260" fill="#eef3fb" stroke="#222"/><text x="120" y="140" font-size="22">USERS</text><text x="120" y="180" font-size="18">PK id</text><text x="120" y="210" font-size="18">full_name</text><text x="120" y="240" font-size="18">account_number</text><text x="120" y="270" font-size="18">username</text><text x="120" y="300" font-size="18">password</text><text x="120" y="330" font-size="18">balance</text><text x="120" y="360" font-size="18">is_admin</text><rect x="560" y="100" width="330" height="260" fill="#eefaf5" stroke="#222"/><text x="590" y="140" font-size="22">TRANSACTIONS</text><text x="590" y="180" font-size="18">PK id</text><text x="590" y="210" font-size="18">FK user_id</text><text x="590" y="240" font-size="18">action</text><text x="590" y="270" font-size="18">amount</text><text x="590" y="300" font-size="18">details</text><text x="590" y="330" font-size="18">created_at</text><line x1="420" y1="230" x2="560" y2="230" stroke="#222" stroke-width="3"/><text x="490" y="215" text-anchor="middle" font-size="18">1 : Many</text></svg></div>', '<h1 class="chapter-title keep-with-next">CHAPTER 10: DATABASE DESIGN</h1>\n' + ER_DIAGRAM)
    report = report.replace('<div class="diagram-block"><h4>Figure 4: Entity Relationship Diagram</h4><svg viewBox="0 0 980 520" xmlns="http://www.w3.org/2000/svg"><rect x="90" y="100" width="330" height="260" fill="#eef3fb" stroke="#222"/><text x="120" y="140" font-size="22">USERS</text><text x="120" y="180" font-size="18">PK id</text><text x="120" y="210" font-size="18">full_name</text><text x="120" y="240" font-size="18">account_number</text><text x="120" y="270" font-size="18">username</text><text x="120" y="300" font-size="18">password</text><text x="120" y="330" font-size="18">balance</text><text x="120" y="360" font-size="18">is_admin</text><rect x="560" y="100" width="330" height="260" fill="#eefaf5" stroke="#222"/><text x="590" y="140" font-size="22">TRANSACTIONS</text><text x="590" y="180" font-size="18">PK id</text><text x="590" y="210" font-size="18">FK user_id</text><text x="590" y="240" font-size="18">action</text><text x="590" y="270" font-size="18">amount</text><text x="590" y="300" font-size="18">details</text><text x="590" y="330" font-size="18">created_at</text><line x1="420" y1="230" x2="560" y2="230" stroke="#222" stroke-width="3"/><text x="490" y="215" text-anchor="middle" font-size="18">1 : Many</text></svg></div>', ER_DIAGRAM)
    report = report.replace('<h2>22.1 Appendix A: Project File Structure</h2>', '<h2 class="compact-gap">22.1 Appendix A: Project File Structure</h2>')
    report = report.replace('<h2>22.2 Appendix B: Important Functional Highlights</h2>', '<h2 class="compact-gap">22.2 Appendix B: Important Functional Highlights</h2>')
    return report


def replace_section(text: str, start_marker: str, end_marker: str, replacement: str) -> str:
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    return text[:start] + replacement + text[end:]


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)

    for label, path, asset_name, _ in CODE_FILES:
        render_code_svg(label, path, ASSETS / asset_name)

    for _, src, asset_name, _ in APP_SCREENSHOTS:
        if src.exists():
            shutil.copyfile(src, ASSETS / asset_name)

    report = SOURCE_HTML.read_text(encoding="utf-8", errors="ignore")

    report = re.sub(
        r"<h2>22\.1 Appendix A: Project File Structure</h2>\s*<pre>.*?</pre>",
        "<h2>22.1 Appendix A: Project File Structure</h2>\n\n" + build_file_structure(),
        report,
        flags=re.S,
    )
    report = re.sub(
        r"<h2>22\.2 Appendix B: Important Functional Highlights</h2>\s*<ul>.*?</ul>",
        "<h2>22.2 Appendix B: Important Functional Highlights</h2>\n\n" + build_highlights(),
        report,
        flags=re.S,
    )

    code_section = build_code_section()
    ui_section = build_interface_section()
    report = replace_section(
        report,
        '<h2 class="page-break">22.6 Source File Screenshots and Brief Explanation</h2>',
        "  </div>\n</div>\n</body>\n</html>",
        ui_section + "\n" + code_section + "\n  </div>\n</div>\n</body>\n</html>",
    )

    report = report.replace("A significant focus of the project is security and usability.", "A significant focus of the project is security, usability, and presentation quality.")
    report = report.replace("The front end was redesigned to appear more professional and attractive.", "The front end was redesigned to appear more professional, premium, and suitable for final-year project demonstration.")
    report = report.replace("The home module acts as the entry point to the application. It introduces the system to the user, highlights the major features, and provides direct navigation to login and registration pages. It also presents the application as a digital banking product with a modern, professional visual style.", "The home module acts as the entry point to the application. It introduces the system to the user, highlights the major services, and provides direct navigation to login and registration pages. The latest version presents the application in a cleaner and more professional banking style.")
    report = tighten_layout(report)
    report = improve_structure(report)

    OUTPUT_HTML.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
