from database.session_manager import db_manager
from models.Interview import Interview
from services.llm_service import GeminiService


def prepare_interview_report(
    interview_id: int
):
    try:
        from crud.interview import InterviewService

        with db_manager.sync_session_scope() as sync_db:
            interview_service = InterviewService(sync_db)
            interview = interview_service.get_interview(interview_id)
            prepare_interview_result(interview)
    except Exception as e:
        raise


def prepare_interview_result(interview: Interview):
    try:
        from crud.interview import InterviewService

        with db_manager.sync_session_scope() as sync_db:
            interview_service = InterviewService(sync_db)
            interview_questions = interview_service.get_interview_questions(interview.id)
            evaluation_data = []

            for iq in interview_questions:
                evaluation_data.append({
                    "question": iq.personalized_question
                        or iq.original_question,
                    "score": iq.score,
                    "feedback": iq.feedback,
                    "strengths": iq.strengths,
                    "gaps": iq.gaps
                })
            llm_service = GeminiService()
            result = llm_service.get_interview_evaluation(
                interview_id=interview.id,
                interview_context=interview.interview_context or {},
                evaluation_results=evaluation_data
            )
            interview_service.set_interview_result(interview, result)
    except Exception as e:
        raise