import hashlib

from dissertation.core.openai_client import embed_text
from dissertation.core.cache_store import store_bundle, get_cached_by_similarity

text1 = "As a user, I want to reset my password so that I can regain access."
text2 = "Allow users to reset forgotten passwords to access their account again."

emb1 = embed_text(text1)
emb2 = embed_text(text2)

h = hashlib.sha256(text1.lower().encode("utf-8")).hexdigest()

store_bundle(
    raw_text=text1,
    normalized_text=text1.lower(),
    text_hash=h,
    embedding=emb1,
    bundle_json={"stories": ["dummy"], "scenarios": ["dummy"], "trace_map": {}},
    model="test",
)

hit = get_cached_by_similarity(emb2, min_similarity=0.60)
print(hit)
