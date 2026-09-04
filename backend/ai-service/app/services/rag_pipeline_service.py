"""
Advanced Hybrid RAG Pipeline Service for Tirenn Banking Copilot.
================================================================
Combines:
1. Dual Retrieval: Dense Vector Search (ChromaDB) + Sparse Lexical Search (BM25)
2. Reciprocal Rank Fusion (RRF): Pure algorithmic rank merger (< 1 ms latency)
3. Content Deduplication: Filters out redundant/overlapping sliding-window chunks (> 85% overlap)
4. Top-K Final Selection: Narrows down to top 3 highest-precision chunks
5. Context Window Budget Guardrail: Hard cap on output characters to prevent context window explosion
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from app.config import settings
from app.repositories.faq_repository import faq_repository
from app.services.bm25_service import bm25_service, tokenize_financial_text
from app.logger import app_logger as logger


def compute_jaccard_similarity(text_a: str, text_b: str) -> float:
    """
    Computes word-level Jaccard similarity between two text snippets:
    Jaccard(A, B) = |A ∩ B| / |A ∪ B|
    """
    words_a = set(tokenize_financial_text(text_a))
    words_b = set(tokenize_financial_text(text_b))

    if not words_a or not words_b:
        return 0.0

    intersection = len(words_a.intersection(words_b))
    union = len(words_a.union(words_b))

    return intersection / union if union > 0 else 0.0


class RAGPipelineService:
    """
    Orchestrates the 5-stage Hybrid Retrieval, Fusion, Deduplication,
    and Budgeting pipeline for banking FAQ inquiries.
    """

    def __init__(self):
        self._rrf_k = 60  # Standard smoothing constant for Reciprocal Rank Fusion

    async def execute_hybrid_search(
        self,
        query: str,
        top_k_candidates: Optional[int] = None,
        top_k_final: Optional[int] = None,
        dedup_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes the full hybrid search and fusion pipeline.

        Returns:
            List of top-k unique, deduplicated, and re-ranked document dictionaries.
        """
        candidates_k = top_k_candidates or settings.RAG_TOP_K_CANDIDATES
        final_k = top_k_final or settings.RAG_TOP_K_FINAL
        threshold = dedup_threshold or settings.RAG_DEDUPLICATION_THRESHOLD

        # Ensure BM25 index is populated (auto-sync if empty)
        if bm25_service.corpus_size == 0:
            await bm25_service.sync_from_faq_repository()

        # -------------------------------------------------------------
        # Stage 1: Dual Retrieval (Vector + Lexical)
        # -------------------------------------------------------------
        # 1A. Vector Search (ChromaDB)
        vector_results = faq_repository.search_raw(query=query, n_results=candidates_k)

        # 1B. Lexical Search (BM25)
        bm25_results = bm25_service.search(query=query, top_k=candidates_k)

        logger.debug(f"[Hybrid RAG Dual-Retrieval] Vector: {len(vector_results)} candidates | BM25: {len(bm25_results)} candidates")

        # -------------------------------------------------------------
        # Stage 2: Reciprocal Rank Fusion (RRF)
        # -------------------------------------------------------------
        rrf_scores: Dict[str, float] = {}
        doc_store: Dict[str, Dict[str, Any]] = {}

        # Process Vector rankings
        for rank, item in enumerate(vector_results, 1):
            doc_text = item.get("document", "").strip()
            if not doc_text:
                continue
            doc_id = item.get("id") or str(hash(doc_text))
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (self._rrf_k + rank))
            doc_store[doc_id] = item

        # Process BM25 rankings
        for rank, item in enumerate(bm25_results, 1):
            doc_text = item.get("document", "").strip()
            if not doc_text:
                continue
            doc_id = item.get("id") or str(hash(doc_text))
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (self._rrf_k + rank))
            if doc_id not in doc_store:
                doc_store[doc_id] = item

        # Sort all candidates by combined RRF score descending
        fused_candidates = sorted(
            [
                {**doc_store[doc_id], "rrf_score": round(score, 6)}
                for doc_id, score in rrf_scores.items()
            ],
            key=lambda x: x["rrf_score"],
            reverse=True
        )

        logger.debug(f"[Hybrid RAG RRF Merged] Total unique candidates across both engines: {len(fused_candidates)}")

        # -------------------------------------------------------------
        # Stage 3: Content Deduplication Filter
        # -------------------------------------------------------------
        deduplicated: List[Dict[str, Any]] = []

        for candidate in fused_candidates:
            candidate_text = candidate.get("document", "")
            is_duplicate = False

            for existing in deduplicated:
                existing_text = existing.get("document", "")
                
                # Check A: Exact substring or high Jaccard overlap
                if candidate_text in existing_text or existing_text in candidate_text:
                    is_duplicate = True
                    break

                sim = compute_jaccard_similarity(candidate_text, existing_text)
                if sim >= threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                deduplicated.append(candidate)

        logger.info(
            f"🔍 [Hybrid RAG Funnel] Query: '{query[:40]}...' | "
            f"Vector: {len(vector_results)}, BM25: {len(bm25_results)} -> "
            f"RRF Fused: {len(fused_candidates)} -> Dedup: {len(deduplicated)} -> "
            f"Final Selected: {min(len(deduplicated), final_k)} chunks"
        )

        # -------------------------------------------------------------
        # Stage 4: Top-K Final Selection
        # -------------------------------------------------------------
        return deduplicated[:final_k]

    async def search_and_format(
        self,
        query: str,
        top_k_final: Optional[int] = None,
        max_chars: Optional[int] = None
    ) -> Tuple[str, Optional[str], Optional[Dict[str, Any]]]:
        """
        Executes the hybrid search pipeline and returns a clean, budget-capped markdown
        string for tool execution in SubAgents.
        """
        final_k = top_k_final or settings.RAG_TOP_K_FINAL
        char_budget = max_chars or settings.RAG_MAX_OUTPUT_CHARS

        results = await self.execute_hybrid_search(query=query, top_k_final=final_k)

        if not results:
            return "No matching FAQ articles found in banking knowledge base.", None, None

        formatted_chunks: List[str] = []
        for i, item in enumerate(results, 1):
            q_title = item.get("metadata", {}).get("question", "Banking FAQ")
            category = item.get("metadata", {}).get("category", "General")
            content = item.get("document", "").strip()

            chunk_repr = (
                f"### [FAQ Match {i}] {q_title}\n"
                f"Category: {category}\n"
                f"{content}"
            )
            formatted_chunks.append(chunk_repr)

        full_output = "\n\n".join(formatted_chunks)

        # -------------------------------------------------------------
        # Stage 5: Context Window / Character Budget Guardrail
        # -------------------------------------------------------------
        if len(full_output) > char_budget:
            logger.info(f"✂️ [RAG Context Budget] Truncating output from {len(full_output)} to {char_budget} chars")
            # Truncate at nearest newline or space before budget limit
            truncated = full_output[:char_budget]
            last_break = max(truncated.rfind("\n"), truncated.rfind(". "))
            if last_break > char_budget * 0.7:
                truncated = truncated[:last_break]
            full_output = truncated.strip() + "\n\n... [Remaining context truncated for token efficiency]"

        return full_output, None, None


# Global singleton instance
rag_pipeline_service = RAGPipelineService()
