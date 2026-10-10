import os
import re

def load_policy_chunks(policy_dir="policies", chunk_size=1200, overlap=150):
    """Extract text from policy PDFs and split it into overlapping chunks."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("Install dependencies with: pip install -r requirements.txt") from exc

    if not os.path.isdir(policy_dir):
        return []
    chunks = []
    for filename in sorted(os.listdir(policy_dir)):
        if not filename.lower().endswith(".pdf"):
            continue
        path = os.path.join(policy_dir, filename)
        reader = PdfReader(path)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        text = re.sub(r"\s+", " ", text).strip()
        start = 0
        while start < len(text):
            part = text[start:start + chunk_size]
            if part.strip():
                chunks.append({"source": filename, "text": part})
            start += max(1, chunk_size - overlap)
    return chunks

def search_policy(question, chunks, limit=4):
    """Simple lexical retrieval; no external embedding service is required."""
    stop = {"the", "a", "an", "is", "are", "to", "for", "of", "and", "or",
            "my", "me", "i", "do", "does", "what", "how", "can", "will", "about"}
    terms = {w.lower() for w in re.findall(r"[a-zA-Z0-9₹]+", question) if w.lower() not in stop}
    scored = []
    for chunk in chunks:
        text_terms = {w.lower() for w in re.findall(r"[a-zA-Z0-9₹]+", chunk["text"])}
        score = len(terms & text_terms)
        if score:
            scored.append((score, chunk))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in scored[:limit]]
