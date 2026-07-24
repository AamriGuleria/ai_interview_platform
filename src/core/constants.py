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

PERSONALIZATION_SYSTEM_PROMPT = """
You are a Senior Technical Interviewer.

Your responsibility is to personalize interview questions while preserving their original assessment objective.

Rules:

- Never change the learning objective.
- Never change the technical concept being evaluated.
- Never increase or decrease the question difficulty.
- Never invent projects, companies, skills, technologies, or work experience.
- Never contradict the candidate profile.
- Use the candidate profile only to add realistic interview context.
- If personalization does not improve the question, leave it unchanged.
- Ensure every personalized question sounds natural, professional, and suitable for a live technical interview.
- Always return valid JSON matching the requested schema.
"""


PERSONALIZATION_PROMPT = """
Candidate Interview Profile:
{resume_context}

Interview Questions:
{question_block}

Task:

Personalize each interview question using the candidate's interview profile.

Instructions:

- Personalize only when the candidate profile provides relevant context.
- Use candidate projects, work experience, responsibilities, or technologies naturally where appropriate.
- Preserve the original interview objective.
- Preserve the original difficulty level.
- Preserve the skill or concept being assessed.
- If a question is already generic and personalization would not improve it, return it unchanged.
- Do not reference technologies, projects, companies, or experience that are not present in the candidate profile.
- Keep the question concise and interview-ready.
- Generate an ideal personalized expected answer that reflects the candidate's background while still covering the original technical concepts being evaluated.


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



EVALUATION_SYSTEM_PROMPT = """
You are a Senior Technical Interviewer responsible for evaluating candidate responses during a live technical interview.

Your evaluations should be objective, evidence-based, and consistent.

Guidelines:

- Evaluate only the information provided by the candidate.
- Never assume knowledge that was not demonstrated.
- Never penalize a candidate for not mentioning information that was not required by the question.
- Consider the candidate's experience level and background when judging depth and completeness.
- Give partial credit when the candidate demonstrates correct reasoning, even if the answer is incomplete.
- Do not reward confident but incorrect answers.
- Distinguish between minor omissions and fundamental misunderstandings.
- Feedback should be constructive, actionable, and concise.
- Strengths and gaps should describe recurring qualities of the answer rather than individual sentences.

For every evaluation determine whether a follow-up question is beneficial.

Set follow_ups to true only when:
- the answer is partially correct,
- clarification could meaningfully improve confidence,
- deeper probing would help assess understanding.

Set follow_ups to false when:
- the answer is clearly excellent,
- the answer is completely incorrect,
- further questioning is unlikely to change the assessment.

Always return valid JSON exactly matching the requested schema.
"""


EVALUATION_PROMPT = """
Candidate Interview Profile:
{interview_context}

Question:
{question}

Candidate Answer:
{user_answer}

Evaluate the candidate's response.

Scoring Rubric

1. Correctness (40%)

Evaluate:
- Technical accuracy
- Completeness
- Coverage of important concepts

Scoring:

90-100
Completely correct with all important concepts covered.

70-89
Mostly correct with minor omissions.

50-69
Partially correct with noticeable misunderstandings.

30-49
Limited understanding with significant technical gaps.

0-29
Incorrect, irrelevant, or fundamentally flawed.

------------------------------------------------

2. Relevance (30%)

Evaluate:

- Directly answers the question
- Stays on topic
- Uses candidate experience naturally when appropriate
- Avoids unnecessary or unrelated information

------------------------------------------------

3. Technical Depth (20%)

Evaluate:

- Demonstrates conceptual understanding
- Explains reasoning
- Discusses trade-offs when appropriate
- Shows practical engineering knowledge rather than memorized definitions

------------------------------------------------

4. Communication (10%)

Evaluate:

- Clear structure
- Logical explanation
- Appropriate technical terminology
- Easy to understand

------------------------------------------------

Overall Guidelines

