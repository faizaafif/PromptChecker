"""HTML reporter for PromptCheck.

Generates self-contained HTML reports from SuiteResult or ComparisonResult.
No external CSS/JS dependencies — everything is inline.
"""

from __future__ import annotations

import html
from datetime import datetime, timezone
from pathlib import Path

from promptcheck.models import ComparisonResult, SuiteResult


def _escape(text: str) -> str:
    """HTML-escape a string."""
    return html.escape(str(text))


def _status_badge(passed: bool | None, error: str | None) -> str:
    """Return an HTML span badge for a test status."""
    if error:
        return '<span class="badge badge-error">ERROR</span>'
    if passed:
        return '<span class="badge badge-pass">PASS</span>'
    return '<span class="badge badge-fail">FAIL</span>'


def _suite_summary_html(sr: SuiteResult) -> str:
    """Render a summary stats bar for one SuiteResult."""
    return (
        f'<div class="summary">'
        f'<span class="stat">Total: <strong>{sr.total}</strong></span>'
        f'<span class="stat pass">Passed: <strong>{sr.passed}</strong></span>'
        f'<span class="stat fail">Failed: <strong>{sr.failed}</strong></span>'
        f'<span class="stat error">Errors: <strong>{sr.errors}</strong></span>'
        f'<span class="stat">Duration: <strong>{sr.duration_seconds:.4f}s</strong></span>'
        f'</div>'
    )


def _test_rows_html(sr: SuiteResult) -> str:
    """Render table rows for each test result in a suite."""
    rows: list[str] = []
    for tr in sr.test_results:
        passed = tr.eval_result.passed if tr.eval_result else None
        badge = _status_badge(passed, tr.error)
        expected = _escape(
            str(tr.eval_result.expected) if tr.eval_result else "—"
        )
        actual = _escape(
            tr.eval_result.actual if tr.eval_result else tr.provider_result.response
        )
        message = ""
        if tr.error:
            message = _escape(tr.error)
        elif tr.eval_result and tr.eval_result.message:
            message = _escape(tr.eval_result.message)

        rows.append(
            f"<tr>"
            f"<td>{badge}</td>"
            f"<td>{_escape(tr.test_name)}</td>"
            f"<td><code>{_escape(tr.prompt)}</code></td>"
            f"<td>{expected}</td>"
            f"<td>{actual}</td>"
            f"<td>{message}</td>"
            f"<td>{tr.duration_seconds:.4f}s</td>"
            f"</tr>"
        )
    return "\n".join(rows)


_CSS = """\
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #f5f7fa; color: #1a1a2e; padding: 24px 16px;
    max-width: 1200px; margin: 0 auto;
}
h1 { font-size: 1.5rem; margin-bottom: 4px; }
.meta { color: #666; font-size: 0.85rem; margin-bottom: 20px; }
h2 { font-size: 1.2rem; margin: 24px 0 8px; }
.summary {
    display: flex; flex-wrap: wrap; gap: 16px;
    padding: 12px 16px; background: #fff;
    border-radius: 8px; border: 1px solid #e0e0e0;
    margin-bottom: 16px;
}
.stat { font-size: 0.9rem; }
.stat.pass strong { color: #16a34a; }
.stat.fail strong { color: #dc2626; }
.stat.error strong { color: #d97706; }
table {
    width: 100%; border-collapse: collapse;
    background: #fff; border-radius: 8px;
    overflow: hidden; border: 1px solid #e0e0e0;
}
th {
    background: #f0f0f5; text-align: left;
    padding: 10px 12px; font-size: 0.8rem;
    text-transform: uppercase; letter-spacing: 0.03em;
    color: #555; border-bottom: 2px solid #e0e0e0;
}
td {
    padding: 10px 12px; font-size: 0.85rem;
    border-bottom: 1px solid #f0f0f0;
    vertical-align: top; word-break: break-word;
}
tr:last-child td { border-bottom: none; }
code { background: #f5f5f5; padding: 2px 6px; border-radius: 4px; font-size: 0.82rem; }
.badge {
    display: inline-block; padding: 2px 10px;
    border-radius: 12px; font-size: 0.75rem;
    font-weight: 600; text-transform: uppercase;
}
.badge-pass { background: #dcfce7; color: #166534; }
.badge-fail { background: #fee2e2; color: #991b1b; }
.badge-error { background: #fef3c7; color: #92400e; }
.provider-section { margin-bottom: 32px; }
footer { margin-top: 32px; color: #999; font-size: 0.75rem; text-align: center; }
@media (max-width: 600px) {
    body { padding: 12px 8px; }
    .summary { gap: 8px; }
    td, th { padding: 8px 6px; font-size: 0.8rem; }
}
"""

