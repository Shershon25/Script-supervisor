import io
import re
import uuid
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

logger = logging.getLogger("script_supervisor.document_parser")

@dataclass
class ParsedPage:
    page_number: int  # 1-indexed
    text: str
    lines: List[str]

@dataclass
class ParsedDocument:
    filename: str
    file_type: str  # "pdf", "docx", "txt"
    file_size: int
    page_count: Optional[int]
    character_count: int
    pages: List[ParsedPage]
    raw_text: str
    warnings: List[str] = field(default_factory=list)

@dataclass
class ParsedScene:
    temporary_id: str
    scene_number: int
    heading: str
    raw_text: str
    source_page_start: Optional[int] = None
    source_page_end: Optional[int] = None
    confidence: float = 1.0


class DocumentParser(ABC):
    """Abstract base parser for screenplay documents."""
    
    @abstractmethod
    def parse(self, file_bytes: bytes, filename: str) -> ParsedDocument:
        pass


class PdfDocumentParser(DocumentParser):
    """PDF document parser preserving reading order and page numbers."""

    def parse(self, file_bytes: bytes, filename: str) -> ParsedDocument:
        import pypdf
        
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        except Exception as e:
            logger.error(f"Failed to open PDF document {filename}: {e}")
            raise ValueError(f"Could not read PDF file. The document may be corrupted or password-protected.")

        page_count = len(reader.pages)
        if page_count == 0:
            raise ValueError("Uploaded PDF document has no pages.")

        pages: List[ParsedPage] = []
        full_text_chunks: List[str] = []
        total_chars = 0

        for i, page in enumerate(reader.pages):
            page_num = i + 1
            extracted = page.extract_text() or ""
            lines = [l.strip() for l in extracted.splitlines() if l.strip()]
            
            # Filter out deterministic standalone header/footer page numbers like "12." or "Page 12"
            cleaned_lines = []
            for line in lines:
                if re.match(r'^(?:page\s+)?\d{1,3}\.?$', line, re.IGNORECASE):
                    continue
                cleaned_lines.append(line)

            page_text = "\n".join(cleaned_lines)
            total_chars += len(page_text)
            full_text_chunks.append(page_text)
            pages.append(ParsedPage(page_number=page_num, text=page_text, lines=cleaned_lines))

        raw_text = "\n\n".join(full_text_chunks).strip()

        if total_chars == 0 or not raw_text.strip():
            raise ValueError("Could not extract readable text from this PDF. It may be scanned or image-based.")

        return ParsedDocument(
            filename=filename,
            file_type="pdf",
            file_size=len(file_bytes),
            page_count=page_count,
            character_count=total_chars,
            pages=pages,
            raw_text=raw_text,
            warnings=[]
        )


class DocxDocumentParser(DocumentParser):
    """DOCX document parser preserving document order and paragraph boundaries."""

    def parse(self, file_bytes: bytes, filename: str) -> ParsedDocument:
        import docx

        try:
            doc = docx.Document(io.BytesIO(file_bytes))
        except Exception as e:
            logger.error(f"Failed to open DOCX document {filename}: {e}")
            raise ValueError("Could not read DOCX file. The document may be corrupted.")

        paragraphs = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
        
        if not paragraphs:
            raise ValueError("Uploaded DOCX file contains no readable text.")

        raw_text = "\n".join(paragraphs).strip()
        total_chars = len(raw_text)

        # Estimate page count (~1800 chars per screenplay page)
        estimated_pages = max(1, round(total_chars / 1800))

        # Build synthetic page mapping for DOCX
        pages = [ParsedPage(page_number=1, text=raw_text, lines=paragraphs)]

        return ParsedDocument(
            filename=filename,
            file_type="docx",
            file_size=len(file_bytes),
            page_count=estimated_pages,
            character_count=total_chars,
            pages=pages,
            raw_text=raw_text,
            warnings=[]
        )


class FountainDocumentParser(DocumentParser):
    """Fountain screenplay document parser (.fountain) preserving line breaks and markdown format."""

    def parse(self, file_bytes: bytes, filename: str) -> ParsedDocument:
        try:
            text_str = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text_str = file_bytes.decode("latin-1")
            except Exception as e:
                raise ValueError("Could not decode Fountain file. Ensure it is encoded in UTF-8 or ASCII.")

        if not text_str.strip():
            raise ValueError("Uploaded Fountain screenplay file is empty.")

        lines = [line.rstrip() for line in text_str.splitlines()]
        raw_text = "\n".join(lines).strip()
        total_chars = len(raw_text)

        pages = [ParsedPage(page_number=1, text=raw_text, lines=lines)]

        return ParsedDocument(
            filename=filename,
            file_type="fountain",
            file_size=len(file_bytes),
            page_count=None,
            character_count=total_chars,
            pages=pages,
            raw_text=raw_text,
            warnings=[]
        )


