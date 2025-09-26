#!/usr/bin/env python3
"""
Test Document Upload Pipeline
Tests the complete flow from text input to HTML conversion and Mimir indexation
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.services.document_processor import DocumentProcessor
# Skip embedding service for now due to missing dependencies

# Test data - your actual examples
TEST_DOCUMENT_1 = """Hackathon Vierzon
Cursor
v0.dev


Hackathon LLMxLaw (Station F)
Ressources (cf. mail avant hackathon) Koyeb, LlamaIndex, Together.ai, etc. https://koyeb.notion.site/Koyeb-Resources-for-LLM-x-Law-Hackathon-at-Station-F-13f914392cfe80bebf22d7b0b2fff722
https://www.koyeb.com/tutorials/use-llamaindex-to-build-a-retrieval-augmented-generation-rag-application
https://docs.llamaindex.ai/en/stable/getting_started/starter_example/


Tex-to-3D
Axel Nguyen Kerbel (troca)
https://research.nvidia.com/labs/toronto-ai/LLaMA-Mesh/, https://arxiv.org/pdf/2411.09595


HuggingFace


RNN


Attentions Mechanism
Big innovation in ML. Rather than going word by word in order, it would consider a sentence as a whole and gives more relevant weighs depending on the whole context.
https://aigents.co/learn/Attention-mechanism
https://towardsdatascience.com/introduction-to-attention-mechanism-8d044442a29 (-> suggestion vers un article sur les modèles de diffusion, écrit par Kemal Erdem)


Diffusion Models
Article de Kemal Erdem : https://erdem.pl/2023/11/step-by-step-visual-introduction-to-diffusion-models
-> Cite 3 papiers :
- 2015 : https://arxiv.org/abs/1503.03585, « Deep Unsupervised Learning using Nonequilibrium Thermodynamics »
- 2020 : https://arxiv.org/abs/2006.11239, « Denoising Diffusion Probabilistic Models »
- 2021 (Researchers from OpenAI) : https://arxiv.org/abs/2102.09672, « Improved Denoising Diffusion Probabilistic Models »
Remarque : les deux auteurs d'OpenAI ont depuis publié des papiers sur la génération 3D. Dinguerie.

