from background_tasks.resume_text_extraction import clean_text


def test_clean_text_normalize_whitespace():
    result = clean_text(" Hello world \r\n\r\n\r\n Python ")
    assert result == "Hello world \n\n Python"

def test_clean_text_removes_control_characters():
    assert clean_text("hello\x00world") == "helloworld"

def test_clean_text_handles_empty_input():
    assert clean_text("") == ""