_TABLE_HEAD = """\
<table>
<thead>
<tr>
    <th>Status</th>
    <th>Test</th>
    <th>Prompt</th>
    <th>Expected</th>
    <th>Actual</th>
    <th>Message</th>
    <th>Duration</th>
</tr>
</thead>
<tbody>
"""


def suite_to_html(result: SuiteResult) -> str:
    """Generate a self-contained HTML report for a single-provider suite."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return (
        f"<!DOCTYPE html>\n<html lang='en'>\n<head>\n"
        f"<meta charset='utf-8'>\n"
        f"<meta name='viewport' content='width=device-width, initial-scale=1'>\n"
        f"<title>PromptCheck — {_escape(result.suite_name)}</title>\n"
        f"<style>{_CSS}</style>\n"
        f"</head>\n<body>\n"
        f"<h1>PromptCheck Report</h1>\n"
        f"<p class='meta'>Suite: {_escape(result.suite_name)} · "
        f"Provider: {_escape(result.provider_name)} · Generated: {now}</p>\n"
        f"{_suite_summary_html(result)}\n"
        f"{_TABLE_HEAD}"
        f"{_test_rows_html(result)}\n"
        f"</tbody>\n</table>\n"
        f"<footer>Generated by PromptCheck</footer>\n"
        f"</body>\n</html>"
    )


def comparison_to_html(result: ComparisonResult) -> str:
    """Generate a self-contained HTML report for a multi-provider comparison."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    sections: list[str] = []
    for sr in result.suite_results:
        sections.append(
            f"<div class='provider-section'>\n"
            f"<h2>Provider: {_escape(sr.provider_name)}</h2>\n"
            f"{_suite_summary_html(sr)}\n"
            f"{_TABLE_HEAD}"
            f"{_test_rows_html(sr)}\n"
            f"</tbody>\n</table>\n"
            f"</div>"
        )

    body = "\n".join(sections)
    return (
        f"<!DOCTYPE html>\n<html lang='en'>\n<head>\n"
        f"<meta charset='utf-8'>\n"
        f"<meta name='viewport' content='width=device-width, initial-scale=1'>\n"
        f"<title>PromptCheck — {_escape(result.suite_name)}</title>\n"
        f"<style>{_CSS}</style>\n"
        f"</head>\n<body>\n"
        f"<h1>PromptCheck Comparison Report</h1>\n"
        f"<p class='meta'>Suite: {_escape(result.suite_name)} · "
        f"Providers: {result.provider_count} · "
        f"Duration: {result.total_duration_seconds:.4f}s · "
        f"Generated: {now}</p>\n"
        f"{body}\n"
        f"<footer>Generated by PromptCheck</footer>\n"
        f"</body>\n</html>"
    )


def to_html(result: SuiteResult | ComparisonResult) -> str:
    """Dispatch to the correct HTML generator based on result type."""
    if isinstance(result, ComparisonResult):
        return comparison_to_html(result)
    return suite_to_html(result)


def write_html_report(
    result: SuiteResult | ComparisonResult,
    path: str | Path,
) -> Path:
    """Write an HTML report to the given file path.

    Creates parent directories if they don't exist.

    Returns:
        The resolved Path to the written report file.
    """
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(to_html(result), encoding="utf-8")
    return report_path.resolve()
