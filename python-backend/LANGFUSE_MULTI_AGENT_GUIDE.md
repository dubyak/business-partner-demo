# Langfuse Multi-Agent Tracing & Evaluation Guide

## 📊 Part 1: Best Practices for Multi-Agent Tracing

### Current Setup Analysis

Your current setup uses:
- **LangGraph** for orchestration (StateGraph with conditional routing)
- **Langfuse decorators** (`@observe`) on agent methods
- **Top-level trace** in `main.py` for each conversation turn
- **Nested observations** for each agent execution

### Recommended Improvements

#### 1. **Hierarchical Trace Structure**

**Current**: Each turn creates a trace, agents create observations
**Best Practice**: Create a clear hierarchy that shows the full workflow

```python
# In main.py - Create trace at conversation level
trace = langfuse.trace(
    name="business-partner-conversation",
    session_id=session_id,
    user_id=user_id,
    metadata={
        "turn_number": get_turn_number(session_id),  # Track conversation progress
        "phase": initial_state.get("phase", "onboarding"),
    }
)

# Each agent method should create a span (not just observation)
# Use @observe decorator which automatically creates spans
```

#### 2. **State Tracking in Traces**

**Current**: State info in metadata
**Best Practice**: Track state transitions explicitly

```python
# Add state snapshots at key points
trace.span(
    name="state-transition",
    metadata={
        "from_phase": old_phase,
        "to_phase": new_phase,
        "state_snapshot": {
            "business_type": state.get("business_type"),
            "completed_tasks": state.get("completed_tasks", []),
        }
    }
)
```

#### 3. **Agent Routing Decisions**

**Current**: Routing logic in `route_after_business_partner`
**Best Practice**: Log routing decisions with context

```python
# In graph.py routing function
def route_after_business_partner(state: BusinessPartnerState):
    next_agent = state.get("next_agent")
    
    # Log routing decision
    langfuse_context.update_current_observation(
        metadata={
            "routing_decision": next_agent,
            "routing_reason": {
                "all_tasks_complete": all_tasks_complete,
                "has_photo_insights": len(state.get("photo_insights", [])) > 0,
                "loan_offered": state.get("loan_offered", False),
            }
        }
    )
    
    return next_agent or "end"
```

#### 4. **Error Handling & Recovery**

**Best Practice**: Wrap agent calls with error tracking

```python
@observe(name="business-partner-agent-process")
def process(self, state: BusinessPartnerState) -> Dict:
    try:
        # ... agent logic ...
    except Exception as e:
        langfuse_context.update_current_observation(
            level="ERROR",
            output={"error": str(e), "error_type": type(e).__name__},
            metadata={"state_at_error": state}
        )
        raise
```

#### 5. **Cost Tracking Per Agent**

**Best Practice**: Track costs separately for each agent

```python
# Each agent should log its own token usage
@observe(name="underwriting-agent-process")
def process(self, state: BusinessPartnerState):
    # ... agent logic ...
    # Token usage is automatically tracked by @observe decorator
    # But you can add custom cost metadata
    langfuse_context.update_current_observation(
        metadata={
            "agent_type": "underwriting",
            "estimated_cost_usd": calculate_cost(input_tokens, output_tokens),
        }
    )
```

### Recommended Trace Structure

```
Session: session-abc123
└─ Trace: business-partner-conversation (turn 1)
   ├─ Metadata: {phase: "onboarding", turn_number: 1}
   ├─ Span: state-loading
   │  └─ Observation: checkpoint-load
   ├─ Span: business-partner-agent-process
   │  ├─ Observation: extract-business-info
   │  ├─ Observation: generate-response
   │  └─ Observation: photo-analysis (if photos)
   ├─ Span: routing-decision
   │  └─ Metadata: {next_agent: "underwriting", reason: {...}}
   ├─ Span: underwriting-agent-process (if routed)
   │  ├─ Observation: calculate-risk-score
   │  └─ Observation: generate-loan-offer
   └─ Span: state-persistence
      └─ Observation: checkpoint-save
```

---

## 🧪 Part 2: Evaluation Setup

### Evaluation Strategy for Multi-Agent Systems

#### 1. **Unit-Level Evaluations** (Per Agent)

Evaluate each agent independently:

**Business Partner Agent:**
- **Information Extraction Accuracy**: Does it correctly extract business info?
- **Context Awareness**: Does it avoid asking for already-collected info?
- **Response Quality**: Is the response helpful and appropriate?

**Underwriting Agent:**
- **Risk Assessment Accuracy**: Does risk tier match business profile?
- **Offer Consistency**: Are offers reasonable given the inputs?

