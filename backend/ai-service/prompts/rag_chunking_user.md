You are an expert financial document parser and semantic chunking specialist.
Task: Divide the following banking document (Topic: '{topic}') into coherent, self-contained semantic chunks.

Rules for Dynamic Semantic Chunking:
1. Do NOT cut mid-sentence, mid-policy, mid-clause, or in the middle of financial tables/interest rates.
2. Each chunk must be a complete, self-contained unit of information (100 to 500 characters).
3. Include necessary contextual headings or clauses so each chunk is fully understandable independently.
4. Return ONLY a valid JSON array of strings: ["chunk 1 text", "chunk 2 text", ...]. Do not include markdown code block markers or extra explanation.

Document Text:
{text}
