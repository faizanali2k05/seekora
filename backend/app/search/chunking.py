def chunk_text(text: str, target_words: int = 180, overlap_words: int = 30) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks: list[str] = []
    step = max(1, target_words - overlap_words)
    for start in range(0, len(words), step):
        chunk = " ".join(words[start : start + target_words])
        if chunk:
            chunks.append(chunk)
        if start + target_words >= len(words):
            break
    return chunks
