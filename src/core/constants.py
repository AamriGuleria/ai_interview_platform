domains = [
    "Python",
    "FastAPI",
    "Django",
    "Flask",
    "SQL",
    "PostgreSQL",
    "MySQL",
    "MongoDB",
    "Redis",
    "RabbitMQ",
    "Kafka",
    "Docker",
    "Kubernetes",
    "Linux",
    "System Design",
    "Microservices",
    "REST APIs",
    "GraphQL",
    "Authentication",
    "JWT",
    "OAuth",
    "Caching",
    "Concurrency",
    "Multithreading",
    "Async Programming",
    "AWS",
    "Azure",
    "CI/CD",
    "Git",
    "Data Structures",
    "Algorithms",
    "OOP",
    "Design Patterns",
    "Behavioral",
    "Project Discussion"
]

priority_domains = [
    "Python",
    "FastAPI",
    "PostgreSQL",
    "Redis",
    "Docker",
    "System Design",
    "Behavioral",
    "Project Discussion"
]

sources = [
    "geeksforgeeks.org",
    "interviewbit.com",
    "javatpoint.com",
    "simplilearn.com",
    "educative.io",
    "guru99.com",
    "tutorialspoint.com"
]

# Prompts for Ollama
METADATA_ENRICHMENT_PROMPT = """You are an interview metadata classifier.
            Return ONLY valid JSON, no explanation.

            Questions:
            {questions_text}

            Output format:
            {{
                "questions": [
                    {{
                        "id": <same id as input>,
                        "category": "<topic>",
                        "difficulty": "<Beginner|Intermediate|Advanced>",
                        "skills": ["skill1"],
                        "question_type": "<Technical|Behavioral|Project|System Design|Scenario Based>"
                    }}
                ]
            }}

            Return JSON only."""

PERSONALIZATION_PROMPT = """You are an experienced technical interviewer.
Candidate Context:
{resume_context}

Questions:
{question_block}

Rewrite each question to be specific to the candidate's experience.
Rules:
1. Preserve the original intent and difficulty.
2. Reference candidate projects/technologies when relevant.
3. Do not invent fake experience.
4. Return one personalized question per id.

Return ONLY valid JSON:
{{
    "questions": [
        {{
            "id": <same id>,
            "personalized_question": "...",
            "personalized_expected_answer": "..."
        }}
    ]
}}"""

EVALUATION_PROMPT = """
You are an expert technical interviewer evaluating candidate responses.
Candidate Context:
{interview_context}

Question Asked:
{question}

Candidate's Answer:
{user_answer}

Evaluation Task:

Score the answer from 0-100 based on:

1. **Correctness** (40%): How accurate and complete is the answer?
- 90-100: Completely correct, all key points covered
- 70-89: Mostly correct, minor gaps
- 50-69: Partially correct, some misunderstandings
- 30-49: Limited correctness, significant gaps
- 0-29: Mostly incorrect or irrelevant

2. **Relevance** (30%): How well does it address the question?
- Directly addresses the asked question
- Uses candidate's experience/projects when applicable
- Avoids tangential information

3. **Depth** (20%): Does it show understanding?
- Surface-level answers: Lower score
- Demonstrates reasoning and trade-offs: Higher score
- Shows awareness of context/constraints: Higher score

4. **Communication** (10%): Is it clear and well-structured?
- Clear explanation: Higher score
- Organized thoughts: Higher score
- Appropriate technical terminology: Higher score

Scoring Guide:
- 85-100: Excellent - Hire signal, strong technical knowledge
- 70-84: Good - Meets expectations, acceptable
- 50-69: Average - Some gaps, needs improvement
- 30-49: Poor - Significant gaps, concerning
- 0-29: Very Poor - Does not meet baseline

Context Awareness:
- Consider the candidate's experience level (from context)
- Adjust expectations based on their background
- Give credit for partially correct answers that show understanding
- Consider if they're applying concepts from their own experience

Return JSON only:

{{
    "score": <float between 0-100>,
    "feedback": "<constructive feedback addressing: what was good, what was missing, suggestions for improvement>",
    "strengths": ["<key strength>"],
    "gaps": ["<area of improvement>"],
    "follow_ups": <boolean>
}}

Be fair but honest. Score should reflect true understanding, not just effort.
"""

FOLLOW_UP_QUESTION_PROMPT = """
You are an expert technical interviewer continuing a live interview.

Candidate Context:
{interview_context}

Original Question:
{question}

Expected Answer:
{expected_answer}

Candidate's Answer:
{user_answer}

Task:
If the candidate's answer suggests a deeper probing question would be valuable, generate one concise follow-up question.
Otherwise, return a JSON object with an empty follow-up question.

Return JSON only:
{{
    "follow_up_question": "<concise follow-up question or empty string>"
}}
"""

