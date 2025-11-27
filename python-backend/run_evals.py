#!/usr/bin/env python3
"""
Script to run evaluations on the Business Partner multi-agent system.

Usage:
    python run_evals.py                    # Run all evaluations
    python run_evals.py --dataset looping  # Run specific dataset
    python run_evals.py --quick            # Run quick smoke tests
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
from langfuse import Langfuse
from langchain_core.messages import HumanMessage

from graph import graph
from state import BusinessPartnerState
from eval_datasets import (
    ONBOARDING_DATASET,
    STATE_PERSISTENCE_DATASET,
    ROUTING_DATASET,
)
from evaluators import (
    evaluate_no_looping,
    evaluate_state_extraction,
    evaluate_response_quality,
    evaluate_routing_accuracy,
    evaluate_onboarding_efficiency,
)

load_dotenv()

langfuse = Langfuse(
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    host=os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com"),
)


def create_state_from_input(messages: list) -> BusinessPartnerState:
    """Create initial state from test case input."""
    langchain_messages = []
    for msg in messages:
        if msg["role"] == "user":
            langchain_messages.append(HumanMessage(content=msg["content"]))
    
    return {
        "messages": langchain_messages[-1:] if langchain_messages else [],
        "session_id": "eval-session",
        "user_id": "eval-user",
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
            "photo_analysis_complete",
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


def run_onboarding_evaluations():
    """Run evaluations on onboarding dataset."""
    print("=" * 80)
    print("Running Onboarding Evaluations")
    print("=" * 80)
    
    results = []
    
    for test_case in ONBOARDING_DATASET:
        print(f"\n📋 Test: {test_case['name']}")
        
        # Create trace
        trace = langfuse.trace(
            name="eval-onboarding",
            metadata={"test_case": test_case["name"]}
        )
        
        try:
            # Run the graph
            initial_state = create_state_from_input(test_case["input"])
            config = {"configurable": {"thread_id": f"eval-{test_case['name']}"}}
            
            result = graph.invoke(initial_state, config=config)
            
            # Get response text
            response_text = ""
            if result.get("messages"):
                last_message = result["messages"][-1]
                if hasattr(last_message, "content"):
                    response_text = last_message.content
            
            # Evaluate
            looping_score = evaluate_no_looping(
                output=response_text,
                expected_state=test_case["expected_state"],
                forbidden_phrases=test_case.get("forbidden_phrases", [])
            )
            
            extraction_score = evaluate_state_extraction(
                output_state=result,
                expected_state=test_case["expected_state"]
            )
            
            # Log scores
            trace.score(name="no_looping", value=looping_score)
            trace.score(name="state_extraction", value=extraction_score)
            
            trace.update(
                output={"result": result},
                metadata={
                    "test_case": test_case["name"],
                    "looping_score": looping_score,
                    "extraction_score": extraction_score,
                }
            )
            
            results.append({
                "test_case": test_case["name"],
                "looping_score": looping_score,
                "extraction_score": extraction_score,
                "passed": looping_score >= 0.8 and extraction_score >= 0.8,
            })
            
            status = "✅ PASS" if results[-1]["passed"] else "❌ FAIL"
            print(f"  {status} - Looping: {looping_score:.2f}, Extraction: {extraction_score:.2f}")
            
        except Exception as e:
            trace.update(level="ERROR", output={"error": str(e)})
            print(f"  ❌ ERROR: {e}")
            results.append({
                "test_case": test_case["name"],
                "error": str(e),
                "passed": False,
            })
    
    # Summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    passed = sum(1 for r in results if r.get("passed", False))
    total = len(results)
    print(f"Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    
    return results


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run evaluations on Business Partner system")
    parser.add_argument("--dataset", choices=["onboarding", "routing", "all"], default="all")
    parser.add_argument("--quick", action="store_true", help="Run quick smoke tests only")
    
    args = parser.parse_args()
    
    if args.quick:
        # Run just one test case
        print("Running quick smoke test...")
        test_case = ONBOARDING_DATASET[0]
        # ... run single test ...
    elif args.dataset == "onboarding" or args.dataset == "all":
        run_onboarding_evaluations()
    # Add more dataset runners as needed
    
    langfuse.flush()
    print("\n✅ Evaluations complete. Check Langfuse UI for detailed results.")


if __name__ == "__main__":
    main()

