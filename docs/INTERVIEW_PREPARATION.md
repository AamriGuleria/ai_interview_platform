# AI-Powered Interview Platform: Interview Preparation Guide

This guide prepares you to explain the platform described on your resume using the implementation in this repository. Treat the sample answers as a foundation: phrase them naturally, and distinguish what the code does from design intentions or future improvements.

## 1. A concise project introduction

> I built an AI-powered mock-interview backend with FastAPI, PostgreSQL and pgvector. A candidate submits a resume and target role; the platform stores the PDF in MinIO and queues processing with Celery. A worker extracts and cleans the PDF text, uses Gemini 2.5 Flash to create a structured candidate profile, and creates two 384-dimensional embeddings with Sentence Transformers. The system retrieves relevant questions from PostgreSQL, reranks them using both role/retrieval and resume relevance, and personalizes selected questions with Llama 3.2. Candidate answers are evaluated asynchronously with Gemma 2 2B, and Llama 3.2 can generate follow-ups and an overall report. RabbitMQ is the Celery broker; Redis is the Celery result backend. The project also supports Whisper transcription and gTTS playback, plus JWT authentication with refresh sessions.

If asked for a result or benchmark, give a measured number only if you have actually measured it. The code shows the data flow and configured models; it does not establish a comparative model benchmark or production-scale latency.

## 2. Know the actual architecture

### End-to-end flow

1. **Create an interview:** an authenticated FastAPI endpoint receives the target role, experience, skills and resume PDF. The API stores the file in MinIO and creates an interview row in PostgreSQL.
2. **Parse and profile:** a Celery task downloads the PDF, extracts text with PyMuPDF, normalizes whitespace/control characters, and requests a structured profile from Gemini 2.5 Flash. Pydantic validates the returned `ResumeContext`.
3. **Embed:** the local Sentence Transformers model `all-MiniLM-L6-v2` encodes the resume summary and a separate retrieval summary into 384-element vectors. The temporary resume object is deleted after this processing path succeeds.
4. **Retrieve and rerank:** PostgreSQL/pgvector computes cosine distances between question embeddings and each of the two interview embeddings. The initial query orders by retrieval-context distance and takes up to 100 questions. A weighted score reranks them: 70% retrieval/role-context similarity and 30% resume similarity. The top 30 are retained.
5. **Personalize:** selected questions are saved. Eligible questions are sent in batches of five to Llama 3.2, which is prompted to preserve the original objective and difficulty and not invent candidate experience.
6. **Conduct the interview:** the API serves the next question in display order. For voice interaction, gTTS generates English audio and Faster-Whisper transcribes uploaded audio.
7. **Evaluate and report:** answer evaluation is queued. Gemma 2 2B returns a score, feedback, strengths, gaps and a follow-up recommendation. If the recommendation is true and the score is below the configured threshold (default 70), a Llama 3.2 follow-up may be created, subject to a per-interview cap (default three). Llama 3.2 also produces an overall report.

### Model and component map

| Component | Actual role in this repository | Interview-safe description |
|---|---|---|
| Gemini 2.5 Flash | Resume-profile extraction/context generation through LiteLLM; API key comes from configuration | External model API for extracting structured context from resume text |
| Qwen 2.5 3B | Configured Ollama model for question metadata enrichment | Used by the metadata-enrichment method; do not say it powers the main question-personalization path |
| Llama 3.2 | Ollama model for question personalization, follow-up generation and final interview evaluation | Local Ollama-served generation for these interview tasks |
| Gemma 2 2B | Ollama model for individual answer evaluation | Local Ollama-served scoring and feedback |
| `all-MiniLM-L6-v2` | Sentence Transformers model to embed question text and resume/retrieval summaries | Embedding model, distinct from the generative LLMs |
| PostgreSQL + pgvector | Relational application data and 384-dimensional vectors; cosine-distance queries | One database for transactional records and vector retrieval |
| RabbitMQ + Celery | Message broker and background task execution | Queues work so slow processing does not block the request/response path |
| Redis | Celery result backend, configured with a one-hour result expiry | Not the configured Celery broker in this project |

The `GEMINI_2_5` and Qwen/Llama/Gemma constants are not proof that every configured model is used on every request. In particular, Gemini 2.5 Flash is the resume-context model in the current path. The separate Gemini 2.5 constant is defined but is not used in the inspected service methods.

## 3. Project and architecture questions

### Q1. What problem does the platform solve?

**Answer:** It turns a resume and target role into a tailored mock interview. It first extracts candidate context, retrieves relevant questions from a curated question bank, and personalizes selected questions. It then evaluates submitted answers and provides feedback and an interview-level report. It combines ordinary API/database work with asynchronous AI and document-processing tasks.