Erdem cite aussi un autre crack : Lilian Weng (qui taff chez OpenAI mtn d'ailleurs).

Lilan Weng
Blog du turfu. Son git à 9k followers aussi. Hyper clair.
https://lilianweng.github.io


GANs

VLMs


RAG
https://www.youtube.com/watch?v=kPL-6-9MVyA


Apps

Cursor
Claude Code
Klein (plugged to Claude)
Supabase (scalable contrairement à MongoDB)
Pinecoin (utile pour mémoire dynamique RAG)


Hyperparameters

https://symbl.ai/developers/blog/a-guide-to-llm-hyperparameters/

La température peut servir à comparer des outputs de « créativité » différente. Par ex, groupe d'agents via Autogen qui se concertent pour une même tâche avec des styles de pensée différents (un rationnel + un créatif + un comparateur etc.)
https://www.hopsworks.ai/dictionary/llm-temperature
Apparemment la temp est majorée à 2 dans les modèles d'OpenAi. Si tu fais le tien, tu pourrais faire joujou.

In a dynamic model selection, memory can be persistent while switching from a model to another (only if you keep handle it with LangGraph etc. and not inside the models themselves). Ask Chat he will show you."""

TEST_DOCUMENT_2 = """Ressources Web

https://www.youtube.com/watch?v=eMlx5fFNoYc&list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi&index=7
(Bête de ressources à la fin + chaîne de contenu strato)

https://www.youtube.com/watch?v=Nqb7JTx0Pqo
Alors lui mon frr il a un niveau terrifiant

https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-10-small-focused-agents.md
Très bons tips en agentique. C'est un vrai cours. Ça commence à l'appendice.

https://www.youtube.com/watch?v=gv0WHhKelSE
Vidéo tuto lecture d'Anthropic sur les best tips pout Claude Code. Les commandes '/', les terminaux en parallèle, la logique interne, CLAUDE.md (possible à chaque étage).

https://situational-awareness.ai
https://situational-awareness.ai/wp-content/uploads/2024/06/situationalawareness.pdf
'Situational Awareness - The Decade Ahead' Essay, Leopold Aschenbrenner (June 2024).


LangGraph

Update v1 Octobre
-> la doc va changer

https://docs.langchain.com/oss/python/integrations/providers
Versions de la librairie pour + de compatibilité // Le J ça instruit


Wow signal
Paradoxe de Fermi


Annales akhashiques


zeitgeist


Lenia - https://chakazul.github.io/lenia.html#Directions
(Conway's Game of Life inspired)


Synergologie


S&P 500 (wiki)


https://fr.wikipedia.org/wiki/Wakan_Tanka
https://fr.glosbe.com/fr/lkt/renne


Make a QR Code :
https://www.youtube.com/watch?v=w5ebcowAJD8

How do GPUs work ?
https://www.youtube.com/watch?v=h9Z4oGN89MU


Trading & Poker :
https://www.youtube.com/watch?v=CamgBXjnSik

Ère piraterie Barbe Noire, boucaniers, flibustiers, Frères de la côté :
https://fr.wikipedia.org/wiki/Boucanier#:~:text=Un%20boucanier%20(de%20boucan%2C%20gril,c'est%2Dà%2Ddire"""

async def test_document_processing():
    """Test document processing with real examples"""

    print("🧪 Testing Document Processing Pipeline\n")
    print("=" * 60)

    # Initialize processor
    processor = DocumentProcessor()

    # Test cases
    test_cases = [
        {
            "name": "Post-it IA Notes #1",
            "content": TEST_DOCUMENT_1,
            "filename": "hackathon_ai_notes.txt"
        },
        {
            "name": "Post-it IA Notes #2",
            "content": TEST_DOCUMENT_2,
            "filename": "web_resources_notes.txt"
        }
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📄 Test Case {i}: {test_case['name']}")
        print("-" * 40)

        # Process document
        try:
            result = processor.process_document(
                content=test_case['content'],
                filename=test_case['filename'],
                file_type="text/plain"
            )

            results.append(result)

            # Display results
            print(f"✅ Title: {result['title']}")
            print(f"📊 Stats: {result['metadata']['word_count']} words, {result['metadata']['char_count']} chars")
            print(f"🏷️  Topics: {', '.join(result['metadata']['topics'][:5])}...")
            print(f"🔗 Links: {len(result['metadata']['links'])} found")
            print(f"📝 Chunks: {len(result['chunks'])} pieces")

            # Show HTML preview (first 200 chars)
            html_preview = result['content_html'][:200] + "..." if len(result['content_html']) > 200 else result['content_html']
            print(f"🌐 HTML Preview: {html_preview}")

            # Show first chunk
            if result['chunks']:
                first_chunk = result['chunks'][0]
                chunk_preview = first_chunk['text'][:150] + "..." if len(first_chunk['text']) > 150 else first_chunk['text']
                print(f"🧩 First Chunk: {chunk_preview}")

        except Exception as e:
            print(f"❌ Error processing: {str(e)}")
            continue

    print(f"\n✅ Processing completed: {len(results)} documents processed")
    return results

async def test_embedding_generation():
    """Test embedding generation (mock without API keys)"""

    print(f"\n🔮 Testing Embedding Generation\n")
    print("=" * 60)

    # Test chunks from processed documents
    test_chunks = [
        "Hackathon Vierzon avec Cursor et v0.dev pour développer des prototypes",
        "Attention Mechanism : Big innovation in ML. Rather than going word by word in order, it would consider a sentence as a whole",
        "Diffusion Models - Article de Kemal Erdem sur les modèles de diffusion avec références aux papiers OpenAI"
    ]

    try:
        # This would normally generate real embeddings
        # For testing without API keys, we simulate
        print("📊 Simulating embedding generation...")

        for i, chunk in enumerate(test_chunks, 1):
            print(f"  {i}. Chunk ({len(chunk)} chars): {chunk[:80]}...")

            # Mock embedding (1536 dimensions of random values for demo)
            mock_embedding = [0.1] * 1536  # In reality this would be the actual embedding
            print(f"     → Generated {len(mock_embedding)}D vector")

        print("✅ Embedding generation test completed")

    except Exception as e:
        print(f"❌ Embedding test error: {str(e)}")

def test_html_output():
    """Test HTML output quality"""

    print(f"\n🌐 Testing HTML Output Quality\n")
    print("=" * 60)

    processor = DocumentProcessor()

    # Test with first document
    result = processor.process_document(
        content=TEST_DOCUMENT_1,
        filename="test_html.txt",
        file_type="text/plain"
    )

    html_content = result['content_html']

    print("📋 HTML Structure Analysis:")

    # Count HTML elements
    import re
    headers = len(re.findall(r'<h[1-6]>', html_content))
    paragraphs = len(re.findall(r'<p>', html_content))
    links = len(re.findall(r'<a href=', html_content))
    lists = len(re.findall(r'<ul>|<ol>', html_content))

    print(f"  📑 Headers: {headers}")
    print(f"  📄 Paragraphs: {paragraphs}")
    print(f"  🔗 Links: {links}")
    print(f"  📋 Lists: {lists}")

    # Show full HTML
    print(f"\n📝 Complete HTML Output:")
    print("-" * 40)
    print(html_content)

    return html_content

def test_toggle_view():
    """Test text/HTML toggle functionality"""

    print(f"\n🔄 Testing Text/HTML Toggle View\n")
    print("=" * 60)

    processor = DocumentProcessor()
    result = processor.process_document(
        content=TEST_DOCUMENT_2,
        filename="toggle_test.txt"
    )

    print("📄 TEXT VIEW:")
    print("-" * 20)
    print(result['content_text'][:300] + "...")

    print(f"\n🌐 HTML VIEW:")
    print("-" * 20)
    print(result['content_html'][:300] + "...")

    print(f"\n✅ Toggle test completed - both views available")

async def main():
    """Run all tests"""

    print("🚀 SCRIBE Document Upload Pipeline Test")
    print("=" * 60)

    # Test 1: Document Processing
    processed_docs = await test_document_processing()

    # Test 2: Embedding Generation (simulated)
    await test_embedding_generation()

    # Test 3: HTML Output Quality
    test_html_output()

    # Test 4: Toggle View Functionality
    test_toggle_view()

    print(f"\n🎉 All tests completed!")
    print(f"📊 Summary: {len(processed_docs)} documents ready for Mimir indexation")
    print("\n🔮 Next steps:")
    print("  1. Set up API keys (OpenAI, Claude, Supabase)")
    print("  2. Run backend server (FastAPI)")
    print("  3. Test frontend upload interface")
    print("  4. Verify Mimir RAG search functionality")

if __name__ == "__main__":
    # Install required dependencies check
    try:
        import markdown
        import bleach
        from bs4 import BeautifulSoup
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Install with: pip install markdown bleach beautifulsoup4")
        sys.exit(1)

    # Run tests
    asyncio.run(main())