**Servicing Agent:**
- **Payment Plan Quality**: Are plans realistic and helpful?
- **Empathy**: Is the tone appropriate for difficult situations?

**Coaching Agent:**
- **Advice Relevance**: Is advice specific to the business type?
- **Actionability**: Are suggestions concrete and testable?

#### 2. **Integration Evaluations** (End-to-End)

Evaluate the full workflow:

- **Onboarding Completion**: Can users complete onboarding in < 7 exchanges?
- **State Persistence**: Does state persist correctly between turns?
- **Routing Accuracy**: Are agents called at the right times?
- **Conversation Quality**: Is the overall experience smooth?

#### 3. **Multi-Turn Conversation Evaluations**

Test full conversation flows:

- **Context Retention**: Does the agent remember earlier information?
- **Progressive Disclosure**: Does it gather info efficiently?
- **Error Recovery**: How does it handle user corrections?

### Implementation Guide

#### Step 1: Create Evaluation Datasets

```python
# python-backend/eval_datasets.py

ONBOARDING_DATASET = [
    {
        "input": [
            {"role": "user", "content": "I have a bakery in Condesa"}
        ],
        "expected_state": {
            "business_type": "bakery",
            "location": "Condesa",
        },
        "expected_behavior": "should NOT ask for business type or location again"
    },
    {
        "input": [
            {"role": "user", "content": "I have a bakery in Condesa"},
            {"role": "user", "content": "3 years, 3 employees"},
            {"role": "user", "content": "5k revenue, 3k expenses"},
        ],
        "expected_state": {
            "business_type": "bakery",
            "location": "Condesa",
            "years_operating": 3,
            "num_employees": 3,
            "monthly_revenue": 5000,
            "monthly_expenses": 3000,
        },
        "expected_behavior": "should request photos or ask about loan purpose"
    },
    # ... more test cases
]

LOOPING_PREVENTION_DATASET = [
    {
        "name": "should_not_ask_twice",
        "conversation": [
            {"role": "user", "content": "I have a bakery in Condesa"},
            {"role": "assistant", "content": "..."},
            {"role": "user", "content": "3 years"},
            # After this, agent should NOT ask "what type of business" again
        ],
        "evaluation": {
            "should_not_contain": ["what type of business", "where are you located"],
            "should_contain": ["bakery", "Condesa"]  # Should acknowledge what it knows
        }
    }
]
```

#### Step 2: Create Evaluators

```python
# python-backend/evaluators.py

from langfuse import Langfuse
from langfuse.decorators import langfuse_eval

langfuse = Langfuse(
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    host=os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com"),
)

@langfuse_eval
def evaluate_no_looping(output: str, expected_state: dict) -> float:
    """
    Evaluates if agent avoids asking for already-collected information.
    Returns score 0-1 (1 = perfect, 0 = asked for info it already has)
    """
    score = 1.0
    
    # Check if output asks for business_type when it's already collected
    if expected_state.get("business_type") and "what type of business" in output.lower():
        score -= 0.5
    
    # Check if output asks for location when it's already collected
    if expected_state.get("location") and "where are you located" in output.lower():
        score -= 0.5
    
    return max(0.0, score)

@langfuse_eval
def evaluate_state_extraction(output_state: dict, expected_state: dict) -> float:
    """
    Evaluates if state extraction is accurate.
    Returns score 0-1 based on how many fields match.
    """
    matches = 0
    total = 0
    
    for key, expected_value in expected_state.items():
        if expected_value is not None:
            total += 1
            actual_value = output_state.get(key)
            if actual_value == expected_value:
                matches += 1
            elif isinstance(expected_value, str) and isinstance(actual_value, str):
                # Fuzzy match for strings
                if expected_value.lower() in actual_value.lower() or actual_value.lower() in expected_value.lower():
                    matches += 0.5
    
    return matches / total if total > 0 else 0.0

@langfuse_eval
def evaluate_response_quality(output: str, context: dict) -> float:
    """
    Uses LLM-as-a-Judge to evaluate response quality.
    """
    # This would use Langfuse's LLM-as-a-Judge feature
    # See Langfuse docs for implementation
    pass
```

#### Step 3: Run Evaluations