**Why this answer works:** It explains the user value and how the main capabilities fit together without implying that an LLM generates the entire interview from scratch.

### Q2. Walk me through what happens after a candidate uploads a resume.

**Answer:** The FastAPI route delegates interview registration to the service. The resume is uploaded to MinIO and interview metadata is stored in PostgreSQL. The API then queues a Celery task. A worker downloads the PDF, extracts and cleans text, calls Gemini 2.5 Flash for structured context, validates that context with Pydantic, generates the two embeddings, and continues to interview question preparation. That preparation retrieves, reranks and saves questions, then personalizes eligible questions in batches.

**Follow-up detail:** Interview state is persisted, so the API can report preparation status instead of holding the upload request open while the model calls and retrieval run.

### Q3. Why FastAPI?

**Answer:** FastAPI gives the project typed request/response handling, dependency injection and convenient integration with async endpoints. I use dependencies for the database session and authenticated user. The API handles the request and authorization boundary, while Celery handles work that can take longer than a normal HTTP request.

Do not claim that every operation is non-blocking: parts of the service use synchronous database sessions and local speech/model work. Explain that async API support is useful, but blocking work still needs to be isolated or managed carefully.

### Q4. Why PostgreSQL and pgvector instead of a separate vector database?

**Answer:** The application already needs relational data such as users, interviews, questions and answers. pgvector lets it store and query embeddings alongside those records, reducing infrastructure and keeping retrieval results easy to associate with relational data. For the current question-bank scale described by the project, that is a practical architecture. If vector traffic or data scale outgrew PostgreSQL, I would benchmark indexes and query plans and compare dedicated vector infrastructure before migrating.

### Q5. What does Celery do here, and why not just use FastAPI `BackgroundTasks`?

**Answer:** Celery runs resume extraction, interview preparation, answer evaluation, follow-up generation and report preparation in worker processes. Those jobs include PDF processing, model/API calls and vector retrieval, so a durable external queue is more appropriate than tying the work to the API process. FastAPI `BackgroundTasks` is convenient for short, best-effort work that can run after a response, but it is not a substitute for a separately managed worker queue when work needs retries, independent scaling or queue-level operations.

The current Celery task configuration includes retry behavior, task time limits for resume extraction and interview preparation, late acknowledgements and a prefetch multiplier of one. These are implementation mechanisms, not a guarantee of exactly-once execution.

## 4. Embeddings, retrieval and RAG

### Q6. What is an embedding, and how does text become a vector?

**Answer:** An embedding model maps text to a fixed-length numeric vector. The model has learned to place texts with related meaning near one another in vector space. This platform uses `all-MiniLM-L6-v2` from Sentence Transformers. Its embeddings have 384 dimensions, matching the `Vector(384)` columns for questions and interview summaries. Each question is embedded from its question text; the resume and retrieval summaries are embedded separately.

The embedding model does not generate interview answers. It creates numeric representations used for retrieval.

### Q7. How is semantic search different from keyword search?

**Answer:** Keyword search looks for matching words or terms. Semantic search compares vector representations, so a question can be relevant even if its wording differs from the candidate context. For example, a resume discussing asynchronous job processing may be related to a question about background workers even if those exact phrases do not match.

Semantic search can also return an incorrect-but-nearby result, so it should be evaluated and combined with metadata, filters or reranking as needed. The platform stores skills and question metadata as well as embeddings, though the active candidate selection path I reviewed primarily uses vector retrieval followed by similarity reranking.

### Q8. Explain cosine similarity and cosine distance in this project.

**Answer:** Cosine similarity measures the angle between two vectors: a larger value means their directions are more alike. The SQLAlchemy pgvector expression used here is cosine **distance**. The code converts the result to a similarity-like value with `1 - distance`, stores both, and ranks by the resulting similarity. The initial query orders by the retrieval-context cosine distance, so nearer retrieval vectors come first.

Keep the distinction clear: the database query orders by distance ascending; the subsequent reranker sorts the weighted similarity score descending.

### Q9. What is the retrieval and reranking formula?

**Answer:** The system compares each question vector to two interview vectors: one based on the resume summary and another based on the retrieval summary, which contains retrieval/role context. It initially retrieves up to 100 questions ordered by retrieval-context distance. It then calculates:

```text
final_score = 0.70 * retrieval_similarity + 0.30 * resume_similarity
```

The top 30 questions after reranking are saved for that interview. That gives more weight to target-role/retrieval relevance while still accounting for the candidate's resume. The weights are configured in the call, not demonstrated by a measured offline optimization.

