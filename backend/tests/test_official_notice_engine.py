"""Tests for official notice and scanned table breakdown extraction."""

from app.services.official_notice_engine import extract_official_notice


NOTICE_TEXT = """
EXTRAORDINARY REGISTERED NO.PIII GOVERNMENT GAZETTE KHYBER PAKHTUNKHWA
Published by Authority
PESHAWAR,WEDNESDAY, 16 JULY, 2025.
KHYBER PAKHTUNKHWA REVENUE AUTHORITY
NOTIFICATION
Peshawar Dated,the 16 June, 2025.
No. KPRA/ADMN/GN/2025/3337. In exercise of the powers conferred under sub-section 3of
section 10 read with section 14-A of the Khyber Pakhtunkhwa Sales Tax on Services Act, 2022
the Policy Board of the Khyber Pakhtunkhwa Revenue Authority is pleased to specify the services
for which the liability to pay tax shall be on the person other than the service provider.
Taxable Service S.No of the Second Schedule Heading Description Person other than service provider
Rate of Tax Customs 9806.3000 Custom House Agents Pakistan Single Window Fixed rate of Rs. 3.000/-per goods declaration.
This notification is issued with immediate effect. The person made liable to pay tax shall ensure
timely collection and payment of sales tax on services not later than the 15 day of the following tax period.
All provisions apply in relation to non-payment or short-payment, e-filing of return,
maintenance of record, imposition of penalty and default surcharge and recovery of tax.
"""


def test_extract_official_notice_returns_structured_breakdown() -> None:
    breakdown = extract_official_notice(NOTICE_TEXT)

    assert breakdown is not None
    assert breakdown.issuing_authority == "Khyber Pakhtunkhwa Revenue Authority"
    assert breakdown.notice_type == "notification"
    assert breakdown.notice_number == "KPRA/ADMN/GN/2025/3337"
    assert breakdown.gazette_date == "16 JULY, 2025"
    assert breakdown.issue_date == "16 June, 2025"
    assert "section 10" in (breakdown.legal_basis or "").lower()
    assert "sales tax" in (breakdown.subject or "").lower()
    assert breakdown.effective_timing == "immediate effect"
    assert breakdown.payment_timing == "not later than the 15 day of the following tax period"
    assert breakdown.table_rows
    row = breakdown.table_rows[0]
    assert row.heading == "9806.3000"
    assert row.service == "Custom House Agents"
    assert row.liable_party == "Pakistan Single Window"
    assert row.rate_or_amount == "Rs. 3,000/- per goods declaration"
    assert any("collection and payment" in duty for duty in breakdown.compliance_duties)
    assert any("penalty" in item for item in breakdown.consequences)
    assert breakdown.confidence in {"medium", "high"}


def test_extract_official_notice_returns_none_for_unrelated_text() -> None:
    assert extract_official_notice("Admission offer letter with a scholarship deadline.") is None


def test_table_row_handles_ocr_reordered_service_words() -> None:
    text = """
    GOVERNMENT GAZETTE KHYBER PAKHTUNKHWA
    KHYBER PAKHTUNKHWA REVENUE AUTHORITY NOTIFICATION
    No. KPRA/ADMN/GN/2025/3337.
    Taxable Service S.No Person Rate of Tax Schedule provider Customs Fixed rate of Rs. 5
    9806.3000 J 0 Custom Pakistan Single Window 3.000/-per goods House Agents declaration.
    """

    breakdown = extract_official_notice(text)

    assert breakdown is not None
    assert breakdown.table_rows
    assert breakdown.table_rows[0].service == "Custom House Agents"
    assert breakdown.table_rows[0].liable_party == "Pakistan Single Window"
    assert breakdown.table_rows[0].rate_or_amount == "Rs. 3,000/- per goods declaration"
