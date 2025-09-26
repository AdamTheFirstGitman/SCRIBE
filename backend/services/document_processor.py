"""
Document Processing Service
Handles file upload, text-to-HTML conversion, and preparation for Mimir indexation
"""

import re
import html
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import markdown
from markdown.extensions import codehilite, fenced_code, tables, toc
import bleach
from bs4 import BeautifulSoup
import uuid

class DocumentProcessor:
    """
    Processes uploaded text documents for SCRIBE system
    Converts plain text to semantic HTML for dual viewing
    """

    def __init__(self):
        self.allowed_tags = [
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'p', 'br', 'strong', 'em', 'u', 'strike',
            'ul', 'ol', 'li', 'blockquote', 'code', 'pre',
            'a', 'table', 'thead', 'tbody', 'tr', 'td', 'th',
            'div', 'span', 'section', 'article'
        ]
        self.allowed_attributes = {
            'a': ['href', 'title'],
            'code': ['class'],
            'pre': ['class'],
            'div': ['class'],
            'span': ['class'],
            'h1': ['id'], 'h2': ['id'], 'h3': ['id'],
            'h4': ['id'], 'h5': ['id'], 'h6': ['id']
        }

    def process_document(self, content: str, filename: str, file_type: str = "text/plain") -> Dict:
        """
        Main processing pipeline for uploaded documents

        Args:
            content: Raw text content
            filename: Original filename
            file_type: MIME type

        Returns:
            Dict with processed content and metadata
        """
        # Generate title from filename or first line
        title = self._extract_title(content, filename)

        # Convert to HTML based on content type
        if file_type == "text/markdown" or filename.endswith('.md'):
            html_content = self._markdown_to_html(content)
        else:
            html_content = self._text_to_html(content)

        # Extract metadata and structure
        metadata = self._extract_metadata(content, html_content)

        # Prepare for chunking
        chunks = self._prepare_chunks(content)

        return {
            "title": title,
            "content_text": content,
            "content_html": html_content,
            "filename": filename,
            "file_type": file_type,
            "file_size": len(content.encode('utf-8')),
            "metadata": metadata,
            "chunks": chunks,
            "processing_status": "completed"
        }

    def _extract_title(self, content: str, filename: str) -> str:
        """Extract or generate document title"""
        lines = content.strip().split('\n')

        # Try to find title in first few lines
        for line in lines[:3]:
            line = line.strip()
            if line:
                # Remove markdown headers
                title = re.sub(r'^#+\s*', '', line)
                if len(title) > 5 and len(title) < 100:
                    return title

        # Fallback to filename without extension
        return Path(filename).stem.replace('_', ' ').replace('-', ' ').title()

    def _text_to_html(self, text: str) -> str:
        """
        Convert plain text to semantic HTML
        Handles your note format with smart paragraph detection
        """
        lines = text.split('\n')
        html_parts = []
        current_section = []

        for line in lines:
            line = line.strip()

            if not line:  # Empty line - section break
                if current_section:
                    html_parts.append(self._process_text_section(current_section))
                    current_section = []
                continue

            # Detect headers (lines that look like titles)
            if self._is_header_line(line):
                if current_section:
                    html_parts.append(self._process_text_section(current_section))
                    current_section = []
                html_parts.append(f"<h2>{html.escape(line)}</h2>")
            else:
                current_section.append(line)

        # Process remaining section
        if current_section:
            html_parts.append(self._process_text_section(current_section))

        return f'<article>{"".join(html_parts)}</article>'

    def _is_header_line(self, line: str) -> bool:
        """Detect if a line should be a header"""
        # Short lines that aren't URLs and don't end with punctuation
        if (len(line) < 50 and
            not line.startswith('http') and
            not line.endswith(('.', '?', '!', ',', ';')) and
            not '->' in line and
            len(line.split()) <= 8):
            return True
        return False

    def _process_text_section(self, lines: List[str]) -> str:
        """Process a section of related lines"""
        if not lines:
            return ""

        content = ' '.join(lines)

        # Check if it's a list (multiple lines with similar structure)
        if len(lines) > 1 and all(self._looks_like_list_item(line) for line in lines):
            items = [f"<li>{html.escape(line)}</li>" for line in lines]
            return f'<ul>{"".join(items)}</ul>'

        # Single paragraph with link detection and formatting
        formatted_content = self._format_inline_content(content)
        return f"<p>{formatted_content}</p>"

    def _looks_like_list_item(self, line: str) -> bool:
        """Check if line looks like a list item"""
        # URLs, short descriptive lines, or lines with separators
        return (line.startswith('http') or
                len(line) < 80 or
                ' - ' in line or
                ' : ' in line)

    def _format_inline_content(self, text: str) -> str:
        """Format inline content with links and emphasis"""
        # Escape HTML first
        text = html.escape(text)

        # Convert URLs to links
        url_pattern = r'(https?://[^\s]+)'
        text = re.sub(url_pattern, r'<a href="\1" target="_blank" rel="noopener">\1</a>', text)

        # Convert parenthetical references to emphasis
        text = re.sub(r'\(([^)]+)\)', r'<em>(\1)</em>', text)

        # Bold for specific patterns (author names, etc.)
        text = re.sub(r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b', r'<strong>\1</strong>', text)

        return text

    def _markdown_to_html(self, markdown_content: str) -> str:
        """Convert Markdown to clean HTML"""
        md = markdown.Markdown(extensions=[
            'fenced_code',
            'codehilite',
            'tables',
            'toc',
            'nl2br'
        ])

        html_content = md.convert(markdown_content)

        # Clean and sanitize
        return bleach.clean(
            html_content,
            tags=self.allowed_tags,
            attributes=self.allowed_attributes,
            strip=True
        )

    def _extract_metadata(self, text: str, html: str) -> Dict:
        """Extract metadata from content"""
        soup = BeautifulSoup(html, 'html.parser')

        # Count elements
        word_count = len(text.split())
        char_count = len(text)

        # Extract links
        links = [a.get('href') for a in soup.find_all('a', href=True)]

        # Extract headers for TOC
        headers = [h.get_text() for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])]

        # Detect topics/keywords (simplified)
        topics = self._extract_topics(text)

        return {
            "word_count": word_count,
            "char_count": char_count,
            "links": links,
            "headers": headers,
            "topics": topics,
            "has_code": bool(soup.find('code') or soup.find('pre')),
            "has_links": len(links) > 0,
            "has_structure": len(headers) > 0
        }

    def _extract_topics(self, text: str) -> List[str]:
        """Extract potential topics/keywords from text"""
        # Simple keyword extraction based on your examples
        topics = []

        # Technology keywords
        tech_keywords = [
            'AI', 'LLM', 'RAG', 'GPT', 'Claude', 'OpenAI', 'Anthropic',
            'Python', 'JavaScript', 'React', 'NextJS', 'FastAPI',
            'Machine Learning', 'Deep Learning', 'NLP', 'Vector', 'Embedding',
            'Hackathon', 'API', 'Database', 'PostgreSQL', 'Redis'
        ]

        text_upper = text.upper()
        for keyword in tech_keywords:
            if keyword.upper() in text_upper:
                topics.append(keyword)

        # Extract URLs as topics
        urls = re.findall(r'https?://([^/\s]+)', text)
        domains = [url.split('.')[0] for url in urls]
        topics.extend(domains)

        return list(set(topics))[:10]  # Limit to 10 topics

    def _prepare_chunks(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[Dict]:
        """
        Prepare text chunks for embedding generation
        Smart chunking that preserves semantic boundaries
        """
        chunks = []

        # Split by paragraphs first
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

        current_chunk = ""
        chunk_index = 0

        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size
            if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
                # Save current chunk
                chunks.append({
                    "index": chunk_index,
                    "text": current_chunk.strip(),
                    "char_count": len(current_chunk),
                    "word_count": len(current_chunk.split())
                })

                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk, overlap)
                current_chunk = overlap_text + paragraph
                chunk_index += 1
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph

        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                "index": chunk_index,
                "text": current_chunk.strip(),
                "char_count": len(current_chunk),
                "word_count": len(current_chunk.split())
            })

        return chunks

    def _get_overlap_text(self, text: str, overlap_size: int) -> str:
        """Get overlap text from end of chunk"""
        if len(text) <= overlap_size:
            return text

        # Try to break at sentence boundary
        overlap_text = text[-overlap_size:]
        sentence_end = overlap_text.find('. ')
        if sentence_end > 0:
            return overlap_text[sentence_end + 2:]

        # Fallback to word boundary
        words = overlap_text.split()
        return ' '.join(words[1:]) if len(words) > 1 else overlap_text

# Example usage for your test cases
if __name__ == "__main__":
    processor = DocumentProcessor()

    # Test with your hackathon notes
    test_content = """Hackathon Vierzon
Cursor
v0.dev

Hackathon LLMxLaw (Station F)
Ressources (cf. mail avant hackathon) Koyeb, LlamaIndex, Together.ai, etc. https://koyeb.notion.site/Koyeb-Resources-for-LLM-x-Law-Hackathon-at-Station-F-13f914392cfe80bebf22d7b0b2fff722

Attention Mechanism
Big innovation in ML. Rather than going word by word in order, it would consider a sentence as a whole and gives more relevant weighs depending on the whole context.
https://aigents.co/learn/Attention-mechanism"""

    result = processor.process_document(test_content, "hackathon_notes.txt")
    print("HTML Output:")
    print(result["content_html"])
    print("\nMetadata:")
    print(result["metadata"])