### Q10. Is this RAG?

**Answer:** It is a retrieval-augmented interview-generation workflow and is RAG-like: the system retrieves relevant question records and supplies candidate context to an LLM when personalizing questions. I would be precise rather than claiming every generation step is grounded by a full document-retrieval pipeline. The implementation retrieves from a question bank; the personalization prompt uses the structured resume context and original question. I do not see source citations or a formal grounding/evaluation layer in this path.

### Q11. How would you evaluate retrieval quality?

**Answer:** I would create a representative labeled set of resume/role contexts and questions judged relevant by a human reviewer. Then I would measure ranking metrics such as Precision@k, Recall@k, MRR or nDCG@k, inspect misses by role and question type, and compare embedding/model/weight choices on the same holdout set. I would also track downstream signals such as question usefulness and candidate feedback. In an interview, be clear that these are evaluation methods I would use; the code reviewed does not include an offline benchmark report.

### Q12. How do you reduce hallucinations?

**Answer:** The system gives the model a structured candidate profile and explicit instructions not to invent projects, companies, skills or experience. It asks models to preserve the original question's objective and difficulty. Pydantic schemas validate expected output fields, and the parser handles common JSON formatting problems before validation. These measures improve consistency, but they do not prove factual correctness. I would still validate outputs and monitor failures, and I would not present generated claims as verified resume facts.

### Q13. How do chunking and token limits apply?

**Answer:** The current resume path extracts a PDF's page text and sends cleaned text in the resume-analysis prompt; it does not show a chunk-and-embed pipeline for each resume page. The platform embeds summaries rather than the entire resume as independent chunks. This keeps the retrieval representation compact, but long resumes can still exceed an LLM's context limit. If that becomes an issue, I would introduce section-aware chunking or a bounded extraction/summarization step, preserve provenance, and test that important skills and projects are not lost.

Avoid saying the project implements chunking unless you add and verify that behavior.

## 5. LLMs and structured outputs

### Q14. Where did you use Gemini, Llama and Qwen?

**Answer:** Gemini 2.5 Flash extracts the structured profile and summaries from resume text through the configured Gemini API key and LiteLLM. Llama 3.2 is served through Ollama and handles selected question personalization, follow-up question generation and the overall interview report. Qwen 2.5 3B is also configured through Ollama and is used for question metadata enrichment. Individual answer evaluation currently uses Gemma 2 2B through Ollama.

This mapping is more accurate than saying all three models are interchangeable or that Qwen powers the primary interview flow.

### Q15. Were the models local or accessed through APIs?

**Answer:** The Gemini resume-analysis call is routed to the external Gemini service using an API key. The Ollama model identifiers for Qwen, Llama and Gemma indicate locally served models. Sentence Transformers loads `all-MiniLM-L6-v2` in the application process for embedding. This means the project combines hosted generation with local model serving and local embeddings; exact deployment placement depends on how the application and Ollama are deployed.

### Q16. Why use different models for different tasks?

**Answer:** The implementation assigns a model by task: resume understanding uses Gemini 2.5 Flash, answer scoring uses Gemma 2 2B, and personalization/follow-ups/final reports use Llama 3.2. Smaller locally served models can be practical for frequent or narrower tasks, while a hosted model can handle resume extraction. The code demonstrates this routing, but it does not contain a controlled quality, latency or cost comparison. I would describe model choice as an architectural assignment, not claim a benchmark result.

### Q17. How do you handle malformed or inconsistent JSON?

**Answer:** The service strips common Markdown code fences, normalizes typographic quotes and dashes, and first attempts normal JSON parsing. If that fails, it tries escaping control characters inside strings and then extracting a JSON object or array from surrounding text. The resulting dictionary is validated against Pydantic models such as `ResumeContext`, `PersonalizedQuestionBatch` or `EvaluationResult`. Errors are surfaced as runtime errors and logged rather than treating arbitrary text as a valid schema.

**Caveat:** This is defensive parsing, not a guarantee that every malformed response can be repaired. A schema validation failure should remain a failure rather than silently accepting incomplete output.

### Q18. What happens on rate limits or API failures?

**Answer:** A failure in resume-context generation raises an error from the service and the Celery resume task is configured for up to three retries with a 60-second delay; after retries are exhausted it publishes failure information to the dead-letter exchange. Other tasks have their own configured retry behavior. I would not claim a universal rate-limit policy or provider failover: I do not see a shared exponential backoff, provider fallback or explicit rate-limit-specific handling in the LLM service. Those would be worthwhile improvements, along with retrying only transient errors and making task effects idempotent.

### Q19. What is the difference between a language model and an embedding model?

