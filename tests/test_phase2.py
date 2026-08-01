import pytest
from antigravity_cli.session_validator import SessionValidator, ValidationResult


def test_validate_header_string_chatgpt():
    header_str = "session_token=mock_session_token_1234567890; __Secure-next-auth.session-token=mock_jwt_token_payload"
    res = SessionValidator.validate_session("chatgpt", header_str, account_label="user@example.com")
    assert res.is_valid is True
    assert res.format_type == "header_string"
    assert res.provider == "chatgpt"
    assert res.normalized_session["cookies"]["session_token"] == "mock_session_token_1234567890"
    assert "cookie_header" in res.normalized_session


def test_validate_json_dict_chatgpt():
    json_str = '{"session_token": "mock_session_token_1234567890", "__Secure-next-auth.session-token": "mock_jwt_token_payload"}'
    res = SessionValidator.validate_session("chatgpt", json_str)
    assert res.is_valid is True
    assert res.format_type == "json"
    assert res.provider == "chatgpt"
    assert res.normalized_session["cookies"]["session_token"] == "mock_session_token_1234567890"


def test_validate_json_list_gemini():
    json_list = '[{"name": "__Secure-1PSID", "value": "g.a000testpsid"}, {"name": "__Secure-3PSID", "value": "g.a000test3psid"}]'
    res = SessionValidator.validate_session("gemini", json_list)
    assert res.is_valid is True
    assert res.format_type == "json"
    assert res.provider == "gemini"
    assert res.normalized_session["cookies"]["__Secure-1PSID"] == "g.a000testpsid"


def test_reject_invalid_json():
    invalid_json = '{"broken": json...}'
    res = SessionValidator.validate_session("chatgpt", invalid_json)
    assert res.is_valid is False
    assert "Malformed JSON" in res.error_message or "Could not parse" in res.error_message


def test_reject_missing_required_token():
    # Cookie header that lacks session token for ChatGPT
    header_str = "random_cookie=123; foo=bar"
    res = SessionValidator.validate_session("chatgpt", header_str)
    assert res.is_valid is False
    assert "missing required token" in res.error_message


def test_reject_unsupported_provider():
    res = SessionValidator.validate_session("claude", "foo=bar")
    assert res.is_valid is False
    assert "Unsupported provider" in res.error_message
