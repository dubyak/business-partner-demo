"""
Evaluation datasets for the Business Partner multi-agent system.

These datasets test:
1. State extraction accuracy
2. Looping prevention
3. Multi-turn conversation quality
4. Agent routing accuracy
"""

# Test cases for onboarding flow
ONBOARDING_DATASET = [
    {
        "name": "simple_bakery_onboarding",
        "input": [
            {"role": "user", "content": "I have a bakery in Condesa"}
        ],
        "expected_state": {
            "business_type": "bakery",
            "location": "Condesa",
        },
        "expected_behavior": "should NOT ask for business type or location again",
        "expected_next_questions": ["years operating", "employees", "revenue"]
    },
    {
        "name": "complete_onboarding_flow",
        "input": [
            {"role": "user", "content": "I have a bakery in Condesa"},
            {"role": "user", "content": "3 years, 3 employees"},
            {"role": "user", "content": "5k revenue, 3k expenses"},
            {"role": "user", "content": "I need a second oven"},
        ],
        "expected_state": {
            "business_type": "bakery",
            "location": "Condesa",
            "years_operating": 3,
            "num_employees": 3,
            "monthly_revenue": 5000,
            "monthly_expenses": 3000,
            "loan_purpose": "second oven",
        },
        "expected_behavior": "should request photos or proceed to underwriting",
    },
    {
        "name": "looping_prevention_test",
        "input": [
            {"role": "user", "content": "I have a bakery in Condesa"},
            {"role": "assistant", "content": "Great! How long have you been operating?"},
            {"role": "user", "content": "3 years"},
            # After this, agent should NOT ask "what type of business" or "where are you located"
        ],
        "expected_state": {
            "business_type": "bakery",
            "location": "Condesa",
            "years_operating": 3,
        },
        "forbidden_phrases": [
            "what type of business",
            "where are you located",
            "what kind of business",
        ],
    },
]

# Test cases for state persistence
STATE_PERSISTENCE_DATASET = [
    {
        "name": "state_persists_between_turns",
        "turns": [
            {
                "input": [{"role": "user", "content": "I have a bakery in Condesa"}],
                "expected_state_after": {
                    "business_type": "bakery",
                    "location": "Condesa",
                }
            },
            {
                "input": [{"role": "user", "content": "3 years"}],
                "expected_state_after": {
                    "business_type": "bakery",  # Should still be there
                    "location": "Condesa",  # Should still be there
                    "years_operating": 3,
                }
            },
        ]
    }
]

# Test cases for agent routing
ROUTING_DATASET = [
    {
        "name": "routes_to_underwriting_when_ready",
        "input": [
            {"role": "user", "content": "I have a bakery in Condesa"},
            {"role": "user", "content": "3 years, 3 employees"},
            {"role": "user", "content": "5k revenue, 3k expenses"},
            {"role": "user", "content": "I need a second oven"},
            # Upload photo here (simulated)
        ],
        "expected_routing": ["business_partner", "underwriting", "business_partner", "end"],
        "required_state": {
            "business_type": "bakery",
            "location": "Condesa",
            "years_operating": 3,
            "num_employees": 3,
            "monthly_revenue": 5000,
            "monthly_expenses": 3000,
            "loan_purpose": "second oven",
            "photo_insights": [{}],  # At least one photo analyzed
        }
    }
]