**Answer:** A language model generates or evaluates text based on prompts. Gemini, Llama, Qwen and Gemma are used for those generative tasks here. An embedding model converts text to a numerical vector for similarity search. `all-MiniLM-L6-v2` performs that vectorization. They solve related but different problems and should not be conflated.

## 6. Celery, RabbitMQ and Redis

### Q20. Explain the producer, broker, worker and result backend in your setup.

**Answer:** The FastAPI/application code is the producer when it enqueues a Celery task. RabbitMQ is the AMQP broker: it accepts and routes task messages to the configured interview queue. Celery workers consume those messages and execute Python task functions. Redis is configured as the Celery result backend, where task results/status can be stored temporarily; results expire after one hour.

**Important correction:** The resume phrase “Celery and Redis” is broadly true in the architecture, but Redis is not the configured broker. If asked directly, say RabbitMQ is the broker and Redis is the result backend.

### Q21. How does Redis differ from PostgreSQL here?

**Answer:** PostgreSQL is the durable relational source of truth for application entities, interview state, answers, question metadata and pgvector embeddings. Redis is configured as a fast Celery result backend for task results with a one-hour expiry. RabbitMQ is the message broker. These components are not substitutes for one another: one stores relational application records, one transports task messages, and one stores transient task results.

### Q22. What happens if a worker crashes?

**Answer:** The Celery configuration uses late acknowledgements, so a task is acknowledged after execution rather than immediately on receipt; prefetch is set to one. This helps avoid acknowledging work before it has completed, but it does not provide exactly-once execution. A task may be redelivered, so side effects must be idempotent. Some tasks have retry policies and the resume/interview preparation paths publish a message to a dead-letter exchange after retry exhaustion. I would monitor queue depth, failures and worker health, and ensure duplicate task delivery cannot create duplicate interview questions or reports.

### Q23. What is task idempotency, and where does it matter?

**Answer:** An idempotent task can run more than once and produce the same final state without duplicate side effects. It matters because Celery retries and message redelivery can re-run work. For example, follow-up generation checks whether a follow-up already exists and applies a per-interview limit. Similar safeguards should exist around question creation, embedding generation and report preparation. I would check the database state before creating records and use unique constraints or transaction boundaries where appropriate.

## 7. Authentication and data security

### Q24. Explain JWT structure, access tokens and refresh tokens.

**Answer:** A JWT consists of a header, payload and signature. This project signs tokens with HS256. Access tokens are configured to expire after 15 minutes; refresh tokens after 30 days. The payload includes a subject and token type, and the access token also includes email and role. The refresh token is associated with an application session whose stored token hash can be checked and revoked. The refresh endpoint verifies the refresh token type, user, matching session, revocation state and expiry before issuing a new access token.

JWT payloads are signed, not encrypted; sensitive information should not be placed in them.

### Q25. How are passwords stored?

**Answer:** Passwords are not stored in plaintext. The project uses Passlib's `CryptContext` configured for Argon2 and bcrypt, with Argon2 preferred and bcrypt retained for compatibility. Password verification checks a submitted password against the stored password hash. Hashing is one-way, unlike encryption, which is designed to be reversible with a key.

### Q26. How does FastAPI authentication work in this project?

**Answer:** `HTTPBearer` extracts the bearer credential, and `Depends` wires authentication and the async database session into route handlers. The dependency decodes the token, reads the user ID from its subject, loads the user and returns that user to downstream code. Interview routes use that dependency to identify the current user, and several interview lookups scope the interview to that user's ID.

**Be precise about authorization:** The token contains a role and the schema defines admin, recruiter and candidate roles, but the reviewed dependency primarily authenticates a user; I did not find a general role-enforcement dependency on the interview routes. Do not claim comprehensive role-based access control unless you can point to the actual route-level enforcement.

### Q27. How are uploaded resumes protected?

**Answer:** Resume files are stored in MinIO under a path that includes the user ID and a UUID, and the resume-processing task downloads the object for parsing and deletes it after successful processing. The MinIO helper can generate a presigned URL, but the reviewed upload/processing path uses direct object operations rather than returning a presigned URL to the client.

**Important limitation:** I do not see explicit file extension/MIME verification, maximum upload-size enforcement or malware scanning in the reviewed upload path. I would not claim those controls are implemented. They are important hardening steps before production use.

## 8. Speech and voice interaction

### Q28. How do speech-to-text and text-to-speech work?

**Answer:** For playback, the service selects the next unanswered question and uses gTTS with English (`en`) to create an MP3 response. For transcription, it writes the uploaded audio to a temporary file and uses Faster-Whisper's `base` model on CPU with `int8` compute and beam size five. The endpoint returns recognized text, detected language and audio duration. Temporary files are removed after processing.