```python
# python-backend/run_evals.py

import asyncio
from graph import graph
from state import BusinessPartnerState
from eval_datasets import ONBOARDING_DATASET
from evaluators import evaluate_no_looping, evaluate_state_extraction

async def run_evaluation_suite():
    """Run all evaluations and log results to Langfuse."""
    
    results = []
    
    for test_case in ONBOARDING_DATASET:
        # Create trace for this test
        trace = langfuse.trace(
            name="eval-onboarding",
            metadata={"test_case": test_case.get("name", "unnamed")}
        )
        
        # Run the graph
        initial_state = create_state_from_input(test_case["input"])
        result = graph.invoke(initial_state, config={"configurable": {"thread_id": f"eval-{test_case['name']}"}})
        
        # Evaluate
        looping_score = evaluate_no_looping(
            output=result.get("messages", [])[-1].content if result.get("messages") else "",
            expected_state=test_case["expected_state"]
        )
        
        extraction_score = evaluate_state_extraction(
            output_state=result,
            expected_state=test_case["expected_state"]
        )
        
        # Log scores
        trace.score(name="no_looping", value=looping_score)
        trace.score(name="state_extraction", value=extraction_score)
        
        results.append({
            "test_case": test_case.get("name"),
            "looping_score": looping_score,
            "extraction_score": extraction_score,
        })
        
        trace.update(output={"result": result})
    
    return results
```

#### Step 4: LLM-as-a-Judge Evaluators

Create evaluators in Langfuse UI:

1. **Go to Langfuse UI** → Evaluators → Create New
2. **Name**: "response-quality-judge"
3. **Type**: LLM-as-a-Judge
4. **Prompt**:
```
You are evaluating a business loan assistant's response.

Context: The assistant is helping a small business owner get a loan.
The user has already provided: {collected_info}

User message: {user_message}
Assistant response: {assistant_response}

Evaluate on a scale of 0-1:
- Does the assistant avoid asking for information it already has? (0.3 weight)
- Is the response helpful and appropriate? (0.3 weight)
- Does it move the conversation forward? (0.2 weight)
- Is the tone professional but warm? (0.2 weight)

Return a JSON object with:
{
  "score": 0.0-1.0,
  "reasoning": "brief explanation"
}
```

#### Step 5: Create Experiments

```python
# python-backend/experiments.py

from langfuse import Langfuse

langfuse = Langfuse(...)

# Create dataset
dataset = langfuse.create_dataset(name="onboarding-quality")

# Add test cases
for test_case in ONBOARDING_DATASET:
    dataset.create_item(
        input=test_case["input"],
        expected_output=test_case["expected_state"]
    )

# Run experiment with different prompt versions
experiment = langfuse.create_experiment(
    name="prompt-version-comparison",
    dataset_id=dataset.id
)

# Test version 6 vs version 7
for version in [6, 7]:
    # Run dataset through graph with that prompt version
    # Results automatically logged to experiment
    pass
```

### Evaluation Metrics to Track

1. **Looping Prevention Score**: % of conversations that don't ask for info twice
2. **State Extraction Accuracy**: % of fields correctly extracted
3. **Onboarding Completion Rate**: % of users who complete onboarding
4. **Average Exchanges to Completion**: Target < 7 exchanges
5. **Agent Routing Accuracy**: % of correct routing decisions
6. **Response Quality Score**: LLM-as-a-Judge score (0-1)
7. **Cost per Conversation**: Track token usage and costs

### Continuous Evaluation Pipeline

```python
# python-backend/ci_eval.py
# Run this in CI/CD pipeline

def run_ci_evaluations():
    """Run critical evaluations on every commit."""
    
    critical_tests = [
        "no_looping",
        "state_extraction",
        "routing_accuracy",
    ]
    
    results = {}
    for test_name in critical_tests:
        score = run_evaluation(test_name)
        results[test_name] = score
        
        # Fail CI if critical tests fail
        if score < 0.8:  # 80% threshold
            raise Exception(f"Evaluation failed: {test_name} scored {score}")
    
    return results
```

---

## 🎯 Recommended Next Steps

1. **Improve Trace Structure**
   - Add explicit state transition spans
   - Log routing decisions with context
   - Track costs per agent

2. **Create Evaluation Datasets**
   - Start with looping prevention dataset
   - Add state extraction test cases
   - Create multi-turn conversation scenarios

3. **Set Up LLM-as-a-Judge Evaluators**
   - Response quality evaluator
   - Context awareness evaluator
   - Efficiency evaluator

4. **Run Baseline Evaluations**
   - Establish current performance metrics
   - Identify biggest issues
   - Set improvement targets

5. **Integrate into CI/CD**
   - Run evaluations on every PR
   - Block merges if critical tests fail
   - Track metrics over time

---

## 📚 Additional Resources

- [Langfuse Multi-Agent Guide](https://langfuse.com/guides/cookbook/example_langgraph_agents)
- [Langfuse Evaluation Docs](https://langfuse.com/docs/evaluation)
- [LLM-as-a-Judge Guide](https://langfuse.com/blog/2025-09-05-automated-evaluations)
- [LangGraph + Langfuse Integration](https://langfuse.com/docs/integrations/langgraph)



