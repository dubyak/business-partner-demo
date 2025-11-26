#!/usr/bin/env python3
"""
Test script to verify task completion tracking and phase transitions.

This script simulates a conversation flow and verifies:
1. Tasks are marked as complete when information is collected
2. Phase transitions occur correctly
3. Underwriting is only called when all tasks are complete
"""

import os
# Mock database imports to avoid requiring Supabase credentials
import sys
from unittest.mock import MagicMock
sys.modules['db'] = MagicMock()

from state import BusinessPartnerState
from agents.onboarding_agent import OnboardingAgent
from agents.underwriting_agent import UnderwritingAgent

def test_task_tracking():
    """Test that tasks are properly tracked."""
    print("=" * 60)
    print("TEST 1: Task Completion Tracking")
    print("=" * 60)
    
    agent = OnboardingAgent()
    
    # Initial state
    state: BusinessPartnerState = {
        "messages": [],
        "session_id": "test-session",
        "user_id": "test-user",
        "conversation_id": None,
        "business_name": None,
        "business_type": None,
        "location": None,
        "years_operating": None,
        "monthly_revenue": None,
        "monthly_expenses": None,
        "num_employees": None,
        "loan_purpose": None,
        "photos": [],
        "photo_insights": [],
        "risk_score": None,
        "risk_tier": None,
        "key_risk_factors": [],
        "key_strengths": [],
        "loan_offer": None,
        "phase": "onboarding",
        "onboarding_stage": "info_gathering",
        "info_complete": False,
        "photos_received": False,
        "loan_offered": False,
        "loan_accepted": False,
        "required_tasks": [
            "confirm_eligibility",
            "capture_business_profile",
            "capture_business_financials",
            "capture_business_photos",
            "photo_analysis_complete"
        ],
        "completed_tasks": [],
        "next_agent": None,
        "system_prompt": None,
        "servicing_type": None,
        "disbursement_status": None,
        "disbursement_info": None,
        "repayment_status": None,
        "repayment_info": None,
        "repayment_method": None,
        "payment_schedule": None,
        "repayment_impact_explanation": None,
        "recovery_status": None,
        "recovery_info": None,
        "recovery_response": None,
        "bank_account": None,
        "persona_id": None,
        "coaching_advice": None,
    }
    
    # Simulate collecting business info
    print("\n1. Adding business type and location...")
    state["business_type"] = "corner shop"
    state["location"] = "Mexico City"
    result = agent.process(state)
    state.update(result)
    print(f"   Completed tasks: {state.get('completed_tasks', [])}")
    assert "confirm_eligibility" in state.get("completed_tasks", []), "confirm_eligibility should be marked complete"
    print("   ✓ confirm_eligibility marked complete")
    
    # Simulate collecting more business info
    print("\n2. Adding years operating and employees...")
    state["years_operating"] = 3
    state["num_employees"] = 1
    result = agent.process(state)
    state.update(result)
    print(f"   Completed tasks: {state.get('completed_tasks', [])}")
    assert "capture_business_profile" in state.get("completed_tasks", []), "capture_business_profile should be marked complete"
    print("   ✓ capture_business_profile marked complete")
    
    # Simulate collecting financial info
    print("\n3. Adding financial information...")
    state["monthly_revenue"] = 25000.0
    state["monthly_expenses"] = 18000.0
    state["loan_purpose"] = "Buy inventory"
    result = agent.process(state)
    state.update(result)
    print(f"   Completed tasks: {state.get('completed_tasks', [])}")
    assert "capture_business_financials" in state.get("completed_tasks", []), "capture_business_financials should be marked complete"
    print("   ✓ capture_business_financials marked complete")
    
    # Simulate adding photos
    print("\n4. Adding business photos...")
    state["photos"] = ["fake_base64_photo_data"]
    result = agent.process(state)
    state.update(result)
    print(f"   Completed tasks: {state.get('completed_tasks', [])}")
    assert "capture_business_photos" in state.get("completed_tasks", []), "capture_business_photos should be marked complete"
    print("   ✓ capture_business_photos marked complete")
    
    # Note: photo_analysis_complete would be marked when photo is actually analyzed
    # For this test, we'll manually add a photo insight
    print("\n5. Simulating photo analysis...")
    from state import PhotoInsight
    state["photo_insights"] = [PhotoInsight(
        photo_index=0,
        cleanliness_score=8.0,
        organization_score=7.5,
        stock_level="medium",
        business_layout_type="small_shop",
        evidence_flags=["has_signage"],
        insights=["Well-organized inventory"],
        coaching_tips=["Keep up the good organization"]
    )]
    result = agent.process(state)
    state.update(result)
    print(f"   Completed tasks: {state.get('completed_tasks', [])}")
    assert "photo_analysis_complete" in state.get("completed_tasks", []), "photo_analysis_complete should be marked complete"
    print("   ✓ photo_analysis_complete marked complete")
    
    # Check if all tasks are complete
    print("\n6. Verifying all tasks complete...")
    all_complete = agent._check_all_tasks_complete(state)
    print(f"   All tasks complete: {all_complete}")
    assert all_complete, "All tasks should be complete"
    print("   ✓ All tasks are complete")
    
    # Check if underwriting should be called
    print("\n7. Checking if underwriting should be called...")
    should_call = agent._should_call_underwriting_agent(state)
    print(f"   Should call underwriting: {should_call}")
    assert should_call, "Should call underwriting when all tasks are complete"
    print("   ✓ Underwriting should be called")
    
    print("\n" + "=" * 60)
    print("✓ TEST 1 PASSED: Task completion tracking works correctly")
    print("=" * 60)


