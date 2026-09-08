import pytest
from types import SimpleNamespace
from background_tasks.prepare_interview import should_personalize

@pytest.mark.parametrize(
    "question_type, expected",
    [
        ("Behaviour",True),
        ("Project",True),
        ("Technical",False)
    ]
)
def test_should_personalize_by_question_type(question_type,expected):
    question = SimpleNamespace(
        question_type=question_type,
        skills=[],
    )
    assert should_personalize(question,{"skills":[]}) is expected

# Sample Pytest command
# python -m pytest tests/test_clean_resume_text.py