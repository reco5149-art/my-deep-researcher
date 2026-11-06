"""토큰 수 세기. tiktoken 이 있으면 정확히, 없으면 '영문 4글자 ≈ 1토큰'으로 어림한다."""

_ENC = None
_TRIED = False


def _encoder():
    global _ENC, _TRIED
    if not _TRIED:
        _TRIED = True
        try:
            import tiktoken  # noqa: WPS433

            _ENC = tiktoken.get_encoding("o200k_base")
        except Exception:  # 설치 안 됨 / 인코딩 파일 다운로드 실패
            _ENC = None
    return _ENC


def count_tokens(text: str) -> int:
    enc = _encoder()
    if enc is not None:
        return len(enc.encode(text, disallowed_special=()))
    return max(1, len(text) // 4)


def method() -> str:
    return "tiktoken(o200k_base)" if _encoder() is not None else "어림값(글자 수 ÷ 4)"