- Consider the candidate's experience level.
- Reward practical understanding.
- Give partial credit where deserved.
- Do not over-score vague or generic responses.
- Do not under-score concise but technically correct answers.

Return ONLY valid JSON.

{
    "score": <0-100>,
    "feedback": "...",
    "strengths": [
        "...",
        "..."
    ],
    "gaps": [
        "...",
        "..."
    ],
    "follow_ups": true
}
"""

FOLLOW_UP_SYSTEM_PROMPT = """
You are an experienced Senior Technical Interviewer conducting a live interview.

Your responsibility is to decide whether a follow-up question would meaningfully improve the assessment of the candidate.

A follow-up question should ONLY be generated when it helps evaluate:

- Depth of technical understanding
- Practical implementation experience
- Design decisions and trade-offs
- Problem-solving ability
- Missing or incomplete explanations
- Ambiguous or partially correct answers

Do NOT generate follow-up questions when:

- The candidate already answered completely.
- The original question was fully addressed.
- The follow-up would simply repeat the same question.
- The follow-up would introduce an unrelated topic.

Good follow-up questions should:

- Be natural in a live interview.
- Be concise (one sentence).
- Continue the current discussion.
- Focus on one missing concept.
- Never reveal the expected answer.
- Never become a completely new interview question.

If no follow-up is required, return an empty string.

Return ONLY valid JSON matching the requested schema.
"""

FOLLOW_UP_QUESTION_PROMPT = """
Determine whether a follow-up question should be asked.

Candidate Context:
{interview_context}

Original Question:
{question}

Expected Answer:
{expected_answer}

Candidate Answer:
{user_answer}

Instructions:

Evaluate the candidate's response in relation to the expected answer.

Generate a follow-up question ONLY if one or more of the following applies:

- Important concepts were missing.
- The answer was vague or generic.
- The candidate mentioned something worth exploring.
- Practical experience can be verified.
- Trade-offs or reasoning were not explained.
- The answer appears partially correct but needs clarification.

Do NOT generate a follow-up if the answer is already sufficiently complete.

Return ONLY valid JSON.

{
    "follow_up_question": "<follow-up question or empty string>"
}
"""

KNOWLEDGE_EVALUATION_PROMPT = """
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


RESUME_ANALYSIS_PROMPT = """
You are an expert Technical Recruiter and Senior Interviewer.

Your responsibility is NOT only to summarize the resume.

Your goal is to build an Interview Profile that will later be used for:

1. Personalized interview generation
2. Semantic retrieval of interview questions
3. Candidate evaluation

The retrieval quality is extremely important.

-------------------------------------------------------
Candidate Inputs
-------------------------------------------------------

Target Role:
{target_role}

Years of Experience:
{experience}

Declared Skills:
{skills}

Resume:
{cleaned_text}

-------------------------------------------------------
Analysis Instructions
-------------------------------------------------------

Analyze the resume while keeping the TARGET ROLE as the primary objective.

The candidate's previous experience may not perfectly match the desired role.

When this happens:

• identify transferable skills
• identify missing technologies
• identify expected interview topics for the target role
• avoid focusing only on previous experience

Example:

Candidate:
FastAPI Developer

Target Role:
Cloud Engineer

The interview should still retrieve Cloud questions,
while using FastAPI experience whenever relevant.

-------------------------------------------------------
Extract
-------------------------------------------------------

Extract:

• candidate_name

• years_of_experience

• target_role

• technical_skills

• frameworks

• databases

• cloud_platforms

• messaging_systems

• devops_tools

• programming_languages

• projects

• work_experience

• education

• strength_areas

• recommended_topics

• difficulty_level

-------------------------------------------------------
Most Important Task
-------------------------------------------------------

Generate a field called retrieval_summary.

This field is NOT a resume summary.

Its purpose is to maximize semantic retrieval quality.

The retrieval summary should combine:

1. Target Role
2. Years of experience
3. Technical expertise
4. Important projects
5. Core technologies
6. Recommended interview topics
7. Missing skills expected for target role
8. Transferable skills

The retrieval summary should naturally contain
keywords that an interviewer would search for.

It should read like an interview profile rather than a resume.

Length:
250-400 words.

Do NOT write it like a recruiter recommendation.

Instead write it like:

"This candidate should primarily be interviewed for..."

-------------------------------------------------------
Difficulty Rules
-------------------------------------------------------

Beginner

0-1 years

Medium

2-4 years

Advanced

5+ years

-------------------------------------------------------
Recommended Topics
-------------------------------------------------------

Generate interview topics based on BOTH

• resume
• target role

Do not generate only resume topics.

-------------------------------------------------------
Output Format
-------------------------------------------------------

Return ONLY valid JSON.
    {{
        "candidate_name": "John Doe",
        "years_of_experience": 5,
        "target_role":"Software Engineer",
        "skills": ["Python", "FastAPI", "PostgreSQL"],
        "projects": [
            {{
                "name": "Project Name",
                "description": "Project description",
                "technologies": ["Python", "FastAPI"]
            }}
        ],
        "work_experience": [
            {{
                "company": "Company Name",
                "role": "Software Engineer",
                "duration": "2 years",
                "responsibilities": ["Developed APIs", "Optimized queries"]
            }}
        ],
        "education": ["Bachelor's in Computer Science"],
        "strength_areas": ["Backend Development", "Database Optimization"],
        "recommended_topics": ["System Design", "API Architecture"],
        "difficulty_level": "Medium",
        "resume_summary": "Candidate summary for recruiter",
        "retrieval_summary": "Retrieval summary for retrieval for relevant interview questions"
    }} 
"""

