# AI Interview Platform - Architecture, RAG, and Retrieval Concepts

This document explains the architecture of the AI Interview Platform and the core retrieval concepts behind it, including embeddings, cosine similarity, pgvector, semantic search, RAG, and async processing.

---

## 1. Project Overview

The AI Interview Platform is an intelligent mock interview system that helps candidates practice technical interviews.

The platform works in the following flow:

1. A candidate uploads a resume.
2. The system extracts and cleans the resume text.
3. An LLM analyzes the resume and creates a structured candidate profile.
4. The resume context and interview questions are converted into embeddings.
5. The system retrieves semantically relevant questions using similarity search.
6. Relevant questions are personalized based on the candidate profile.
7. Answers are evaluated using an LLM-based workflow.

The main implementation is organized around FastAPI APIs, SQLAlchemy models, background workers, and AI services.

---

## 2. Architecture

The project uses a layered architecture:

- API layer: FastAPI endpoints for interview creation, question retrieval, and answer submission.
- Application layer: business logic for interview preparation and evaluation.
- Data layer: PostgreSQL stores interview records, questions, context, and embeddings.
- Storage layer: MinIO stores uploaded resumes.
- AI layer: LLMs and embedding models generate context and personalize interview questions.
- Background processing layer: Celery and RabbitMQ handle heavy tasks asynchronously.

### Key modules

- [src/apis/v1/interview.py](../src/apis/v1/interview.py)
- [src/background_tasks/resume_text_extraction.py](../src/background_tasks/resume_text_extraction.py)
- [src/background_tasks/prepare_interview.py](../src/background_tasks/prepare_interview.py)
- [src/services/embeddings.py](../src/services/embeddings.py)
- [src/services/llm_service.py](../src/services/llm_service.py)
- [src/services/celery_app.py](../src/services/celery_app.py)

---

## 3. Resume Parsing

Resume parsing is the first important step in the pipeline.

### What happens

- The uploaded PDF is downloaded from storage.
- Text is extracted from the PDF using PyMuPDF.
- The extracted text is cleaned and normalized.
- The cleaned resume text is passed to an LLM.
- The LLM extracts structured fields such as:
  - candidate name
  - years of experience
  - skills
  - projects
  - work experience
  - education
  - strengths
  - recommended topics
  - difficulty level

### Why it matters

The system does not rely on raw resume text alone. It converts the resume into a structured profile so interviews can be personalized in a more meaningful way.

---

## 4. Embeddings

Embeddings are vector representations of text.

Instead of representing a sentence as plain text, the model converts it into a numerical vector in a high-dimensional space.

### Why embeddings are useful

- They capture semantic meaning.
- They allow similarity search between different texts.
- They help the system retrieve relevant interview questions even when the wording is different.

In this project:

- the resume context is converted into an embedding
- each interview question is converted into an embedding
- the system compares them to find semantically similar questions

---

## 5. Why pgvector?

pgvector is used because it allows the project to store embeddings directly inside PostgreSQL.

### Benefits

- no need for a separate vector database for small to medium-scale use cases
- easy integration with existing relational data
- simple deployment and maintenance
- supports similarity search directly from the application stack

For this project, pgvector is an effective choice because the system needs semantic retrieval while still keeping the architecture simple and practical.

---

## 6. Similarity Search

Similarity search is the process of finding items that are semantically close to an input.

In this project:

- the resume embedding is compared against question embeddings
- the most relevant questions are retrieved
- those questions are used as the starting pool for the interview

This is more powerful than keyword matching because it can find relevant items even if the words are different but the meaning is similar.

---

## 7. Cosine Similarity

Cosine similarity is the main metric used in this project for retrieval.

### What it means

Cosine similarity measures the angle between two vectors.

- If two vectors point in the same direction, they are considered similar.
- If they are orthogonal, they are considered unrelated.
- If they point in opposite directions, they are considered dissimilar.

### Why it is used

It is especially useful because it focuses on the direction of the vector, which represents semantic meaning.

### Direction vs magnitude

- Direction tells us what the meaning is.
- Magnitude is the length of the vector.

In practical terms:

- a short sentence and a long paragraph can still be considered semantically similar
- cosine similarity ignores the size difference and focuses on meaning

That is why it is a strong choice for comparing resume context to interview questions.

### Why cosine similarity is good for this project

It is a strong fit because:

1. It is robust to length differences.
2. It focuses on meaning rather than exact word overlap.
3. It works well for embedding-based retrieval.
4. It is commonly used in modern RAG systems.

### Other techniques

Other options include:

- Euclidean distance
- dot product
- BM25 keyword search
- hybrid retrieval using both keyword and vector methods

Cosine similarity is preferred here because it is simple, effective, and aligned with the semantic matching requirements of the system.

---

## 8. Sentence Transformers

Sentence transformers are used to generate embeddings from text.

The project currently uses the model:

- `all-MiniLM-L6-v2`

This is a strong general-purpose embedding model and is suitable for semantic similarity tasks.

### Model choice for this use case

For a system where you compare:

- long resume context paragraphs
- short interview questions
- short candidate profile summaries

A query-document optimized model is often better.

### Recommended options

- `multi-qa-MiniLM-L6-cos-v1`: very good for short query vs long document matching
- `all-MiniLM-L6-v2`: strong general-purpose baseline
- `BAAI/bge-m3`: better for higher accuracy and multilingual scenarios, but heavier