def test_phase_transitions():
    """Test that phase transitions occur correctly."""
    print("\n" + "=" * 60)
    print("TEST 2: Phase Transitions")
    print("=" * 60)
    
    agent = OnboardingAgent()
    underwriting_agent = UnderwritingAgent()
    
    # Start in onboarding phase
    state: BusinessPartnerState = {
        "messages": [],
        "session_id": "test-session",
        "user_id": "test-user",
        "conversation_id": None,
        "business_type": "corner shop",
        "location": "Mexico City",
        "years_operating": 3,
        "num_employees": 1,
        "monthly_revenue": 25000.0,
        "monthly_expenses": 18000.0,
        "loan_purpose": "Buy inventory",
        "photos": ["fake_photo"],
        "photo_insights": [{
            "photo_index": 0,
            "cleanliness_score": 8.0,
            "organization_score": 7.5,
            "stock_level": "medium",
            "business_layout_type": "small_shop",
            "evidence_flags": [],
            "insights": [],
            "coaching_tips": []
        }],
        "risk_score": None,
        "risk_tier": None,
        "key_risk_factors": [],
        "key_strengths": [],
        "loan_offer": None,
        "phase": "onboarding",
        "onboarding_stage": "info_gathering",
        "info_complete": True,
        "photos_received": True,
        "loan_offered": False,
        "loan_accepted": False,
        "required_tasks": [
            "confirm_eligibility",
            "capture_business_profile",
            "capture_business_financials",
            "capture_business_photos",
            "photo_analysis_complete"
        ],
        "completed_tasks": [
            "confirm_eligibility",
            "capture_business_profile",
            "capture_business_financials",
            "capture_business_photos",
            "photo_analysis_complete"
        ],
        "next_agent": "underwriting",
        "system_prompt": None,
        "servicing_type": None,
        "disbursement_status": None,
        "disbursement_info": None,
        "repayment_status": None,
        "repayment_info": None,
        "repayment_method": None,
        "payment_schedule": None,
        "repayment_impact_explanation": None,
        "recovery_status": None,
        "recovery_info": None,
        "recovery_response": None,
        "bank_account": None,
        "persona_id": None,
        "coaching_advice": None,
    }
    
    print("\n1. Starting in 'onboarding' phase...")
    print(f"   Current phase: {state['phase']}")
    assert state["phase"] == "onboarding", "Should start in onboarding phase"
    print("   ✓ Phase is 'onboarding'")
    
    # Call underwriting (simulate)
    print("\n2. Calling underwriting agent...")
    underwriting_result = underwriting_agent.process(state)
    state.update(underwriting_result)
    print(f"   Loan offer generated: {state.get('loan_offer') is not None}")
    
    # Process with business_partner agent - should transition to "offer" phase
    print("\n3. Processing with business_partner agent (should transition to 'offer' phase)...")
    result = agent.process(state)
    state.update(result)
    print(f"   Current phase: {state.get('phase')}")
    assert state.get("phase") == "offer", "Should transition to 'offer' phase after loan offer"
    print("   ✓ Phase transitioned to 'offer'")
    
    # Simulate loan acceptance
    print("\n4. Simulating loan acceptance...")
    state["loan_accepted"] = True
    from langchain_core.messages import HumanMessage
    state["messages"] = [HumanMessage(content="Yes, I accept")]
    result = agent.process(state)
    state.update(result)
    print(f"   Current phase: {state.get('phase')}")
    # Should still be "offer" until disbursement
    assert state.get("phase") in ["offer", "post_disbursement"], "Should be in offer or post_disbursement phase"
    print("   ✓ Phase handling loan acceptance")
    
    # Simulate disbursement completion
    print("\n5. Simulating disbursement completion...")
    state["disbursement_status"] = "completed"
    result = agent.process(state)
    state.update(result)
    print(f"   Current phase: {state.get('phase')}")
    assert state.get("phase") == "post_disbursement", "Should transition to 'post_disbursement' phase"
    print("   ✓ Phase transitioned to 'post_disbursement'")
    
    # Simulate recovery status (delinquent)
    print("\n6. Simulating recovery status (delinquent)...")
    state["recovery_status"] = "in_conversation"
    result = agent.process(state)
    state.update(result)
    print(f"   Current phase: {state.get('phase')}")
    assert state.get("phase") == "delinquent", "Should transition to 'delinquent' phase"
    print("   ✓ Phase transitioned to 'delinquent'")
    
    print("\n" + "=" * 60)
    print("✓ TEST 2 PASSED: Phase transitions work correctly")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_task_tracking()
        test_phase_transitions()
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