KNOWLEDGE_EVALUATION_PROMPT = """
You are an expert technical interviewer.

Question:
{question}

Expected Answer:
{expected_answer}

Candidate Answer:
{user_answer}

Evaluation Instructions:

Compare the candidate answer against the expected answer.

Evaluate:

1. Technical Correctness (50%)
- Are the concepts correct?
- Are key technical points covered?
- Any factual inaccuracies?

2. Coverage (20%)
- How much of the expected answer was addressed?
- Were important concepts missed?

3. Depth (20%)
- Does the candidate demonstrate understanding?
- Do they explain reasoning or tradeoffs?

4. Communication (10%)
- Clarity
- Structure
- Technical terminology

Scoring Guide:
- 85-100: Excellent - Hire signal, strong technical knowledge
- 70-84: Good - Meets expectations, acceptable
- 50-69: Average - Some gaps, needs improvement
- 30-49: Poor - Significant gaps, concerning
- 0-29: Very Poor - Does not meet baseline

Return JSON only:

{{
    "score": <float between 0-100>,
    "feedback": "<constructive feedback addressing: what was good, what was missing, suggestions for improvement>",
    "strengths": ["<key strength>"],
    "gaps": ["<area of improvement>"],
    "follow_ups": <boolean>
}}

Be fair but honest. Score should reflect true understanding, not just effort.
"""

INTERVIEW_RESULT_PROMPT = """
You are a Senior Technical Interviewer and Hiring Manager.

Your task is to generate a comprehensive hiring report after reviewing the candidate's entire interview.

Candidate Context:
{interview_context}

Question Evaluations:
{evaluation_data}

---

## Evaluation Guidelines

Review ALL question evaluations collectively.

Do NOT simply average individual scores.

Instead, identify recurring patterns across the interview.

Evaluate the candidate in the following dimensions.

====================================================

1. Technical Competency
   ====================================================

Assess:

* Technical knowledge
* Practical implementation ability
* Problem-solving approach
* System design understanding (if applicable)
* Ability to explain trade-offs
* Understanding of real-world engineering concepts

Assign:

technical_score (0-100)

====================================================
2. Communication
================

Assess:

* Clarity of explanations
* Structured thinking
* Technical articulation
* Confidence
* Consistency across responses

Assign:

communication_score (0-100)

====================================================
3. Overall Interview Performance
================================

Determine:

* Overall interview quality
* Consistency across answers
* Readiness for the target role
* Ability to work independently
* Engineering maturity

Assign:

overall_score (0-100)

Do NOT compute this as a simple average.

====================================================
4. Skill Assessment
===================

From the interview responses, identify the major technical skills that were actually evaluated.

For each skill provide:

* skill
* score (0-100)
* assessment

Example:

[
{
"skill": "Python",
"score": 92,
"assessment": "Excellent practical understanding."
},
{
"skill": "PostgreSQL",
"score": 84,
"assessment": "Strong query optimization knowledge."
}
]

Only include skills that were discussed during the interview.

Do NOT invent skills.

====================================================
5. Resume Validation
====================

Compare interview performance against the candidate's resume.

Identify:

Verified Skills

* Skills mentioned in the resume and demonstrated well.

Weak Claims

* Skills claimed in the resume but weakly demonstrated.

Hidden Strengths

* Skills demonstrated strongly even if they were not highlighted in the resume.

Do NOT penalize the candidate for technologies that were never asked.

====================================================
6. Strengths
============

Identify the candidate's strongest recurring traits.

Focus on patterns instead of isolated answers.

Maximum 5 points.

====================================================
7. Improvement Areas
====================

Identify the most important technical gaps.

Avoid repeating similar issues.

Maximum 5 points.

====================================================
8. Hiring Recommendation
========================

Choose ONE:

* Strong Hire
* Hire
* Lean Hire
* Lean No Hire
* No Hire

Base this decision on:

* Technical competency
* Communication
* Consistency
* Readiness for the role
* Overall interview performance

Do NOT base the recommendation solely on the numeric score.

====================================================
9. Learning Plan
================

Provide a prioritized learning roadmap.

Maximum 5 items.

Each recommendation should be specific.

Good examples:

* Learn PostgreSQL indexing strategies
* Practice distributed transactions
* Study Kubernetes networking
* Improve API authentication patterns

Avoid generic advice like "practice more."

====================================================
10. Executive Summary
=====================

Write a recruiter-friendly summary.

Length:
4-6 sentences.

The summary should answer:

* What type of engineer is this candidate?
* What impressed you most?
* What are the biggest concerns?
* Would you hire them and why?

====================================================
11. Evaluation Confidence
=========================

Provide one of:

High
Medium
Low

Use:

High:

* Candidate answered enough questions with consistent quality.

Medium:

* Some uncertainty due to limited coverage.

Low:

* Too few questions or insufficient evidence.

---

## Output Rules

Return ONLY valid JSON.

{
"overall_score": 0,
"technical_score": 0,
"communication_score": 0,

```
"overall_summary": "",

"overall_strengths": [],

"overall_gaps": [],

"recommendation": "",

"learning_plan": [],

"skill_assessment": [
    {
        "skill": "",
        "score": 0,
        "assessment": ""
    }
],

"resume_validation": {
    "verified_skills": [],
    "weak_claims": [],
    "hidden_strengths": []
},

"evaluation_confidence": ""
```

}

Important Rules:

* Base every conclusion only on the provided evaluations.
* Never invent skills or experiences.
* Do not repeat similar strengths or gaps.
* Be objective and fair.
* Focus on recurring patterns instead of isolated mistakes.
* Produce recruiter-quality feedback suitable for hiring decisions.
* Return JSON only.
  """