class SceneBoundaryDetector:
    """
    Deterministic screenplay scene boundary detector.
    Recognizes screenplay scene heading patterns:
    - Standard INT./EXT. prefixes
    - Location headings with time-of-day suffixes (e.g. INTERROGATION ROOM - DAY)
    - Custom location headings (e.g. INTERROGATION ROOM) at document start or separated by blank lines
    Guarantees no leading document content is dropped.
    """

    SCENE_HEADING_PATTERN = re.compile(
        r'^(?:\d{1,3}\s+)?(?:INT\.|EXT\.|INT\./EXT\.|I/E\.|EXT/INT|INT/EXT|INT\b|EXT\b|EST\.|ESTABLISHING)'
        r'[\s\.\-\:\/].*$',
        re.IGNORECASE
    )

    TIME_OF_DAY_SUFFIX_PATTERN = re.compile(
        r'[\-\–\—]\s*(?:DAY|NIGHT|MORNING|EVENING|AFTERNOON|DUSK|DAWN|CONTINUOUS|LATER|MOMENTS\s+LATER|SAME|SUNSET|SUNRISE|NIGHT\s*\([^\)]+\)|DAY\s*\([^\)]+\))\s*$',
        re.IGNORECASE
    )

    TIME_OF_DAY_PATTERN = re.compile(
        r'\b(?:DAY|NIGHT|MORNING|EVENING|AFTERNOON|DUSK|DAWN|CONTINUOUS|LATER|MOMENTS\s+LATER|SAME|SUNSET|SUNRISE|NIGHT\s*\([^\)]+\)|DAY\s*\([^\)]+\))\b',
        re.IGNORECASE
    )

    NON_HEADING_TRANSITIONS = {
        "CUT TO:", "FADE IN:", "FADE OUT.", "DISSOLVE TO:", "SMASH CUT TO:", 
        "MATCH CUT TO:", "FADE TO BLACK.", "INTERCUT WITH:", "BACK TO:"
    }

    COVER_PAGE_INDICATORS = re.compile(
        r'\b(?:title:|credit:|author:|authors:|source:|written\s+by|screenplay\s+by|story\s+by|created\s+by|teleplay\s+by|adapted\s+by|draft\s+date|copyright|all\s+rights\s+reserved|contact:)\b',
        re.IGNORECASE
    )

    LOCATION_WORDS = {
        "ROOM", "HALLWAY", "HOUSE", "OFFICE", "STREET", "PARK", "CAR", "APARTMENT", 
        "BUILDING", "CORRIDOR", "STAGE", "SET", "LOCATION", "BAR", "CLUB", "CAFE", 
        "RESTAURANT", "KITCHEN", "BEDROOM", "BASEMENT", "ROOFTOP", "DOCK", "ALLEY", 
        "HIGHWAY", "STATION", "GATE", "STUDIO", "STORE", "SHOP", "GYM", "HOSPITAL", 
        "LAB", "LIBRARY", "WAREHOUSE", "PIER", "GARAGE", "LIVING", "DINER", "CEMETERY",
        "ARCHIVE", "CENTRAL", "SCHOOL", "INTERROGATION"
    }

    def is_scene_heading(
        self, 
        clean_line: str, 
        is_first_non_empty: bool = False, 
        preceded_by_blank: bool = False,
        allow_standalone_uppercase: bool = False
    ) -> Tuple[bool, float]:
        if not clean_line:
            return False, 0.0

        upper_line = clean_line.upper()
        if upper_line in self.NON_HEADING_TRANSITIONS or upper_line.endswith(" TO:"):
            return False, 0.0

        # Ignore lines with cover page metadata keywords when identifying scene headings
        if self.COVER_PAGE_INDICATORS.search(clean_line):
            return False, 0.0

        # 1. Standard scene heading pattern (INT., EXT., etc.)
        if self.SCENE_HEADING_PATTERN.match(clean_line):
            has_time_of_day = bool(self.TIME_OF_DAY_PATTERN.search(clean_line))
            is_all_caps = clean_line.isupper()
            if has_time_of_day and is_all_caps:
                return True, 0.98
            elif has_time_of_day or is_all_caps:
                return True, 0.90
            else:
                return True, 0.75

        # 2. Location heading with Time-of-Day suffix (e.g. INTERROGATION ROOM - DAY)
        if self.TIME_OF_DAY_SUFFIX_PATTERN.search(clean_line):
            if not clean_line.endswith(":") and len(clean_line) < 80:
                return True, 0.90

        # 3. Custom standalone location heading (e.g. INTERROGATION ROOM)
        if is_first_non_empty or preceded_by_blank or allow_standalone_uppercase:
            if (
                len(clean_line) >= 3
                and len(clean_line) < 60
                and clean_line.isupper()
                and not clean_line.startswith('(')
                and not clean_line.endswith('.')
                and not clean_line.endswith('?')
                and not clean_line.endswith('!')
                and not clean_line.endswith(':')
                and not re.search(r'\((?:V\.O\.|O\.S\.|CONT\'D|O\.C\.)\)$', clean_line, re.IGNORECASE)
                and '—' not in clean_line
            ):
                words = set(re.findall(r'\b[A-Z]+\b', clean_line))
                if words & self.LOCATION_WORDS:
                    return True, 0.85
                elif is_first_non_empty and len(words) >= 2:
                    return True, 0.85

        return False, 0.0

    def strip_cover_page(self, lines_with_pages: List[Tuple[str, Optional[int]]]) -> List[Tuple[str, Optional[int]]]:
        if not lines_with_pages:
            return lines_with_pages

        # Find the index of the VERY FIRST scene heading in the document
        first_heading_idx = -1
        for i, (line, _) in enumerate(lines_with_pages):
            clean_line = line.strip()
            if not clean_line:
                continue
            is_heading, _ = self.is_scene_heading(
                clean_line,
                is_first_non_empty=(i == 0),
                preceded_by_blank=True,
                allow_standalone_uppercase=True
            )
            if is_heading:
                first_heading_idx = i
                break

        if first_heading_idx <= 0:
            # If no heading found or first line is already a heading, return intact
            return lines_with_pages

        # Preserve opening transition (e.g. FADE IN:) if directly preceding the first scene heading
        start_idx = first_heading_idx
        for check_idx in range(first_heading_idx - 1, -1, -1):
            line_str = lines_with_pages[check_idx][0].strip().upper()
            if not line_str:
                continue
            if line_str in ("FADE IN:", "FADE IN", "FADE IN.") or line_str.endswith("TO:"):
                start_idx = check_idx
                break
            else:
                break

        # Check lines BEFORE start_idx for cover page indicators or metadata
        preamble_lines = [l[0] for l in lines_with_pages[:start_idx]]
        has_cover_indicator = any(self.COVER_PAGE_INDICATORS.search(l) for l in preamble_lines)

        # Strip preamble lines if cover metadata is present or if preamble is short (title page metadata)
        if has_cover_indicator or start_idx < 15:
            logger.info(f"Cover page detected and stripped ({start_idx} preamble lines omitted before first scene heading).")
            return lines_with_pages[start_idx:]

        return lines_with_pages

    def sanitize_and_normalize_lines(self, lines_with_pages: List[Tuple[str, Optional[int]]]) -> List[Tuple[str, Optional[int]]]:
        if not lines_with_pages:
            return lines_with_pages

        expanded_lines: List[Tuple[str, Optional[int]]] = []

        for line, pg in lines_with_pages:
            clean = line.strip()
            if not clean:
                expanded_lines.append(("", pg))
                continue

            # Strip embedded title page metadata prefix if present on line (e.g. "OUAC Written by Melissa Vivian Holicek INTERROGATION ROOM...")
            if self.COVER_PAGE_INDICATORS.search(clean):
                match = re.search(
                    r'^(?:.*?\b(?:written|screenplay|story|created|Written|Screenplay|Story|Created)\s+[bB][yY]\b.+?)(?=\s+[A-Z]{3,}\b|\s*INT\.|\s*EXT\.)',
                    clean,
                    re.DOTALL
                )
                if match:
                    remainder = clean[match.end():].strip()
                    if remainder:
                        clean = remainder
                    else:
                        continue

            # Split inline scene headings from action text (e.g. "INTERROGATION ROOM (A BOY...")
            split_line = re.sub(
                r'([A-Z0-9\s]{3,}\b(?:ROOM|HALLWAY|HOUSE|OFFICE|STREET|PARK|CAR|APARTMENT|BUILDING|CORRIDOR|STAGE|SET|LOCATION|BAR|CLUB|CAFE|RESTAURANT|KITCHEN|BEDROOM|BASEMENT|ROOFTOP|DOCK|ALLEY|HIGHWAY|STATION|GATE|STUDIO|STORE|SHOP))\s+(\()',
                r'\1\n\2',
                clean
            )

            for part in split_line.splitlines():
                if part.strip():
                    expanded_lines.append((part.strip(), pg))

        if expanded_lines:
            lines_with_pages = expanded_lines

        return self.strip_cover_page(lines_with_pages)

    def detect_scenes(self, parsed_doc: ParsedDocument) -> List[ParsedScene]:
        lines_with_pages: List[Tuple[str, Optional[int]]] = []

        if parsed_doc.pages:
            for page in parsed_doc.pages:
                page_num = page.page_number if parsed_doc.file_type != "txt" else None
                for line in page.lines:
                    lines_with_pages.append((line, page_num))
        else:
            for line in parsed_doc.raw_text.splitlines():
                lines_with_pages.append((line, None))

        lines_with_pages = self.sanitize_and_normalize_lines(lines_with_pages)

        detected_scenes: List[ParsedScene] = []
        current_heading: Optional[str] = None
        current_lines: List[str] = []
        current_page_start: Optional[int] = None
        current_page_end: Optional[int] = None
        current_confidence: float = 1.0

        def finalize_scene(scene_num: int):
            nonlocal current_heading, current_lines, current_page_start, current_page_end, current_confidence
            if not current_heading:
                return

            raw_scene_text = "\n".join(current_lines).strip()
            if not raw_scene_text:
                return

            detected_scenes.append(ParsedScene(
                temporary_id=str(uuid.uuid4()),
                scene_number=scene_num,
                heading=current_heading,
                raw_text=raw_scene_text,
                source_page_start=current_page_start,
                source_page_end=current_page_end,
                confidence=current_confidence
            ))

        scene_counter = 0
        is_first_non_empty = True
        preceded_by_blank = True
        opening_preamble: List[str] = []

        for line, page_num in lines_with_pages:
            clean_line = line.strip()
            if not clean_line:
                if current_lines:
                    current_lines.append("")
                elif opening_preamble:
                    opening_preamble.append("")
                preceded_by_blank = True
                continue

            is_heading, confidence = self.is_scene_heading(
                clean_line, 
                is_first_non_empty=is_first_non_empty, 
                preceded_by_blank=preceded_by_blank
            )

            # If before the first scene heading, accumulate preamble text (e.g. FADE IN:)
            if not is_heading and current_heading is None:
                opening_preamble.append(line)
                is_first_non_empty = False
                preceded_by_blank = False
                continue

            if is_heading:
                norm_heading = re.sub(r'^\d{1,3}\s+', '', clean_line).strip()

                if current_heading:
                    scene_counter += 1
                    finalize_scene(scene_counter)

                current_heading = norm_heading
                # Attach any opening preamble (e.g. FADE IN:) to the first scene
                if opening_preamble:
                    current_lines = [l for l in opening_preamble]
                    current_lines.append("")
                    current_lines.append(clean_line)
                    opening_preamble = []
                else:
                    current_lines = [clean_line]

                current_page_start = page_num if current_page_start is None else current_page_start
                current_page_end = page_num
                current_confidence = confidence
            else:
                if current_heading:
                    current_lines.append(line)
                    if page_num is not None:
                        if current_page_start is None:
                            current_page_start = page_num
                        current_page_end = page_num

            is_first_non_empty = False
            preceded_by_blank = False

        if current_heading:
            scene_counter += 1
            finalize_scene(scene_counter)
        elif opening_preamble:
            # Fallback if no scenes detected at all
            scene_counter += 1
            current_heading = "SCENE 1 (UNFORMATTED DOCUMENT)"
            current_lines = opening_preamble
            finalize_scene(scene_counter)

        # Fallback if no scenes detected
        if not detected_scenes and parsed_doc.raw_text.strip():
            parsed_doc.warnings.append(
                "No screenplay scene headings were detected. Check that the document is formatted as a screenplay."
            )
            detected_scenes.append(ParsedScene(
                temporary_id=str(uuid.uuid4()),
                scene_number=1,
                heading="SCENE 1 (UNFORMATTED DOCUMENT)",
                raw_text=parsed_doc.raw_text,
                source_page_start=1 if parsed_doc.file_type != "txt" else None,
                source_page_end=parsed_doc.page_count if parsed_doc.file_type != "txt" else None,
                confidence=0.50
            ))

        return detected_scenes
