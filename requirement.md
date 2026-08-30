AgentCritiqueLoop

One-line:

A multi-agent validation loop where agents iteratively critique, refine, and validate each other's results until they reach agreement.

Objective

Given a task, two agents continuously review each other's work, identify gaps, refine the answer, and terminate when a defined consensus condition is met.

Core Requirements
Two or more configurable agents
Shared task/context
Independent initial solutions
Critique → Response → Refinement loop
Agents can use tools and MCPs
Structured critique:
Correctness
Missing information
Contradictions
Evidence
Confidence
Consensus mechanism
Configurable:
Maximum iterations
Agreement threshold
Timeout
Token budget
Final output only after:
Consensus achieved, or
Maximum iterations reached
Complete execution trace
Show:
Agent decision
Critique
Tool/MCP invocation
Evidence/result
Revision
Agreement state
Export trace as JSON/Markdown for learning and debugging
Pluggable evaluator
MVP Flow
                         Task
                          │
                ┌─────────┴─────────┐
                ▼                   ▼
             Agent A             Agent B
                │                   │
             Result A            Result B
                │                   │
                └─────────┬─────────┘
                          ▼
                     Critique
                          │
                    ┌─────┴─────┐
                    ▼           ▼
                Agent A       Agent B
                Refine         Refine
                    │           │
                    └─────┬─────┘
                          ▼
                    Agreement?
                    /       \
                  No         Yes
                  │           │
                  └── Loop    ▼
                         Final Result
                              +
                         Execution Trace