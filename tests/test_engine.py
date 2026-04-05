# tests/test_engine.py
from engine import RefinerEngine

def test_build_refiner_prompt_contains_original():
    engine = RefinerEngine()
    prompt = engine.build_refiner_prompt("write a sort function", comment=None)
    assert "write a sort function" in prompt

def test_build_refiner_prompt_contains_json_instruction():
    engine = RefinerEngine()
    prompt = engine.build_refiner_prompt("explain recursion", comment=None)
    assert "JSON" in prompt
    assert "refined_prompt" in prompt
    assert "annotations" in prompt

def test_build_refiner_prompt_with_comment():
    engine = RefinerEngine()
    prompt = engine.build_refiner_prompt("write code", comment="make it shorter")
    assert "make it shorter" in prompt

def test_parse_response_valid_json():
    engine = RefinerEngine()
    raw = '{"refined_prompt": "You are an expert. Write code.", "annotations": [{"technique": "Role prompting", "reason": "code task"}]}'
    result = engine.parse_response(raw)
    assert result["refined_prompt"] == "You are an expert. Write code."
    assert len(result["annotations"]) == 1

def test_parse_response_extracts_json_from_text():
    engine = RefinerEngine()
    raw = 'Here is the refined prompt:\n\n```json\n{"refined_prompt": "test", "annotations": []}\n```'
    result = engine.parse_response(raw)
    assert result["refined_prompt"] == "test"

def test_parse_response_returns_fallback_on_failure():
    engine = RefinerEngine()
    result = engine.parse_response("this is not json at all")
    assert "refined_prompt" in result
    assert "annotations" in result