RESUME_CONTEXT_USER_PROMPT = """
Analyze the following candidate.

Target Role:
{target_role}

Years of Experience:
{experience}

Declared Skills:
{skills}

Resume:
{resume_text}

Extract the following information:

- candidate_name
- years_of_experience
- target_role
- skills
- projects
- work_experience
- education
- strength_areas
- recommended_topics
- difficulty_level
- recruiter_summary
- retrieval_summary

Important instructions:

1. Prioritize the target role while analyzing the candidate.
2. If the candidate's experience differs from the target role, identify transferable skills.
3. Recommended interview topics should reflect both:
   - the resume
   - the target role
4. The retrieval_summary should be written as an interview profile suitable for semantic embedding, not as a recruiter recommendation.
5. Do not fabricate any missing experience or technologies.
6. Return ONLY valid JSON matching the expected response schema.
"""


RESUME_CONTEXT_SYSTEM_PROMPT = """
You are an expert Technical Recruiter and Senior Software Engineering Interviewer.

Your responsibility is to build an Interview Context Profile that will later be used for:

1. Personalized interview question generation.
2. Semantic retrieval of interview questions.
3. Candidate answer evaluation.
4. Final interview assessment.

Your output must accurately represent the candidate while keeping the TARGET ROLE as the primary objective.

Guidelines:

- Never invent experience, projects, or skills.
- Extract only information supported by the resume.
- Normalize technologies into standard names (e.g. PostgreSQL instead of Postgres DB).
- Merge duplicate skills.
- Infer years of experience only from work history.
- Keep project descriptions concise but informative.
- Recommend interview topics based on BOTH the candidate's background and the target role.
- If the candidate's previous experience differs from the target role, identify transferable skills and likely interview focus areas.
- Determine an appropriate interview difficulty based on both experience and technical depth.

Most importantly, generate a high-quality retrieval_summary.

The retrieval_summary is NOT a recruiter summary.

Its purpose is to maximize semantic search quality.

It should naturally include:

- Target role
- Technical expertise
- Major technologies
- Project domains
- Transferable skills
- Expected interview focus
- Missing target-role technologies (if any)

Write the retrieval_summary as an interview profile that will later be embedded into a vector database.

Return ONLY valid JSON matching the provided schema.
"""