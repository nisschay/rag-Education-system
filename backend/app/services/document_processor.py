from io import BytesIO
import re
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Dict

import PyPDF2


class DocumentProcessor:
    def __init__(self):
        # Larger chunks with overlap for better coherence with Gemini
        self.chunk_size = 1000  # words
        self.overlap = 200      # words

    async def extract_text_from_bytes(self, content: bytes, filename: str) -> str:
        """Extract text from file bytes without persisting to disk."""
        ext = filename.lower().split('.')[-1]

        if ext == 'pdf':
            return await self._extract_pdf_bytes(content)
        if ext == 'docx':
            return await self._extract_docx_bytes(content)
        if ext == 'pptx':
            return await self._extract_pptx_bytes(content)

        raise ValueError(f"Unsupported file type: {ext}")

    async def _extract_pdf_bytes(self, content: bytes) -> str:
        """Extract text from PDF bytes."""
        reader = PyPDF2.PdfReader(BytesIO(content))
        text_parts: List[str] = []

        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            text_parts.append(f"\n--- Page {page_num + 1} ---\n{page_text}")

        return "".join(text_parts)

    async def _extract_docx_bytes(self, content: bytes) -> str:
        """Extract text from DOCX bytes."""
        text_parts: List[str] = []
        with zipfile.ZipFile(BytesIO(content)) as docx:
            xml_content = docx.read('word/document.xml')
            root = ET.fromstring(xml_content)
            for elem in root.iter():
                if elem.text:
                    text_parts.append(elem.text)
        return " ".join(text_parts)

    async def _extract_pptx_bytes(self, content: bytes) -> str:
        """Extract text from PPTX bytes."""
        text_parts: List[str] = []
        with zipfile.ZipFile(BytesIO(content)) as pptx:
            for name in pptx.namelist():
                if name.startswith('ppt/slides/slide') and name.endswith('.xml'):
                    xml_content = pptx.read(name)
                    root = ET.fromstring(xml_content)
                    for elem in root.iter():
                        if elem.text and elem.text.strip():
                            text_parts.append(elem.text.strip())
        return "\n".join(text_parts)

    def create_semantic_chunks(self, text: str, metadata: Dict) -> List[Dict]:
        """Create sentence-aware overlapping chunks for embeddings."""
        cleaned = re.sub(r"\s+", " ", text).strip()
        sentences = re.split(r'(?<=[.!?])\s+', cleaned)

        chunks: List[Dict] = []
        current_chunk: List[str] = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence.split())

            if current_length + sentence_length > self.chunk_size:
                if current_chunk:
                    chunk_text = ' '.join(current_chunk)
                    chunks.append({
                        "content": chunk_text,
                        "metadata": {**metadata, "chunk_index": len(chunks)}
                    })

                # Maintain overlap to preserve context
                overlap_words = self.overlap
                current_chunk = current_chunk[-overlap_words:] if overlap_words > 0 else []
                current_length = len(' '.join(current_chunk).split())

            current_chunk.append(sentence)
            current_length += sentence_length

        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                "content": chunk_text,
                "metadata": {**metadata, "chunk_index": len(chunks)}
            })

        return chunks


document_processor = DocumentProcessor()
