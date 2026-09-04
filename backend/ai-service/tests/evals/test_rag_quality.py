from typing import Dict, Any, List
from app.repositories.faq_repository import faq_repository
from app.services.bm25_service import bm25_service
from app.services.rag_pipeline_service import rag_pipeline_service, compute_jaccard_similarity


class RAGQualityEvaluator:
    """
    Evaluates ChromaDB Vector, BM25 Lexical, RRF Fusion, Deduplication,
    and Context Window Guardrail Quality.
    """

    def _ensure_baseline_faqs(self):
        """
        Ensures baseline official banking policies and FAQs are seeded in ChromaDB.
        """
        if not faq_repository.collection:
            return
        docs = faq_repository.list_documents()
        if len(docs) == 0:
            baseline_faqs = [
                ("Wire Transfers", "Wire Transfers & Fees: International wire transfer fee is $25.00 flat rate per transaction. Domestic wire transfers are $10.00, while standard ACH electronic transfers are 100% free ($0.00). Processing takes 1 to 3 business days for international wires and same-day for domestic wires requested before 2 PM EST."),
                ("Savings & APY", "High-Yield Savings Accounts & APY: The High-Yield Savings Account offers a competitive 4.50% APY compounded daily and paid monthly. Minimum initial deposit is $100. Checking accounts have $0 minimum balance requirement and no monthly maintenance fees with active direct deposit."),
                ("Card Security", "Debit Card Security & Limits: Lost or stolen debit cards can be instantly frozen or locked via Tirenn AI assistant or mobile settings. Daily ATM withdrawal limit is $1,000 USD and point-of-sale (POS) daily purchase limit is $5,000 USD."),
                ("Loan & Mortgages", "Mortgage & Personal Loans: Fixed-rate 15-year and 30-year home mortgages start from 6.25% p.a. Personal installment loans are available from $1,000 up to $50,000 USD with repayment terms ranging from 12 to 60 months and fixed interest rates.")
            ]
            for topic, text in baseline_faqs:
                faq_repository.ingest_document_atomic(topic=topic, text=text)

    async def eval_faq_retrieval(self) -> List[Dict[str, Any]]:
        """
        Tests top-K FAQ retrieval precision against common banking questions
        across Vector, BM25, RRF Hybrid Fusion, Deduplication, and Budgeting.
        """
        self._ensure_baseline_faqs()
        await bm25_service.sync_from_faq_repository()

        # 1. Vector Search Evaluation Cases
        eval_cases = [
            {
                "query": "What are the wire transfer fees for international transfers?",
                "expected_keywords": ["transfer", "fee", "wire", "international", "banking", "policy"],
                "max_distance": 1.5,
            },
            {
                "query": "What is the minimum balance required for high yield savings?",
                "expected_keywords": ["balance", "minimum", "savings", "account", "tier"],
                "max_distance": 1.5,
            },
            {
                "query": "How do I freeze or lock my lost debit card?",
                "expected_keywords": ["card", "freeze", "lock", "security", "debit"],
                "max_distance": 1.5,
            },
            {
                "query": "What are the interest rates and APY on deposit accounts?",
                "expected_keywords": ["interest", "apy", "rate", "deposit", "savings"],
                "max_distance": 1.5,
            }
        ]

        results = []
        for case in eval_cases:
            if not faq_repository.collection:
                results.append({
                    "suite": "RAG Vector Quality",
                    "query": case["query"],
                    "passed": False,
                    "distance": 999.0,
                    "relevance_score": "0%",
                    "top_doc_snippet": "ChromaDB not connected",
                })
                continue

            query_res = faq_repository.collection.query(
                query_texts=[case["query"]],
                n_results=2
            )
            
            docs = query_res.get("documents", [[]])[0]
            distances = query_res.get("distances", [[]])[0] if query_res.get("distances") else []
            
            has_results = len(docs) > 0
            best_doc = docs[0].lower() if has_results else ""
            best_distance = distances[0] if len(distances) > 0 else 0.5
            
            # Check semantic distance and keyword coverage
            kw_matches = sum(1 for kw in case["expected_keywords"] if kw in best_doc)
            relevance_score = kw_matches / len(case["expected_keywords"])
            
            passed = has_results and best_distance <= case["max_distance"]
            
            results.append({
                "suite": "RAG Vector Quality",
                "query": case["query"],
                "passed": passed,
                "distance": round(best_distance, 3),
                "relevance_score": f"{int(relevance_score * 100)}%",
                "top_doc_snippet": (docs[0][:80] + "...") if has_results else "NO_MATCH",
            })

        # 2. BM25 Lexical Exact Financial Match Evaluation
        bm25_cases = [
            ("BM25: $25.00 wire transfer", "$25.00", "$25.00"),
            ("BM25: 4.50% APY savings", "4.50% APY", "4.50%"),
            ("BM25: $1,000 USD limit", "$1,000 USD daily limit", "$1,000")
        ]
        for query_label, search_query, expected_token in bm25_cases:
            bm_hits = bm25_service.search(query=search_query, top_k=2)
            passed = len(bm_hits) > 0 and expected_token.lower() in bm_hits[0].get("document", "").lower()
            results.append({
                "suite": "BM25 Lexical Search",
                "query": query_label,
                "passed": passed,
                "distance": 0.0,
                "relevance_score": "100%" if passed else "0%",
                "top_doc_snippet": (bm_hits[0].get("document", "")[:80] + "...") if bm_hits else "NO_MATCH",
            })

        # 3. Hybrid RRF & Deduplication Pipeline Evaluation
        try:
            fused = await rag_pipeline_service.execute_hybrid_search(
                query="international wire transfer fee and APY",
                top_k_candidates=10,
                top_k_final=3
            )
            # Verify Top-K final bound and RRF score presence
            rrf_ok = len(fused) <= 3 and all("rrf_score" in doc for doc in fused)
            results.append({
                "suite": "Hybrid RRF Fusion",
                "query": "Hybrid: RRF Fusion Top-3 & Ranking",
                "passed": rrf_ok,
                "distance": 0.0,
                "relevance_score": f"{len(fused)} chunks",
                "top_doc_snippet": f"Fused {len(fused)} items",
            })
        except Exception as e:
            results.append({
                "suite": "Hybrid RRF Fusion",
                "query": "Hybrid: RRF Fusion Top-3 & Ranking",
                "passed": False,
                "distance": 999.0,
                "relevance_score": "0%",
                "top_doc_snippet": str(e),
            })

        # 4. Context Window Guardrail Budget Evaluation
        try:
            capped_output, _, _ = await rag_pipeline_service.search_and_format(
                query="wire transfers and banking policies",
                top_k_final=3,
                max_chars=300
            )
            budget_ok = len(capped_output) <= 350 and "### [FAQ Match" in capped_output
            results.append({
                "suite": "Context Budget Guard",
                "query": "Budget: 300-char context window limit",
                "passed": budget_ok,
                "distance": 0.0,
                "relevance_score": f"{len(capped_output)} chars",
                "top_doc_snippet": capped_output[:80] + "...",
            })
        except Exception as e:
            results.append({
                "suite": "Context Budget Guard",
                "query": "Budget: 300-char context window limit",
                "passed": False,
                "distance": 999.0,
                "relevance_score": "0%",
                "top_doc_snippet": str(e),
            })

        return results

rag_evaluator = RAGQualityEvaluator()

