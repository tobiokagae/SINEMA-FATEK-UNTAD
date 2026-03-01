# -*- coding: utf-8 -*-
"""Document loading and chunking for RAG - Universal File Support"""
import os
import re
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
        
        # Collect all files (non-recursive, skip subdirectories like raw/)
        files = [f for f in self.documents_dir.iterdir() if f.is_file()]
        
        # Track MD stems to skip duplicate PDF/DOCX files
        md_stems = {f.stem for f in files if f.suffix.lower() in {'.md', '.markdown'}}
        
        for file_path in files:
            if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                continue
            
            # Skip PDF/DOCX if a corresponding .md file exists (prevent double chunking)
            if file_path.suffix.lower() in {'.pdf', '.docx', '.doc'} and file_path.stem in md_stems:
                print(f"Skipping {file_path.name} (MD version exists)")
                continue
            
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

        # Auto-detect category from filename if not provided
        if category is None or category == 'uncategorized':
            category = self._detect_category_from_filename(file_path.name)

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

        documents = []
        for i, chunk in enumerate(chunks):
            # Extract heading and snippet for source citation
            heading = self._extract_heading(chunk, content)
            snippet = self._extract_snippet(chunk)

            documents.append(Document(
                content=chunk,
                metadata={
                    'source': file_path.name,
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'original_type': ext,
                    'category': category,
                    'heading': heading,
                    'snippet': snippet
                }
            ))

        return documents

    def _detect_category_from_filename(self, filename: str) -> str:
        """Auto-detect document category from filename for better retrieval

        Args:
            filename: Name of the document file

        Returns:
            Detected category string
        """
        filename_lower = filename.lower()

        # Keyword-based category detection
        categories = {
            'poin_ekstrakurikuler': ['poin', 'ekstrakurikuler', 'spe'],
            'panduan_akademik': ['panduan', 'akademik', 'buku_panduan'],
            'ta_skripsi': ['skripsi', 'ta_skripsi'],
            'ta_non_skripsi': ['ta_non_skripsi', 'non_skripsi'],
            'website_sinema': ['sinema', 'website'],
            'integritas': ['integritas', 'plagiarisme'],
            'transkrip_tem': ['transkrip', 'tem'],
        }

        for category, keywords in categories.items():
            if any(keyword in filename_lower for keyword in keywords):
                return category

        return 'general'
    
    def _extract_heading(self, chunk: str, full_content: str) -> str:
        """Extract the nearest heading/section for a chunk.
        
        Looks for markdown headings (## or ###) in the chunk or preceding content.
        """
        import re
        
        # First try to find heading in the chunk itself
        heading_patterns = [
            r'^#{1,3}\s+(.+)$',  # Markdown headings
            r'^(BAB\s+[IVX\d]+[.:]\s*.+)$',  # BAB format
            r'^(\d+\.\d*\s+[A-Z].+)$',  # Numbered sections like "7.1 Tugas Akhir"
            r'^(Pasal\s+\d+.*)$',  # Pasal format
        ]
        
        for line in chunk.split('\n'):
            stripped = line.strip()
            for pattern in heading_patterns:
                match = re.match(pattern, stripped, re.IGNORECASE | re.MULTILINE)
                if match:
                    heading = match.group(1).strip()
                    # Clean up heading
                    heading = re.sub(r'^#+\s*', '', heading)
                    return heading[:80]  # Limit length
        
        # If no heading in chunk, look for the preceding heading in full content
        try:
            chunk_start = full_content.find(chunk[:50])
            if chunk_start > 0:
                preceding = full_content[:chunk_start]
                # Find the last heading before this chunk
                for pattern in heading_patterns:
                    matches = list(re.finditer(pattern, preceding, re.IGNORECASE | re.MULTILINE))
                    if matches:
                        heading = matches[-1].group(1).strip()
                        heading = re.sub(r'^#+\s*', '', heading)
                        return heading[:80]
        except Exception:
            pass
        
        return ''
    
    def _extract_snippet(self, chunk: str) -> str:
        """Extract a clean snippet preview from chunk content."""
        # Remove markdown formatting
        import re
        snippet = chunk.strip()
        snippet = re.sub(r'^#+\s+', '', snippet)  # Remove heading markers
        snippet = re.sub(r'\*+([^*]+)\*+', r'\1', snippet)  # Remove bold/italic
        snippet = re.sub(r'\s+', ' ', snippet)  # Normalize whitespace
        
        # Take first 60 characters
        if len(snippet) > 60:
            snippet = snippet[:57] + '...'
        
        return snippet
    
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
        
        print(f"[OK] Converted {file_path.name} -> {md_filename} ({len(md_content)} chars)")
        return md_path
    
    def convert_pdf_to_markdown(self, pdf_path: Path, output_dir: Path = None) -> Path:
        """Alias for convert_to_markdown for backward compatibility"""
        return self.convert_to_markdown(pdf_path, output_dir)
    
    def _text_to_markdown(self, text: str, title: str) -> str:
        """
        Convert raw text to a structured Markdown format.
        Includes cleaning of unnecessary sections like page numbers, TOC, etc.
        
        Args:
            text: Raw text from PDF
            title: Document title (usually filename without extension)
        
        Returns:
            Formatted markdown string (cleaned and ready for chunking)
        """
        import re
        
        # Step 1: Remove page numbers with surrounding blank lines FIRST
        # Pattern: detect standalone page numbers (1-3 digits or roman numerals)
        text = re.sub(r'\n\s*\n\s*(\d{1,3})\s*\n\s*\n', '\n', text)  # Number between blanks
        text = re.sub(r'\n\s*(\d{1,3})\s*\n\s*\n', '\n', text)  # Number followed by blank
        text = re.sub(r'\n\s*\n\s*(\d{1,3})\s*\n', '\n', text)  # Number preceded by blank
        text = re.sub(r'\n\s*(\d{1,3})\s*\n', '\n', text)  # Just page number line
        
        # Also handle roman numerals
        text = re.sub(r'\n\s*\n\s*([ivxlc]+)\s*\n\s*\n', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'\n\s*([ivxlc]+)\s*\n', '\n', text, flags=re.IGNORECASE)
        
        # Clean up the text line by line
        lines = text.split('\n')
        cleaned_lines = []
        
        # Patterns for sections to skip entirely
        skip_section_patterns = [
            r'^DAFTAR\s+(ISI|TABEL|GAMBAR|LAMPIRAN)',
            r'^KATA\s+PENGANTAR',
            r'^SAMBUTAN',
            r'^SUSUNAN\s+(PANITIA|TIM|PENYUSUN)',
            r'^TIM\s+PENYUSUN',
            r'^DAFTAR\s+PIMPINAN',
            r'^HALAMAN\s+PENGESAHAN',
            r'^COVER$',
            r'^LEMBAR\s+(PENGESAHAN|PERSETUJUAN)',
        ]
        
        skip_until_next_section = False
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines at the start
            if not stripped and not cleaned_lines:
                continue
            
            # Check if this line starts a section to skip
            for pattern in skip_section_patterns:
                if re.match(pattern, stripped, re.IGNORECASE):
                    skip_until_next_section = True
                    break
            
            # Check if we've hit a new major section (ends the skip)
            if skip_until_next_section:
                # A new major section starts with BAB, Pasal, or numbered section
                if re.match(r'^(BAB|Pasal|\d+\.(\d+\.)?)\s+\w', stripped, re.IGNORECASE):
                    skip_until_next_section = False
                else:
                    continue  # Skip this line
            
            # Skip standalone page numbers (backup)
            if re.match(r'^(\d{1,3}|[ivxlc]+)$', stripped, re.IGNORECASE):
                continue
            
            # Skip TOC-style entries with dots (e.g., "7.3. Seminar Proposal ......... 57")
            if re.match(r'^[\d.]+\s+\w+.*[.]{3,}\s*\d+$', stripped):
                continue
            
            # Skip lines that are just page markers with dots
            if re.match(r'^[.\s]+\d+$', stripped):
                continue
            
            # Remove excessive whitespace
            if stripped:
                stripped = ' '.join(stripped.split())
                
                # Detect potential headers (all caps, short lines)
                # Use stricter validation to avoid turning data into headings
                if stripped.isupper() and len(stripped) < 80 and len(stripped) > 3 and self._is_valid_heading(stripped):
                    stripped = f"## {stripped.title()}"
                
                # Detect numbered sub-chapter headings: "1.1 PENGERTIAN TUGAS AKHIR", "3.1 Proyek", "1.1. Sejarah"
                # Pattern: {digit}.{digit}[.{digit}][.] followed by text starting with uppercase
                # Trailing dot is optional to handle both "1.1 Text" and "1.1. Text" formats
                elif re.match(r'^\d+\.\d+(\.\d+)?\.?\s+[A-Z]', stripped) and len(stripped) < 100:
                    section_match = re.match(r'^(\d+\.\d+(?:\.\d+)?\.?)\s+(.+)$', stripped)
                    if section_match:
                        sec_num = section_match.group(1)
                        sec_text = section_match.group(2)
                        # Accept as heading if text is short (not a full sentence)
                        # Full sentences typically have commas, "yang", "untuk", etc. and are long
                        if len(sec_text) < 80:
                            stripped = f"## {sec_num} {sec_text.title()}"
                
                # Detect numbered lists (but not section headings we just converted)
                if not stripped.startswith('## ') and re.match(r'^\d+[.\)]\s', stripped):
                    stripped = re.sub(r'^(\d+)[.\)]\s', r'\1. ', stripped)
                
                # Detect bullet points
                if stripped.startswith(('- ', '• ', '* ', '○ ')):
                    stripped = '- ' + stripped[2:]
            
            cleaned_lines.append(stripped if stripped else '')
        
        # Join lines and fix multiple blank lines
        content = '\n'.join(cleaned_lines)
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Auto-detect and format inline tables
        content = self._detect_and_format_inline_tables(content)
        
        # Add document header
        header = f"# {title.replace('_', ' ').title()}\n\n"
        header += f"*Dokumen ini dikonversi dan dibersihkan otomatis*\n\n---\n\n"
        
        return header + content.strip()
    
    def _is_valid_heading(self, text: str) -> bool:
        """
        Check if an uppercase line is actually a heading (BAB, section title)
        vs data that happens to be uppercase (NIP, table values, abbreviations).
        
        Returns True if the text looks like a real heading.
        """
        # Contains long numbers (NIP, phone numbers, SK numbers)
        if re.search(r'\d{5,}', text):
            return False
        
        # Starts with numbers/scores (table data like "85,01 - 100 A 4,00")
        if re.match(r'^\d[\d,.\s\-]+', text):
            return False
        
        # Too short — likely abbreviation like "(MKWK)" or "IPS"
        words = text.split()
        if len(words) <= 1 and len(text) < 6:
            return False
        
        # Wrapped in parentheses — abbreviation like "(MKWK)."
        if re.match(r'^\(.*\)\.?$', text.strip()):
            return False
        
        # Contains formula/code characters
        if re.search(r'[=`\[\]{}]', text):
            return False
        
        # Looks like table header row (many short words like "JABATAN NAMA")
        # Real headings are usually phrases, not column labels
        if len(words) >= 2 and all(len(w) <= 12 for w in words) and len(text) < 30:
            # But allow known heading patterns
            if not re.match(r'^(BAB|PASAL|LAMPIRAN|PENDAHULUAN|DAFTAR|PROFIL)', text, re.IGNORECASE):
                # Check if it looks like "NOUN NOUN" (table header) vs "VERB NOUN" (heading)
                # Simple heuristic: if every word is a single capitalized word, likely table header
                if not any(kw in text for kw in ['DAN', 'ATAU', 'UNTUK', 'DALAM', 'DENGAN', 'PADA']):
                    return False
        
        # Contains slash-separated codes like "SK/LAM/TEKNIK"
        if text.count('/') >= 2:
            return False
        
        return True
    
    def _detect_and_format_inline_tables(self, text: str) -> str:
        """
        Detect and reformat poorly structured inline tables in text.
        
        This handles cases like:
        - "Tabel 6.1. Nilai dan Angka Mutu Penilaian"
        - "Rentang Nilai Akhir (NA) Nilai Mutu (NM) Angka Mutu (AM)"
        - "## 85,01 - 100 A 4,00"
        
        Converts to proper markdown table with clear column structure.
        """
        import re
        
        lines = text.split('\n')
        result_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Detect table header pattern: multiple column names in parentheses
            # e.g., "Rentang Nilai Akhir (NA) Nilai Mutu (NM) Angka Mutu (AM)"
            header_match = re.match(
                r'^([\w\s]+)\s*\((\w+)\)\s+([\w\s]+)\s*\((\w+)\)\s+([\w\s]+)\s*\((\w+)\)',
                line.strip()
            )
            
            if header_match:
                # Found a table header, extract column names
                col1_name = header_match.group(1).strip()
                col1_abbr = header_match.group(2).strip()
                col2_name = header_match.group(3).strip()
                col2_abbr = header_match.group(4).strip()
                col3_name = header_match.group(5).strip()
                col3_abbr = header_match.group(6).strip()
                
                # Build proper markdown table
                table_lines = []
                table_lines.append(f"| {col1_name} ({col1_abbr}) | {col2_name} ({col2_abbr}) | {col3_name} ({col3_abbr}) |")
                table_lines.append("|---|---|---|")
                
                # Look for data rows (pattern: ## or number range followed by letter and number)
                # e.g., "## 85,01 - 100 A 4,00"
                j = i + 1
                while j < len(lines):
                    data_line = lines[j].strip()
                    
                    # Skip empty lines
                    if not data_line:
                        j += 1
                        continue
                    
                    # Match data row patterns:
                    # "## 85,01 - 100 A 4,00" or "85,01 - 100 A 4,00"
                    data_match = re.match(
                        r'^(?:##\s*)?([\d,]+(?:\s*[-–]\s*[\d,]+)?)\s+([A-E][+-]?)\s+([\d,]+)',
                        data_line
                    )
                    
                    if data_match:
                        range_val = data_match.group(1).strip()
                        letter_val = data_match.group(2).strip()
                        number_val = data_match.group(3).strip()
                        table_lines.append(f"| {range_val} | {letter_val} | {number_val} |")
                        j += 1
                    else:
                        # Not a data row anymore, stop collecting
                        break
                
                # Only output as table if we found at least 2 data rows
                if len(table_lines) > 3:
                    result_lines.append("\n" + "\n".join(table_lines) + "\n")
                    i = j
                    continue
                else:
                    # Not enough data rows, keep original line
                    result_lines.append(line)
            else:
                result_lines.append(line)
            
            i += 1
        
        return '\n'.join(result_lines)
    
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
        """Load PDF file with inline table extraction and OCR fallback"""
        text = ""
        
        # First try pdfplumber for text-based PDFs with inline table handling
        try:
            import pdfplumber
            with pdfplumber.open(str(file_path)) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_content = self._extract_page_with_inline_tables(page, page_num)
                    if page_content and len(page_content.strip()) > 20:
                        text += page_content + "\n\n"
            
            if len(text.strip()) > 200:
                print(f"Extracted {len(text)} chars from {file_path.name} using pdfplumber (inline tables)")
                text = self._detect_and_format_formulas(text)
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
    
    def _extract_page_with_inline_tables(self, page, page_num: int) -> str:
        """
        Extract text from a single page with tables inserted inline.
        
        Instead of extracting text and tables separately (which causes garbled
        table text + duplicated tables appended at end), this method:
        1. Finds table bounding boxes on the page
        2. Extracts text OUTSIDE table areas (avoiding garbled table text)
        3. Inserts clean Markdown tables at their correct vertical position
        """
        try:
            # Find tables with their bounding boxes
            tables = page.find_tables()
            
            if not tables:
                # No tables on this page - just extract text normally
                page_text = page.extract_text()
                return page_text or ""
            
            # Get page height for positioning
            page_height = page.height
            
            # Collect table info: position (top y) and markdown content
            table_items = []
            table_bboxes = []
            
            for table in tables:
                bbox = table.bbox  # (x0, top, x1, bottom)
                table_data = table.extract()
                
                if table_data and len(table_data) > 1:
                    md_table = self._convert_table_to_markdown(table_data)
                    if md_table:
                        table_items.append({
                            'top': bbox[1],       # vertical position
                            'bottom': bbox[3],
                            'content': md_table
                        })
                        table_bboxes.append(bbox)
            
            # Extract text OUTSIDE table areas
            # Use crop to get text from non-table regions
            if table_bboxes:
                # Create a filtered page that excludes table areas
                filtered_page = page
                for bbox in table_bboxes:
                    # pdfplumber's filter: remove chars inside table bounding boxes
                    filtered_page = filtered_page.filter(
                        lambda obj, tb=bbox: not (
                            obj.get('top', 0) >= tb[1] - 2 and 
                            obj.get('bottom', 0) <= tb[3] + 2 and
                            obj.get('x0', 0) >= tb[0] - 2 and
                            obj.get('x1', 0) <= tb[2] + 2
                        )
                    )
                text_outside_tables = filtered_page.extract_text() or ""
            else:
                text_outside_tables = page.extract_text() or ""
            
            # If no tables were successfully extracted, return plain text
            if not table_items:
                return text_outside_tables
            
            # Split text into lines and try to insert tables at approximate positions
            # We use a simple heuristic: insert table after the text that comes before
            # its vertical position on the page
            lines = text_outside_tables.split('\n')
            
            # Sort tables by vertical position (top to bottom)
            table_items.sort(key=lambda t: t['top'])
            
            # Build final content by inserting tables between text sections
            # Simple approach: split text proportionally based on table positions
            result_parts = []
            
            if len(lines) > 0 and len(table_items) > 0:
                total_lines = len(lines)
                
                for table_info in table_items:
                    # Estimate which line the table appears after
                    # based on its vertical position relative to page height
                    position_ratio = table_info['top'] / page_height if page_height > 0 else 0.5
                    insert_after_line = int(position_ratio * total_lines)
                    
                    # Find a good break point (empty line or end of paragraph)
                    for k in range(insert_after_line, min(insert_after_line + 5, total_lines)):
                        if k < total_lines and lines[k].strip() == '':
                            insert_after_line = k
                            break
                    
                    table_info['insert_line'] = insert_after_line
                
                # Build content with tables inserted
                current_line = 0
                for table_info in table_items:
                    insert_at = table_info['insert_line']
                    
                    # Add text lines before this table
                    if insert_at > current_line:
                        result_parts.append('\n'.join(lines[current_line:insert_at]))
                    
                    # Add the table
                    result_parts.append('\n\n' + table_info['content'] + '\n')
                    current_line = insert_at
                
                # Add remaining text after last table
                if current_line < total_lines:
                    result_parts.append('\n'.join(lines[current_line:]))
                
                return '\n'.join(result_parts)
            else:
                # Fallback: just append tables after text
                result = text_outside_tables
                for table_info in table_items:
                    result += '\n\n' + table_info['content'] + '\n'
                return result
                
        except Exception as e:
            print(f"Error extracting page {page_num} with inline tables: {e}")
            # Fallback to simple text extraction
            try:
                return page.extract_text() or ""
            except:
                return ""
    
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
    
    def _preprocess_content(self, text: str) -> str:
        """
        Preprocess document content to remove unnecessary sections before chunking.
        
        Removes:
        - Page numbers (standalone numbers like "57", "58")
        - Blank lines around page numbers (to prevent chunk splitting)
        - Table of contents (Daftar Isi)
        - Preface sections (Kata Pengantar)
        - Author/committee lists
        - Headers that are just page markers
        """
        import re
        
        # Step 1: Remove page numbers with surrounding blank lines
        # Pattern: optional blank line, page number only line, optional blank line
        text = re.sub(r'\n\s*\n\s*(\d{1,3})\s*\n\s*\n', '\n', text)  # Number between blanks
        text = re.sub(r'\n\s*(\d{1,3})\s*\n\s*\n', '\n', text)  # Number followed by blank
        text = re.sub(r'\n\s*\n\s*(\d{1,3})\s*\n', '\n', text)  # Number preceded by blank
        text = re.sub(r'\n\s*(\d{1,3})\s*\n', '\n', text)  # Just page number line
        
        # Also handle roman numerals (i, ii, iii, iv, v, vi, vii, viii, ix, x)
        text = re.sub(r'\n\s*\n\s*([ivxlc]+)\s*\n\s*\n', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'\n\s*([ivxlc]+)\s*\n', '\n', text, flags=re.IGNORECASE)
        
        lines = text.split('\n')
        cleaned_lines = []
        
        # Patterns to skip entirely (headers/sections to remove)
        skip_section_patterns = [
            r'^DAFTAR\s+(ISI|TABEL|GAMBAR|LAMPIRAN)',
            r'^KATA\s+PENGANTAR',
            r'^SAMBUTAN',
            r'^SUSUNAN\s+(PANITIA|TIM|PENYUSUN)',
            r'^TIM\s+PENYUSUN',
            r'^DAFTAR\s+PIMPINAN',
            r'^HALAMAN\s+PENGESAHAN',
            r'^COVER',
            r'^LEMBAR\s+(PENGESAHAN|PERSETUJUAN)',
        ]
        
        skip_until_next_section = False
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Skip empty lines at the start
            if not stripped and not cleaned_lines:
                continue
            
            # Check if this line starts a section to skip
            for pattern in skip_section_patterns:
                if re.match(pattern, stripped, re.IGNORECASE):
                    skip_until_next_section = True
                    break
            
            # Check if we've hit a new major section (ends the skip)
            if skip_until_next_section:
                # A new major section starts with BAB, Pasal, or numbered section like "7.3."
                if re.match(r'^(BAB|Pasal|\d+\.(\d+\.)?)\s+\w', stripped, re.IGNORECASE):
                    skip_until_next_section = False
                else:
                    continue  # Skip this line
            
            # Skip standalone page numbers (e.g., "57", "58")
            # This is a backup in case the regex above missed some
            if re.match(r'^(\d{1,3}|[ivxlc]+)$', stripped, re.IGNORECASE):
                continue
            
            # Skip lines that are just page markers with dots (e.g., ".................. 57")
            if re.match(r'^[.\s]+\d+$', stripped):
                continue
            
            # Skip table of contents style entries (e.g., "7.3. Seminar Proposal ......... 57")
            if re.match(r'^[\d.]+\s+\w+.*[.]{3,}\s*\d+$', stripped):
                continue
            
            cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines)
        
        # Clean up multiple blank lines (but keep maximum 2 for paragraph separation)
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        return result.strip()
    
    def _split_into_sections(self, text: str) -> List[dict]:
        """
        Pecah teks Markdown menjadi sections berdasarkan heading ##.
        
        Returns:
            List of {'heading': str, 'content': str}
            - heading kosong untuk konten sebelum heading pertama
        """
        sections = []
        current_heading = ""
        current_lines = []
        
        for line in text.split('\n'):
            stripped = line.strip()
            # Deteksi heading: ## ... (tapi bukan | tabel |)
            if stripped.startswith('## ') and not stripped.startswith('## |'):
                # Simpan section sebelumnya
                content = '\n'.join(current_lines).strip()
                if content:
                    sections.append({
                        'heading': current_heading,
                        'content': content
                    })
                # Mulai section baru
                current_heading = stripped.lstrip('#').strip()
                current_lines = []
            else:
                current_lines.append(line)
        
        # Jangan lupa section terakhir
        content = '\n'.join(current_lines).strip()
        if content:
            sections.append({
                'heading': current_heading,
                'content': content
            })
        
        return sections
    
    def _separate_table_blocks(self, content: str) -> List[tuple]:
        """
        Pisahkan konten menjadi blok tabel dan blok teks biasa.
        Tabel = baris berturut-turut yang dimulai dengan '|'.
        
        Returns:
            List of (type, content) tuples: type = 'table' atau 'text'
        """
        blocks = []
        current_type = 'text'
        current_lines = []
        
        for line in content.split('\n'):
            stripped = line.strip()
            is_table_line = stripped.startswith('|') and stripped.endswith('|')
            
            if is_table_line and current_type == 'text':
                # Simpan blok teks sebelumnya
                text = '\n'.join(current_lines).strip()
                if text:
                    blocks.append(('text', text))
                current_lines = [line]
                current_type = 'table'
            elif not is_table_line and current_type == 'table':
                # Simpan blok tabel sebelumnya
                table = '\n'.join(current_lines).strip()
                if table:
                    blocks.append(('table', table))
                current_lines = [line]
                current_type = 'text'
            else:
                current_lines.append(line)
        
        # Blok terakhir
        remaining = '\n'.join(current_lines).strip()
        if remaining:
            blocks.append((current_type, remaining))
        
        return blocks

    def _split_numbered_table(self, table_content: str) -> List[str]:
        """
        Pecah tabel besar yang punya kolom nomor (| 1 |, | 2 |, ...)
        menjadi sub-tabel per-item. Setiap sub-tabel mendapat header.
        
        Hanya berlaku untuk tabel yang:
        1. Ukurannya > chunk_size
        2. Punya baris bernomor (kolom pertama berisi angka)
        
        Returns:
            List of sub-table strings, atau [table_content] jika tidak perlu split.
        """
        # Hanya split tabel yang lebih besar dari chunk_size
        if len(table_content) <= self.chunk_size:
            return [table_content]
        
        lines = table_content.split('\n')
        
        # Cari header dan separator
        header_line = None
        separator_line = None
        data_start = 0
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue
            if re.match(r'^\|[\s\-|]+\|$', stripped):
                separator_line = line
                data_start = i + 1
                if i > 0:
                    header_line = lines[i - 1]
            elif header_line is None and separator_line is None:
                header_line = line
        
        if not header_line or not separator_line:
            return [table_content]
        
        # Cek apakah header sebenarnya data row (kolom pertama berisi angka)
        header_cells = [c.strip() for c in header_line.strip().split('|')]
        header_first_col = header_cells[1] if len(header_cells) > 1 else ''
        header_is_data = bool(re.match(r'^\d+$', header_first_col.strip()))
        
        # Kumpulkan SEMUA baris tabel (termasuk header jika itu data)
        all_data_lines = []
        if header_is_data:
            all_data_lines.append(header_line)
        all_data_lines.extend([l for l in lines[data_start:] if l.strip()])
        
        # Kelompokkan per nomor
        groups = []
        current_group = []
        has_numbered_rows = False
        
        for line in all_data_lines:
            stripped = line.strip()
            cells = [c.strip() for c in stripped.split('|')]
            first_col = cells[1] if len(cells) > 1 else ''
            
            is_numbered = bool(re.match(r'^\d+$', first_col.strip()))
            is_separator = bool(re.match(r'^[\s\-]+$', first_col))
            
            if is_numbered:
                has_numbered_rows = True
                if current_group:
                    groups.append(current_group)
                current_group = [line]
            elif is_separator:
                if current_group:
                    current_group.append(line)
            else:
                # Continuation row — join current group
                current_group.append(line)
        
        if current_group:
            groups.append(current_group)
        
        if not has_numbered_rows or len(groups) < 3:
            return [table_content]
        
        # Buat header block
        # Jika header asli = data row, gunakan header generik berdasarkan jumlah kolom
        if header_is_data:
            num_cols = len(header_cells) - 2  # minus leading/trailing empty
            header_block = separator_line  # Only separator, no misleading header
        else:
            header_block = header_line + '\n' + separator_line
        
        sub_tables = []
        for group in groups:
            group_content = '\n'.join(group)
            sub_table = header_block + '\n' + group_content
            sub_tables.append(sub_table)
        
        print(f"   [TABLE SPLIT] Split large table ({len(table_content)} chars) into {len(sub_tables)} sub-tables by numbered rows")
        return sub_tables
    
    
    def _split_text(self, text: str) -> List[str]:
        """
        Structure-aware chunking: pecah teks berdasarkan heading ##,
        lalu sub-split section yang terlalu panjang.
        
        Setiap chunk mendapat prefix [Konteks: heading] agar embedding model
        tahu chunk ini berada di section mana.
        """
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
        except ImportError:
            from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        # Preprocess (hapus TOC, page numbers, dll)
        text = self._preprocess_content(text)
        text = text.strip()
        if not text:
            return []
        
        # Pecah berdasarkan heading
        sections = self._split_into_sections(text)
        
        # Splitter fallback untuk section yang terlalu panjang
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            is_separator_regex=False,
            separators=[
                "\n\n",      # Paragraf
                "\n",        # Baris (penting: pisah antar list item / baris tabel)
                ". ",        # Kalimat
                "? ",
                "! ",
                "; ",
                ", ",
                " ",
                ""
            ]
        )
        
        all_chunks = []
        
        for section in sections:
            heading = section['heading']
            content = section['content']
            
            # Buat prefix konteks heading
            if heading:
                prefix = f"[Konteks: {heading}]\n\n"
            else:
                prefix = ""
            
            # Hitung space yang tersedia untuk konten (kurangi prefix)
            available_size = self.chunk_size - len(prefix)
            
            if len(content) <= available_size:
                # Section muat dalam 1 chunk
                chunk = prefix + content
                all_chunks.append(chunk.strip())
            else:
                # Section terlalu panjang — pisahkan tabel dari teks biasa
                # Tabel (blok | ... |) dijadikan chunk utuh, sisanya di-sub-split
                blocks = self._separate_table_blocks(content)
                
                sub_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=max(available_size, 200),
                    chunk_overlap=self.chunk_overlap,
                    length_function=len,
                    is_separator_regex=False,
                    separators=["\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " ", ""]
                )
                
                for block_type, block_content in blocks:
                    if block_type == 'table':
                        # Try splitting large numbered tables into per-item sub-tables
                        sub_tables = self._split_numbered_table(block_content)
                        for sub_table in sub_tables:
                            chunk = prefix + sub_table
                            all_chunks.append(chunk.strip())
                    else:
                        # Teks biasa = sub-split jika perlu
                        if len(block_content) <= available_size:
                            chunk = prefix + block_content
                            all_chunks.append(chunk.strip())
                        else:
                            sub_chunks = sub_splitter.split_text(block_content)
                            for sub_chunk in sub_chunks:
                                chunk = prefix + sub_chunk
                                all_chunks.append(chunk.strip())
        
        print(f"   Structure-aware chunking: {len(text)} chars -> {len(all_chunks)} chunks "
              f"({len(sections)} sections, size={self.chunk_size}, overlap={self.chunk_overlap})")
        
        return all_chunks

