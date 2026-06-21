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
    "gaps": ["<area of improvement>"]
}}

Be fair but honest. Score should reflect true understanding, not just effort.
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
    "gaps": ["<area of improvement>"]
}}

Be fair but honest. Score should reflect true understanding, not just effort.
"""