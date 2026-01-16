# -*- coding: utf-8 -*-
"""Document loading and chunking for RAG - Universal File Support"""
import os
from pathlib import Path
from typing import List, Dict, Any
import PyPDF2

class Document:
    """Represents a document chunk with content and metadata"""
    def __init__(self, content: str, metadata: Dict[str, Any] = None):
        self.content = content
        self.metadata = metadata or {}
    
    @property
    def page_content(self):
        """Alias for content - compatibility with LangChain-style documents"""
        return self.content
    
    def __repr__(self):
        return f"Document(content={self.content[:50]}..., metadata={self.metadata})"

class DocumentLoader:
    """Load and process documents - PDF, Word, Markdown, and Text support"""
    
    # Supported file types (non-MD files will be converted to MD)
    SUPPORTED_EXTENSIONS = {'.pdf', '.md', '.markdown', '.txt', '.doc', '.docx'}
    
    def __init__(self, documents_dir: Path, chunk_size: int = 500, chunk_overlap: int = 50):
        self.documents_dir = Path(documents_dir)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def load_all_documents(self) -> List[Document]:
        """Load all documents from the documents directory"""
        documents = []
        
        if not self.documents_dir.exists():
            print(f"Documents directory not found: {self.documents_dir}")
            return documents
        
        for file_path in self.documents_dir.iterdir():
            if file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                try:
                    docs = self.load_document(file_path)
                    documents.extend(docs)
                    print(f"Loaded {len(docs)} chunks from {file_path.name}")
                except Exception as e:
                    print(f"Error loading {file_path.name}: {e}")
        
        print(f"Total documents loaded: {len(documents)} chunks")
        return documents
    
    def load_document(self, file_path: Path, category: str = None) -> List[Document]:
        """Load a single document and split into chunks
        
        Args:
            file_path: Path to the document file
            category: Optional category for the document (e.g., 'beasiswa', 'panduan_krs')
        """
        file_path = Path(file_path)
        ext = file_path.suffix.lower()
        
        # Route to appropriate loader
        if ext == '.pdf':
            content = self._load_pdf(file_path)
        elif ext in {'.docx', '.doc'}:
            content = self._load_docx(file_path)
        elif ext in {'.pptx', '.ppt'}:
            content = self._load_pptx(file_path)
        elif ext in {'.xlsx', '.xls'}:
            content = self._load_xlsx(file_path)
        elif ext in {'.html', '.htm'}:
            content = self._load_html(file_path)
        elif ext == '.csv':
            content = self._load_csv(file_path)
        elif ext == '.json':
            content = self._load_json(file_path)
        else:
            # Default: treat as text
            content = self._load_text(file_path)
        
        chunks = self._split_text(content)
        
        return [
            Document(
                content=chunk,
                metadata={
                    'source': file_path.name,
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'original_type': ext,
                    'category': category or 'uncategorized'
                }
            )
            for i, chunk in enumerate(chunks)
        ]
    
    def convert_to_markdown(self, file_path: Path, output_dir: Path = None) -> Path:
        """
        Convert any supported file to Markdown format.
        
        Args:
            file_path: Path to the file (PDF, DOCX, TXT)
            output_dir: Directory to save the markdown file (defaults to same as source)
        
        Returns:
            Path to the created markdown file
        """
        file_path = Path(file_path)
        output_dir = output_dir or file_path.parent
        ext = file_path.suffix.lower()
        
        # Skip if already markdown
        if ext in {'.md', '.markdown'}:
            return file_path
        
        # Extract text based on file type
        if ext == '.pdf':
            text = self._load_pdf(file_path)
        elif ext in {'.doc', '.docx'}:
            text = self._load_docx(file_path)
        elif ext == '.txt':
            text = self._load_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
        
        if not text or len(text.strip()) < 10:
            raise ValueError(f"Could not extract text from: {file_path.name}")
        
        # Convert to Markdown format
        md_content = self._text_to_markdown(text, file_path.stem)
        
        # Save as markdown file
        md_filename = file_path.stem + '.md'
        md_path = output_dir / md_filename
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"✅ Converted {file_path.name} → {md_filename} ({len(md_content)} chars)")
        return md_path
    
    def convert_pdf_to_markdown(self, pdf_path: Path, output_dir: Path = None) -> Path:
        """Alias for convert_to_markdown for backward compatibility"""
        return self.convert_to_markdown(pdf_path, output_dir)
    
    def _text_to_markdown(self, text: str, title: str) -> str:
        """
        Convert raw text to a structured Markdown format.
        
        Args:
            text: Raw text from PDF
            title: Document title (usually filename without extension)
        
        Returns:
            Formatted markdown string
        """
        import re
        
        # Clean up the text
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                cleaned_lines.append('')
                continue
            
            # Remove excessive whitespace
            line = ' '.join(line.split())
            
            # Detect potential headers (all caps, short lines)
            if line.isupper() and len(line) < 80 and len(line) > 3:
                # Convert to header
                line = f"## {line.title()}"
            
            # Detect numbered lists
            if re.match(r'^\d+[.\)]\s', line):
                line = re.sub(r'^(\d+)[.\)]\s', r'\1. ', line)
            
            # Detect bullet points
            if line.startswith(('- ', '• ', '* ', '○ ')):
                line = '- ' + line[2:]
            
            cleaned_lines.append(line)
        
        # Join lines and fix multiple blank lines
        content = '\n'.join(cleaned_lines)
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Add document header
        header = f"# {title.replace('_', ' ').title()}\n\n"
        header += f"*Dokumen ini dikonversi otomatis dari PDF*\n\n---\n\n"
        
        return header + content.strip()
    
    def _convert_table_to_markdown(self, table: list) -> str:
        """
        Convert table data (list of rows) to markdown format.
        
        Args:
            table: List of rows, where each row is a list of cell values
        
        Returns:
            Markdown formatted table string
        """
        if not table or len(table) < 1:
            return ""
        
        # Clean cells - remove None and strip whitespace
        cleaned_table = []
        for row in table:
            cleaned_row = [str(cell or '').strip().replace('\n', ' ') for cell in row]
            cleaned_table.append(cleaned_row)
        
        if not cleaned_table:
            return ""
        
        # Determine max columns
        max_cols = max(len(row) for row in cleaned_table)
        
        # Normalize rows to have same number of columns
        for row in cleaned_table:
            while len(row) < max_cols:
                row.append('')
        
        # Header row
        header = cleaned_table[0]
        md_lines = ["| " + " | ".join(header) + " |"]
        md_lines.append("|" + "|".join(["---"] * len(header)) + "|")
        
        # Data rows
        for row in cleaned_table[1:]:
            md_lines.append("| " + " | ".join(row) + " |")
        
        return "\n".join(md_lines)
    
    def _extract_tables_from_pdf(self, file_path: Path) -> list:
        """
        Extract tables from PDF and convert to markdown format.
        
        Args:
            file_path: Path to the PDF file
        
        Returns:
            List of markdown formatted table strings
        """
        tables_md = []
        
        try:
            import pdfplumber
            with pdfplumber.open(str(file_path)) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    tables = page.extract_tables()
                    for table_idx, table in enumerate(tables):
                        if table and len(table) > 1:
                            md_table = self._convert_table_to_markdown(table)
                            if md_table:
                                tables_md.append(f"\n### Tabel (Halaman {page_num}, #{table_idx + 1})\n\n{md_table}\n")
            
            if tables_md:
                print(f"Extracted {len(tables_md)} tables from {file_path.name}")
        except ImportError:
            print("pdfplumber not installed for table extraction")
        except Exception as e:
            print(f"Error extracting tables from PDF: {e}")
        
        return tables_md
    
    def _extract_tables_from_docx(self, doc) -> list:
        """
        Extract tables from DOCX document and convert to markdown.
        
        Args:
            doc: python-docx Document object
        
        Returns:
            List of markdown formatted table strings
        """
        tables_md = []
        
        try:
            for table_idx, table in enumerate(doc.tables):
                rows = []
                for row in table.rows:
                    cells = [cell.text.strip() for cell in row.cells]
                    rows.append(cells)
                
                if rows and len(rows) > 1:
                    md_table = self._convert_table_to_markdown(rows)
                    if md_table:
                        tables_md.append(f"\n### Tabel #{table_idx + 1}\n\n{md_table}\n")
            
            if tables_md:
                print(f"Extracted {len(tables_md)} tables from DOCX")
        except Exception as e:
            print(f"Error extracting tables from DOCX: {e}")
        
        return tables_md
    
    def _detect_and_format_formulas(self, text: str) -> str:
        """
        Detect and format mathematical formulas in text.
        
        Args:
            text: Raw text that may contain formulas
        
        Returns:
            Text with formatted formulas
        """
        import re
        
        # Pattern untuk rumus dengan format "NAMA = formula"
        # Contoh: IPS = Σ(SKS x Bobot) / Σ SKS
        patterns = [
            # Format rumus dengan sama dengan
            (r'([A-Z]{2,})\s*=\s*([^\n]+)', r'**\1** = `\2`'),
            # Simbol sigma
            (r'Σ\s*\(([^)]+)\)', r'Σ(\1)'),
            # Perkalian
            (r'(\d+)\s*[xX×]\s*(\d+)', r'\1 × \2'),
            # Pembagian dengan kata
            (r'\)\s*/\s*Σ', r') ÷ Σ'),
        ]
        
        for pattern, replacement in patterns:
            try:
                text = re.sub(pattern, replacement, text)
            except Exception:
                pass
        
        return text

    def _load_pdf(self, file_path: Path) -> str:
        """Load PDF file with OCR support for scanned documents and table extraction"""
        text = ""
        tables_md = []
        
        # First try pdfplumber for text-based PDFs
        try:
            import pdfplumber
            with pdfplumber.open(str(file_path)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text and len(page_text.strip()) > 50:
                        text += page_text + "\n\n"
            
            # If we got substantial text, also extract tables
            if len(text.strip()) > 200:
                print(f"Extracted {len(text)} chars from {file_path.name} using pdfplumber")
                
                # Extract tables separately
                tables_md = self._extract_tables_from_pdf(file_path)
                
                # Apply formula formatting
                text = self._detect_and_format_formulas(text)
                
                # Append tables to the end of the text
                if tables_md:
                    text += "\n\n## Tabel yang Diekstrak\n" + "\n".join(tables_md)
                
                return text
        except Exception as e:
            print(f"pdfplumber failed: {e}")
        
        # Fallback to OCR for scanned PDFs
        print(f"Trying OCR for {file_path.name}...")
        try:
            from pdf2image import convert_from_path
            import pytesseract
            
            # Convert PDF pages to images
            images = convert_from_path(str(file_path), dpi=150)
            
            ocr_text = ""
            for i, image in enumerate(images):
                # OCR each page
                page_text = pytesseract.image_to_string(image, lang='ind+eng')
                if page_text.strip():
                    ocr_text += f"--- Halaman {i+1} ---\n{page_text}\n\n"
            
            if ocr_text.strip():
                print(f"OCR extracted {len(ocr_text)} chars from {file_path.name}")
                return self._detect_and_format_formulas(ocr_text)
                
        except ImportError as e:
            print(f"OCR not available: {e}")
            print("Install with: pip install pytesseract pdf2image")
            print("Also install Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki")
        except Exception as e:
            print(f"OCR failed: {e}")
        
        # Final fallback to PyPDF2
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"PyPDF2 failed: {e}")
        
        return self._detect_and_format_formulas(text)
    
    def _load_docx(self, file_path: Path) -> str:
        """Load DOCX file with table extraction"""
        try:
            from docx import Document as DocxDocument
            doc = DocxDocument(str(file_path))
            
            # Extract paragraphs
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            text = "\n\n".join(paragraphs)
            
            # Extract tables
            tables_md = self._extract_tables_from_docx(doc)
            
            # Apply formula formatting
            text = self._detect_and_format_formulas(text)
            
            # Append tables
            if tables_md:
                text += "\n\n## Tabel yang Diekstrak\n" + "\n".join(tables_md)
            
            return text
        except ImportError:
            print("python-docx not installed. Install with: pip install python-docx")
            return self._load_text_fallback(file_path)
        except Exception as e:
            print(f"Error reading DOCX {file_path.name}: {e}")
            return ""
    
    def _load_pptx(self, file_path: Path) -> str:
        """Load PPTX file"""
        try:
            from pptx import Presentation
            prs = Presentation(str(file_path))
            text_parts = []
            for slide_num, slide in enumerate(prs.slides, 1):
                slide_text = []
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        slide_text.append(shape.text)
                if slide_text:
                    text_parts.append(f"## Slide {slide_num}\n" + "\n".join(slide_text))
            return "\n\n".join(text_parts)
        except ImportError:
            print("python-pptx not installed. Install with: pip install python-pptx")
            return ""
        except Exception as e:
            print(f"Error reading PPTX {file_path.name}: {e}")
            return ""
    
    def _load_xlsx(self, file_path: Path) -> str:
        """Load XLSX file"""
        try:
            import pandas as pd
            # Read all sheets
            xlsx = pd.ExcelFile(file_path)
            text_parts = []
            for sheet_name in xlsx.sheet_names:
                df = pd.read_excel(xlsx, sheet_name=sheet_name)
                text_parts.append(f"## Sheet: {sheet_name}\n")
                text_parts.append(df.to_markdown(index=False))
            return "\n\n".join(text_parts)
        except ImportError:
            print("pandas/openpyxl not installed. Install with: pip install pandas openpyxl")
            return ""
        except Exception as e:
            print(f"Error reading XLSX {file_path.name}: {e}")
            return ""
    
    def _load_html(self, file_path: Path) -> str:
        """Load HTML file and convert to text"""
        try:
            from bs4 import BeautifulSoup
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                return soup.get_text(separator='\n')
        except ImportError:
            print("beautifulsoup4 not installed. Install with: pip install beautifulsoup4")
            return self._load_text(file_path)
        except Exception as e:
            print(f"Error reading HTML {file_path.name}: {e}")
            return self._load_text(file_path)
    
    def _load_csv(self, file_path: Path) -> str:
        """Load CSV file"""
        try:
            import pandas as pd
            df = pd.read_csv(file_path)
            return df.to_markdown(index=False)
        except Exception as e:
            print(f"Error reading CSV {file_path.name}: {e}")
            return self._load_text(file_path)
    
    def _load_json(self, file_path: Path) -> str:
        """Load JSON file"""
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return json.dumps(data, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error reading JSON {file_path.name}: {e}")
            return self._load_text(file_path)
    
    def _load_text(self, file_path: Path) -> str:
        """Load plain text file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading text {file_path.name}: {e}")
            return ""
    
    def _load_text_fallback(self, file_path: Path) -> str:
        """Fallback text loader for binary files"""
        return ""
    
    def _split_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks using semantic chunking.
        
        Uses LangChain's RecursiveCharacterTextSplitter which:
        1. Splits by sentence/paragraph boundaries first
        2. Falls back to smaller separators if needed
        3. Properly implements overlap between chunks
        """
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
        except ImportError:
            # Fallback for older langchain versions
            from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        # Clean text
        text = text.strip()
        if not text:
            return []
        
        # Create semantic text splitter
        # Separators are tried in order - prefers paragraph > sentence > word boundaries
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            is_separator_regex=False,
            separators=[
                "\n\n",      # Paragraphs (highest priority)
                "\n",        # Lines
                ". ",        # Sentences
                "? ",        # Questions
                "! ",        # Exclamations
                "; ",        # Semicolons
                ", ",        # Commas
                " ",         # Words
                ""           # Characters (last resort)
            ]
        )
        
        # Split the text
        chunks = text_splitter.split_text(text)
        
        print(f"   Semantic chunking: {len(text)} chars → {len(chunks)} chunks "
              f"(size={self.chunk_size}, overlap={self.chunk_overlap})")
        
        return chunks

