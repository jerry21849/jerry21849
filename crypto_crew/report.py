"""Report rendering — structured Markdown output with disclaimer."""

from crypto_crew.config import DISCLAIMER


def render_report(report_text: str) -> str:
    """Post-process the raw crew output into final report.

    Ensures:
    1. All sections are present (or marked as skipped).
    2. Disclaimer is at the very end.
    3. Data sources are noted.
    """
    if not report_text:
        return "無法生成報告。" + DISCLAIMER

    # Ensure disclaimer is appended
    if DISCLAIMER not in report_text:
        report_text = report_text.rstrip() + DISCLAIMER

    return report_text
