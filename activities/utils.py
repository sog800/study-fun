def chunk_text(text, max_length=500):
    """
    Break text into smaller chunks (e.g., ~500 characters each).
    """
    words = text.split()
    chunks, current = [], []

    for word in words:
        if len(" ".join(current + [word])) > max_length:
            chunks.append(" ".join(current))
            current = [word]
        else:
            current.append(word)

    if current:
        chunks.append(" ".join(current))

    return chunks