### Why this matters

The embedding model directly affects retrieval quality. A better semantic embedding model usually results in better question selection.

---

## 9. Ollama and Qwen

The project uses LLM-based workflows for context extraction and personalization.

### Ollama

Ollama is used to simplify local LLM execution.

Benefits include:

- easier local deployment
- no need to depend heavily on remote APIs for every request
- flexibility to run open-source models locally

### Qwen

Qwen is used as an open-source language model in the LLM workflow.

It helps with:

- reasoning over candidate context
- personalization of interview questions
- generation of structured outputs

---

## 10. Prompt Engineering

Prompt engineering is the practice of crafting instructions carefully so the LLM produces useful, structured, and reliable outputs.

In this project, it matters because the system relies on LLMs for:

- resume interpretation
- structured profile creation
- personalization of questions
- answer evaluation

### Good prompting principles

- provide clear role and task context
- specify the expected output format
- include the relevant input data clearly
- ask for structured JSON when needed
- define boundaries and constraints

Prompt quality directly influences the quality of the system’s output.

---

## 11. Semantic Search

Semantic search retrieves information based on meaning rather than exact keyword overlap.

For example:

- a question about distributed systems may be retrieved for a resume that mentions microservices and event-driven architecture

This is the core value of embedding-based retrieval.

---

## 12. Chunking

Chunking means splitting large documents into smaller pieces before embedding or retrieval.

### Why it is useful

- improves retrieval precision
- helps focus on relevant pieces of information
- reduces noise and context overload

In large-scale RAG systems, chunking is very important. In this project, the pipeline mainly uses summarized candidate context rather than large chunk-based document retrieval, but the concept is still highly relevant for broader RAG applications.

---

## 13. Metadata Filtering

Metadata filtering means narrowing results using structured attributes such as:

- skills
- topics
- question type
- role
- difficulty

This improves retrieval quality because the system does not rely only on vector similarity; it also uses known metadata to filter out irrelevant questions.

In this project, the retrieval process is strengthened by combining semantic relevance with interview-specific context.

---

## 14. RAG (Retrieval-Augmented Generation)

RAG is the process of retrieving relevant information first and then using that information to guide an LLM.

### In simple terms

Instead of asking the model to answer from memory alone, the system first retrieves the most relevant content and provides it as context.

### Why RAG is useful

- improves factual grounding
- reduces hallucinations
- gives better context to the model
- makes responses more relevant to the user’s request

### In this project

The platform uses a retrieval-based workflow for interview question selection and personalization.

The LLM is not acting blindly; it is guided by:

- the candidate’s resume context
- the retrieved interview questions
- structured metadata

This is a practical form of retrieval-augmented generation.

---

## 15. Vector Database

A vector database stores embeddings and enables fast similarity search.

In this project, PostgreSQL with pgvector plays that role.

### Why it works here

- the system is not extremely large
- the database layer is already present
- the architecture remains simple and maintainable

---

## 16. Async Pipelines

Async pipelines allow heavy work to run in the background without blocking the main API response.

### Examples in this project

- resume extraction
- resume context generation
- question preparation
- personalization of questions
- answer evaluation

The project uses Celery and RabbitMQ for this purpose.

### Why it is important

These tasks can take noticeable time. Running them asynchronously keeps the application responsive and reliable.

---

## 17. How the Retrieval Flow Works in This Project

The core retrieval flow is:

1. Build candidate context from the resume.
2. Convert the candidate context into an embedding.
3. Convert interview questions into embeddings.
4. Compare embeddings using cosine similarity.
5. Retrieve the most relevant questions.
6. Apply metadata filtering.
7. Personalize the selected questions.

This gives the platform a strong semantic retrieval foundation.

---

## 18. Interview-Ready Summary

A concise way to explain this project in an interview is:

> This project is an AI-powered mock interview platform built with FastAPI, PostgreSQL, pgvector, and LLMs. When a candidate uploads a resume, the system extracts the text, builds a structured candidate profile, creates embeddings for the resume and interview questions, and retrieves the most relevant questions using semantic similarity. The platform then personalizes those questions and evaluates answers. I use sentence-transformers for embeddings, pgvector for similarity search, Ollama and Qwen for LLM-based workflows, and Celery with RabbitMQ for asynchronous processing.

---

## 19. Common Interview Questions and Answers

### Q1. What is cosine similarity?

Cosine similarity measures how similar two vectors are by comparing their direction. It is commonly used in embedding-based search because it focuses on semantic meaning rather than text length.

### Q2. Why not use exact keyword search only?

Keyword search is limited because it misses semantic matches. Embedding-based retrieval can find relevant content even if the wording is different.

### Q3. Why is pgvector used?

It allows vector similarity search inside PostgreSQL, keeping the architecture simpler and easier to manage.

### Q4. What is the difference between semantic search and keyword search?

Keyword search looks for matching words. Semantic search looks for matching meaning.

### Q5. What is RAG?

RAG is the process of retrieving relevant content first and then using that content as context for an LLM.

### Q6. Why is async processing important?

It keeps the application responsive and allows heavy AI workflows to run in the background.

---

## 20. Final Takeaway

This project combines classic software architecture with modern AI techniques.

The main idea is simple:

- understand the candidate
- retrieve relevant interview questions semantically
- personalize the experience
- evaluate the responses intelligently

That combination makes the system more useful, more adaptive, and more aligned with real interview scenarios.
