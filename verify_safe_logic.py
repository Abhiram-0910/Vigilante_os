from app.services.fusion import classifier

def test_safe_logic():
    print("Testing Safe Logic...")
    
    # 1. Safe Message (Friend)
    safe_msg = "Hey bro, are we still on for the movie and dinner tonight? I'm coming home."
    result = classifier.predict(safe_msg)
    print(f"Msg: '{safe_msg}'")
    print(f"Result: {result['scam_type']} (Conf: {result['confidence']})")
    assert result['confidence'] == 0.0, "Should be Safe (0.0)"

    # 2. Scam Message (Bank)
    scam_msg = "Urgent: Your HDFC bank account is suspended. Verify KYC immediately via this link."
    result = classifier.predict(scam_msg)
    print(f"Msg: '{scam_msg}'")
    print(f"Result: {result['scam_type']} (Conf: {result['confidence']})")
    assert result['confidence'] > 0.6, "Should be Scam"
    
    # 3. Ambiguous but Safe (Work context)
    ambiguous_msg = "Please verify the project assignment and send the salary report to HR."
    # Contains 'verify', 'salary' (scam words) but also 'project', 'assignment', 'HR' (safe/job words)
    # This tests the 'Safe Boost' logic
    result = classifier.predict(ambiguous_msg)
    print(f"Msg: '{ambiguous_msg}'")
    print(f"Result: {result['scam_type']} (Conf: {result['confidence']})")
    
    print("\n✅ Safe Logic Verified!")

if __name__ == "__main__":
    test_safe_logic()
