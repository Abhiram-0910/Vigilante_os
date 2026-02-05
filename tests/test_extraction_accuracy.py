"""
Brutal extraction accuracy tests for judge-style obfuscated inputs.
Run until 100% pass rate. Regex-based extraction must not miss these.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.tools import extract_scam_data
from app.services.fusion import verify_intelligence


def test_upi_spoken_digits():
    """UPI: nine eight seven six at paytm → 9876@paytm"""
    text = "UPI: nine eight seven six at paytm"
    result = extract_scam_data(text)
    verified = verify_intelligence(
        result,
        text,
    )
    assert "upi_ids" in verified
    upis = verified["upi_ids"]
    assert len(upis) >= 1, f"Expected at least one UPI, got {verified}"
    # Normalize: may be 9876@paytm (4 digits)
    assert any("9876" in u and "paytm" in u for u in upis), f"Expected 9876@paytm-like, got {upis}"


def test_upi_triple_zero():
    """nine eight seven six triple zero at paytm → 9876000@paytm"""
    text = "UPI: nine eight seven six triple zero at paytm"
    result = extract_scam_data(text)
    verified = verify_intelligence(result, text)
    assert len(verified.get("upi_ids", [])) >= 1, f"Expected UPI from triple zero, got {verified}"


def test_bank_account_spaces():
    """Account: 1234 5678 9012 3456 → digits concatenated 9-18 len"""
    text = "Account: 1234 5678 9012 3456"
    result = extract_scam_data(text)
    accounts = result.get("bank_accounts", [])
    assert len(accounts) >= 1, f"Expected bank account, got {result}"
    raw = "".join(c for c in text if c.isdigit())
    assert any(raw in a or a in raw for a in accounts) or any(
        9 <= len(a) <= 18 for a in accounts
    ), f"Expected 9-18 digit account, got {accounts}"


def test_phone_hyphens():
    """Call me at 98-88-77-66-55 → 9888776655"""
    text = "Call me at 98-88-77-66-55"
    result = extract_scam_data(text)
    phones = result.get("phone_numbers", [])
    assert "9888776655" in phones or any(p == "9888776655" for p in phones), (
        f"Expected 9888776655, got {phones}"
    )


def test_shortened_url():
    """bit.ly or short links"""
    text = "Click here https://bit.ly/pay-now to pay"
    result = extract_scam_data(text)
    urls = result.get("urls", [])
    assert len(urls) >= 1, f"Expected URL, got {result}"
    assert any("http" in u for u in urls), f"Expected http URL, got {urls}"


def test_combined_obfuscation():
    """Multiple obfuscations in one message"""
    text = "UPI: nine eight seven six at paytm. Call 98-88-77-66-55. Account: 1234 5678 9012."
    result = extract_scam_data(text)
    verified = verify_intelligence(result, text)
    assert len(verified.get("upi_ids", [])) >= 1 or len(result.get("upi_ids", [])) >= 1
    assert len(verified.get("phone_numbers", [])) >= 1 or len(result.get("phone_numbers", [])) >= 1


def test_upi_heavily_spaced():
    """UPI is 9 9 8 8 @ h d f c -> 9988@hdfc (space-collapsed extraction)"""
    text = "UPI is 9 9 8 8 @ h d f c"
    result = extract_scam_data(text)
    upis = result.get("upi_ids", [])
    assert len(upis) >= 1, f"Expected UPI from heavily spaced, got {result}"
    assert any("9988" in u and "hdfc" in u for u in upis), f"Expected 9988@hdfc-like, got {upis}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
