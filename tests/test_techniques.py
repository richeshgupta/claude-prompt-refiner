from techniques import detect_task_type, get_techniques_for_task

def test_detect_code_task():
    assert detect_task_type("write a python function to sort a list") == "code"

def test_detect_debug_task():
    assert detect_task_type("fix this bug in my code") == "debug"

def test_detect_explanation_task():
    assert detect_task_type("explain how neural networks work") == "explanation"

def test_detect_general_task():
    assert detect_task_type("what is the best way to structure a team") == "general"

def test_techniques_for_code():
    techniques = get_techniques_for_task("code")
    names = [t["name"] for t in techniques]
    assert "Role prompting" in names
    assert "Chain-of-thought" in names

def test_techniques_for_general():
    techniques = get_techniques_for_task("general")
    names = [t["name"] for t in techniques]
    assert "XML structuring" in names