### Q29. What would you consider for audio validation and latency?

**Answer:** Audio processing is potentially slow and resource-intensive, particularly on CPU. I would enforce upload size and supported-format/duration limits, avoid trusting the client-provided content type, and return clear errors for invalid or empty audio. For long recordings, I would queue transcription and expose a processing status. I would monitor transcription latency and CPU/memory usage and choose model size based on measured quality/latency requirements.

Do not claim the existing route implements all these validations: the inspected transcription method reads the full upload into a temporary `.wav` path and calls Whisper, but does not show explicit size or format checks.

## 9. Testing and engineering practices

### Q30. What tests did you write?

**Answer:** I wrote focused pytest unit tests for pure decision/cleanup logic. The resume-text tests cover whitespace normalization, removal of control characters and empty input. The follow-up decision test is parametrized across scores and the model's follow-up recommendation, including the configured score threshold behavior. There is also a parametrized test for the question-personalization decision.

**Be accurate about scope:** These tests verify helper logic; they are not end-to-end tests of PostgreSQL, RabbitMQ, Redis, MinIO, model APIs or the full interview workflow. A next step would be integration tests with mocked model/storage boundaries and a small set of end-to-end workflow tests.

### Q31. How would you improve the platform next?

**Answer:** I would prioritize observability and reliability around the asynchronous workflow: structured task logs and correlation IDs, queue/retry/dead-letter monitoring, idempotency tests, and clear user-facing failure states. For AI quality, I would build a labeled retrieval evaluation set and model-quality/latency/cost measurements rather than rely on anecdotes. For security, I would add strict resume/audio type and size validation, stronger role authorization, and a documented data-retention policy. I would also test under realistic concurrent load and inspect PostgreSQL query plans before deciding whether vector indexing or another retrieval service is warranted.

## 10. Claims to phrase carefully

- **“600+ questions”:** The resume states this. The repository contains datasets named `enriched_500_qa.csv` and `enriched_hundred_qa.csv`; be ready to explain whether they are both ingested and how duplicates or missing rows are counted. Do not equate filenames with a verified production row count.
- **“Weighted reranking”:** This is supported by the implementation. Quote the configured 70% retrieval-context and 30% resume-similarity weights; do not claim the weights were empirically optimized unless you have the evaluation evidence.
- **“Celery and Redis”:** Explain the actual topology: Celery + RabbitMQ broker + Redis result backend.
- **“Multiple LLMs”:** Give the task-to-model mapping above. Do not imply all models run locally; Gemini is API-routed and the Ollama models are locally served.
- **“RAG”:** Describe the retrieval-augmented workflow precisely. The code does not show citations or a formal grounding-quality test suite.
- **“Secure file handling / RBAC”:** Explain the controls that exist and acknowledge missing upload validation and incomplete visible route-level role checks.
- **“Speech processing”:** Whisper transcription and gTTS playback are implemented; do not imply robust audio-format/size validation without separate evidence.
- **“Model comparisons”:** The source configures model choices but contains no controlled comparison proving which model is more accurate, faster or cheaper.
- **“Fine-tuning”:** There is no evidence here that any model was fine-tuned.

## 11. Short revision checklist

Before an interview, rehearse these points aloud:

1. Draw the request → MinIO/PostgreSQL → Celery/RabbitMQ → resume extraction → embeddings → pgvector retrieval → reranking → personalization → answer evaluation flow.
2. Memorize the exact role of Gemini, Qwen, Llama, Gemma and MiniLM.
3. Explain cosine **distance** versus similarity and the 70/30 reranking weights.
4. Say “RabbitMQ broker, Redis result backend” without hesitation.
5. Know the access/refresh expiry values and how session refresh-token hashes are used.
6. State what the tests cover and what they do not.
7. When discussing limitations, propose a measurable next step rather than overclaiming a control or benchmark.

## 12. Source files to revisit

- [Interview API routes](../src/apis/v1/interview.py)
- [Interview service and speech flow](../src/crud/interview.py)
- [Resume extraction task](../src/background_tasks/resume_text_extraction.py)
- [Question retrieval and reranking](../src/services/embeddings.py)
- [LLM model routing and output parsing](../src/services/llm_service.py)
- [Interview preparation task](../src/background_tasks/prepare_interview.py)
- [Answer evaluation and follow-ups](../src/background_tasks/evaluate_answers.py)
- [Celery broker/backend configuration](../src/services/celery_app.py)
- [JWT and password hashing](../src/utils/jwt.py) and [password utilities](../src/utils/security.py)
- [Focused tests](../src/tests)
