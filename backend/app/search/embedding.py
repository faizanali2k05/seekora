import hashlib
import math
import re

TOKEN = re.compile(r"[a-z0-9]+")


class HashingEmbedder:
    """Small deterministic baseline; replace through this interface without API changes."""

    dimensions = 384
    model_name = "hashing-v1"

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in TOKEN.findall(text.lower()):
            digest = hashlib.blake2b(token.encode(), digest_size=8).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[bucket] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector
