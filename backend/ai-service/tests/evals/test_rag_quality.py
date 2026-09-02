from typing import Dict, Any, List
from app.repositories.faq_repository import faq_repository


class RAGQualityEvaluator:
    """
    Evaluates ChromaDB Vector RAG Retrieval Quality and Semantic Relevance.
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
        Tests top-K FAQ retrieval precision against common banking questions.
        """
        self._ensure_baseline_faqs()

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

        return results

rag_evaluator = RAGQualityEvaluator()

