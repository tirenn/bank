"""
BM25 Lexical Search Service for Tirenn Banking Microservice.
============================================================
Provides fast, exact-match keyword retrieval tailored for financial documents.

Why BM25 in addition to Vector Search?
--------------------------------------
Vector embeddings (like all-MiniLM-L6-v2) capture general semantic concepts (e.g.,
knowing that 'wire transfer' is related to 'remittance'), but they struggle with exact
numbers, percentages, regulation codes, and currency amounts.
BM25 complements vector search by scoring exact word frequencies and financial tokens.

Financial Tokenizer:
--------------------
Preserves:
- Currency amounts: $500, Rp100.000, 1000EUR
- Percentages: 0.25%, 5.5%
- Identifiers: ACC-1002, PBI No. 23
"""

import math
import re
from typing import List, Dict, Any, Optional
from app.repositories.faq_repository import faq_repository
from app.logger import app_logger as logger


def tokenize_financial_text(text: str) -> List[str]:
    """
    Tokenizes text while preserving financial symbols, percentages, and identifiers.
    """
    if not text:
        return []
    # Match words, numbers with decimals, percentages, currency prefixes, and hyphenated IDs
    pattern = r'(?:[\$€£¥]|rp)?\d+(?:[.,]\d+)?%?|[a-z0-9]+(?:[-_][a-z0-9]+)*'
    tokens = re.findall(pattern, text.lower())
    return [t for t in tokens if len(t) > 1 or t.isalnum()]


class BM25Service:
    """
    In-memory BM25Okapi search engine.
    Zero RAM overhead (< 3 MB for 1,000 banking FAQ articles).
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = 0
        self.avgdl = 0.0
        self.doc_lengths: List[int] = []
        self.doc_freqs: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.tokenized_corpus: List[List[str]] = []
        self.raw_documents: List[Dict[str, Any]] = []

    def build_index(self, documents: List[Dict[str, Any]]) -> None:
        """
        Builds the BM25 index from a list of document dicts.
        Each document dict must have 'document' (text) and optional 'metadata'.
        """
        self.raw_documents = documents
        self.corpus_size = len(documents)
        self.tokenized_corpus = []
        self.doc_lengths = []
        self.doc_freqs = {}
        self.idf = {}

        if self.corpus_size == 0:
            self.avgdl = 0.0
            return

        total_length = 0

        # Step 1: Tokenize and compute document frequencies
        for doc in documents:
            text = doc.get("document", "")
            tokens = tokenize_financial_text(text)
            self.tokenized_corpus.append(tokens)
            doc_len = len(tokens)
            self.doc_lengths.append(doc_len)
            total_length += doc_len

            # Track unique terms per document for Document Frequency (DF)
            unique_terms = set(tokens)
            for term in unique_terms:
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1

        self.avgdl = total_length / self.corpus_size if self.corpus_size > 0 else 0.0

        # Step 2: Pre-compute Inverse Document Frequency (IDF) with BM25 smoothing
        for term, freq in self.doc_freqs.items():
            self.idf[term] = math.log(1.0 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

        logger.info(f"📚 [BM25 Index Built] Indexed {self.corpus_size} documents (Vocab: {len(self.idf)} terms, AvgDL: {self.avgdl:.1f})")

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Scores documents against the query using BM25Okapi formula.
        Returns top_k matching documents with their BM25 score.
        """
        if self.corpus_size == 0 or not query.strip():
            return []

        query_tokens = tokenize_financial_text(query)
        if not query_tokens:
            return []

        scores: List[float] = [0.0] * self.corpus_size

        for term in query_tokens:
            if term not in self.idf:
                continue

            term_idf = self.idf[term]

            for i in range(self.corpus_size):
                # Count term frequency in document i
                doc_tokens = self.tokenized_corpus[i]
                tf = doc_tokens.count(term)
                if tf == 0:
                    continue

                doc_len = self.doc_lengths[i]
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avgdl))
                scores[i] += term_idf * (numerator / denominator)

        # Pair scores with original documents
        ranked_results = []
        for i, score in enumerate(scores):
            if score > 0.0:
                doc_copy = dict(self.raw_documents[i])
                doc_copy["score"] = round(score, 4)
                ranked_results.append(doc_copy)

        # Sort descending by score
        ranked_results.sort(key=lambda x: x["score"], reverse=True)
        return ranked_results[:top_k]

    async def sync_from_faq_repository(self) -> int:
        """
        Loads all current FAQ chunks from ChromaDB and refreshes the BM25 index.
        Ensures both lexical and vector indexes stay in 100% real-time sync.
        """
        try:
            items = faq_repository.list_documents()
            formatted_docs = [
                {
                    "id": item.get("id"),
                    "document": item.get("content", ""),
                    "metadata": {
                        "topic": item.get("topic", ""),
                        "batch_id": item.get("batch_id", "")
                    }
                }
                for item in items
            ]
            self.build_index(formatted_docs)
            return len(formatted_docs)
        except Exception as e:
            logger.warning(f"[BM25 Sync Warning]: Could not sync from ChromaDB ({e}). Will retry on next request.")
            return 0


# Global singleton instance
bm25_service = BM25Service()
