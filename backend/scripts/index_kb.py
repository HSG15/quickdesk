import sys
from pathlib import Path

# Ensure backend directory is in Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.rag_service import index_knowledge_base, retrieve_relevant_chunks


def main():
    print("==================================================")
    print(" QuickDesk Knowledge Base Indexing — Chroma RAG   ")
    print("==================================================")

    result = index_knowledge_base()

    print(f"\nIndexing Complete:")
    print(f"  • Articles processed: {result['articles_indexed']}")
    print(f"  • Chunks stored in Chroma: {result['chunks_indexed']}")
    print(f"\nIndexed Articles:")
    for t in result["article_titles"]:
        print(f"  [KB] {t}")

    print("\n--------------------------------------------------")
    print(" Verifying Sample Retrieval Query: 'VPN connection'")
    print("--------------------------------------------------")
    sample_query = "VPN connection drops after 5 minutes"
    chunks = retrieve_relevant_chunks(sample_query, top_k=2)
    print(f"Query: \"{sample_query}\"")
    print(f"Retrieved {len(chunks)} chunks:")
    for c in chunks:
        print(f"  • [{c['article_id']}] {c['title']} (Score: {c['score']:.3f})")

    print("\nChroma Vector Index is Ready!")


if __name__ == "__main__":
    main()
