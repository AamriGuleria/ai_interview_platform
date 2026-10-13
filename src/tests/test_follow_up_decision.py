import pytest

from background_tasks.evaluate_answers import should_generate_follow_up


@pytest.mark.parametrize(
    ("score", "evaluation_recommends_follow_up", "expected"),
    [
        (69, True, True),
        (70, True, False),
        (95, True, False),
        (40, False, False),
    ],
)
def test_should_generate_follow_up(
    score: float,
    evaluation_recommends_follow_up: bool,
    expected: bool,
) -> None:
    assert should_generate_follow_up(
        score,
        evaluation_recommends_follow_up,
    ) is expected
