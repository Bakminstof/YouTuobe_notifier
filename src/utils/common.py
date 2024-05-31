def strip_text(text: str, text_max_len: int = 140, placeholder: str = "....") -> str:
    """
    Обрезание текста до указанной длины,
    заменяя избыточные символы (середина текста) на плейсхолдеры
    """
    if len(text) < text_max_len:
        return text

    len_half_placeholder = int(len(placeholder) / 2)
    start_strip_idx = int(text_max_len / 2 - len_half_placeholder)
    stop_strip_idx = len(text) - start_strip_idx

    return f"{text[:start_strip_idx]}{placeholder}{text[stop_strip_idx:]}"
