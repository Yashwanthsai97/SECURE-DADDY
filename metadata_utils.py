import csv
import io
import json
import re
from datetime import datetime
from email import policy
from email.parser import BytesParser

import exifread
from PIL import Image
from PyPDF2 import PdfReader
from lxml import etree, html


def _format_size(size):
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} kB"
    if size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.2f} MB"
    return f"{size / (1024 * 1024 * 1024):.2f} GB"


def _format_timestamp(value):
    if not value:
        return "-"
    if isinstance(value, datetime):
        return value.isoformat(sep=" ", timespec="seconds")
    return str(value)


def _clean(value):
    if value is None or value == "":
        return "-"
    if isinstance(value, (list, tuple, set)):
        values = [str(item) for item in value if item not in (None, "")]
        return ", ".join(values) if values else "-"
    return str(value)


def _add_section(sections, title, fields):
    cleaned = {}
    for key, value in fields.items():
        normalized = _clean(value)
        if normalized != "-":
            cleaned[key] = normalized
    if cleaned:
        sections[title] = cleaned


def _extract_text_indicators(text):
    ips = sorted(set(re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)))
    timestamps = sorted(set(re.findall(r"\b\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})?\b", text)))
    email_headers = re.findall(r"^(From|To|Cc|Bcc|Subject|Date|Message-ID|Return-Path|Received):\s*(.+)$", text, flags=re.MULTILINE | re.IGNORECASE)
    return {
        "Logs": "Indicators detected in text content" if ips or timestamps else "-",
        "IP address": ", ".join(ips),
        "Timestamp": ", ".join(timestamps),
        "Email headers": " | ".join([f"{name}: {value}" for name, value in email_headers]),
    }


def _analyze_image(data, file_name, mime_type, sections, warnings):
    image = Image.open(io.BytesIO(data))
    width, height = image.size
    exif_tags = exifread.process_file(io.BytesIO(data), details=False)

    _add_section(sections, "1. Descriptive Metadata", {
        "Title": exif_tags.get("Image ImageDescription"),
        "Author": exif_tags.get("Image Artist"),
        "Keywords": exif_tags.get("Image XPKeywords"),
        "Tags": exif_tags.get("Image XPKeywords"),
        "Description": exif_tags.get("Image ImageDescription"),
        "Subject": "Image",
    })
    _add_section(sections, "2. Structural Metadata", {
        "File structure": "Raster image file",
        "Data organization": f"{width} x {height} pixels",
    })
    _add_section(sections, "3. Administrative Metadata", {
        "File size": _format_size(len(data)),
        "File type/format": mime_type,
        "Owner": "-",
        "Access permissions": "Browser upload access only",
    })
    _add_section(sections, "Administrative Metadata - Technical", {
        "Resolution": f"{width} x {height}",
        "Format": mime_type,
    })
    _add_section(sections, "Administrative Metadata - Rights", {
        "Copyright": exif_tags.get("Image Copyright"),
        "License": exif_tags.get("Image XPAuthor"),
    })
    _add_section(sections, "Images (EXIF)", {
        "Camera model": exif_tags.get("Image Model"),
        "ISO": exif_tags.get("EXIF ISOSpeedRatings"),
        "Location": f"{exif_tags.get('GPS GPSLatitude', '-')}, {exif_tags.get('GPS GPSLongitude', '-')}",
        "Date/time": exif_tags.get("EXIF DateTimeOriginal") or exif_tags.get("Image DateTime"),
    })

    raw_exif = {key: _clean(value) for key, value in exif_tags.items()}
    _add_section(sections, "Raw EXIF Metadata", raw_exif)
    if not raw_exif:
        warnings.append("No embedded EXIF tags were found in this image.")


def _analyze_pdf(data, mime_type, sections, warnings):
    reader = PdfReader(io.BytesIO(data))
    metadata = reader.metadata or {}
    page_count = len(reader.pages)

    _add_section(sections, "1. Descriptive Metadata", {
        "Title": metadata.get("/Title"),
        "Author": metadata.get("/Author"),
        "Keywords": metadata.get("/Keywords"),
        "Description": metadata.get("/Subject"),
        "Subject": metadata.get("/Subject"),
    })
    _add_section(sections, "2. Structural Metadata", {
        "Page order": f"1..{page_count}",
        "Chapters/sections": "Outline parsing not available" if page_count else "-",
        "File structure": "PDF document",
        "Data organization": f"{page_count} pages",
    })
    _add_section(sections, "3. Administrative Metadata", {
        "File size": _format_size(len(data)),
        "File type/format": mime_type,
        "Creation date": metadata.get("/CreationDate"),
        "Modification date": metadata.get("/ModDate"),
        "Owner": metadata.get("/Author"),
        "Access permissions": "Encrypted" if reader.is_encrypted else "Unencrypted",
    })
    _add_section(sections, "Administrative Metadata - Technical", {
        "Format": mime_type,
    })
    _add_section(sections, "Administrative Metadata - Rights", {
        "Copyright": metadata.get("/Copyright"),
    })
    _add_section(sections, "Raw PDF Metadata", {key: _clean(value) for key, value in metadata.items()})


def _analyze_html(text, sections):
    document = html.fromstring(text)
    meta = {
        item.attrib.get("name", "").lower(): item.attrib.get("content", "")
        for item in document.xpath("//meta[@name]")
    }
    _add_section(sections, "1. Descriptive Metadata", {
        "Title": document.findtext(".//title"),
        "Keywords": meta.get("keywords"),
        "Tags": meta.get("keywords"),
        "Description": meta.get("description"),
        "Subject": "HTML document",
    })
    _add_section(sections, "2. Structural Metadata", {
        "Chapters/sections": len(document.xpath("//h1|//h2|//h3")),
        "Table relationships": len(document.xpath("//table")),
        "File structure": "HTML document",
        "Data organization": f"{len(document.xpath('//*'))} elements",
    })
    _add_section(sections, "Websites (SEO)", {
        "Meta title": document.findtext(".//title"),
        "Meta description": meta.get("description"),
        "Keywords": meta.get("keywords"),
    })


def _analyze_xml(text, sections):
    root = etree.fromstring(text.encode("utf-8"))
    children = sorted(set(child.tag for child in root.iterchildren()))
    _add_section(sections, "2. Structural Metadata", {
        "File structure": "XML document",
        "Data organization": f"Root: {root.tag}",
    })
    _add_section(sections, "Databases", {
        "Column names": ", ".join(children),
    })


def _analyze_json(text, sections):
    parsed = json.loads(text)
    keys = list(parsed.keys()) if isinstance(parsed, dict) else []
    _add_section(sections, "2. Structural Metadata", {
        "File structure": "JSON object" if isinstance(parsed, dict) else "JSON array",
        "Data organization": "Top-level keys: " + ", ".join(keys) if keys else "Array or scalar JSON",
    })
    _add_section(sections, "Databases", {
        "Column names": ", ".join(keys),
    })


def _analyze_csv(text, sections):
    rows = list(csv.reader(io.StringIO(text)))
    headers = rows[0] if rows else []
    _add_section(sections, "2. Structural Metadata", {
        "Table relationships": "Flat table structure",
        "File structure": "CSV tabular file",
        "Data organization": f"{max(len(rows) - 1, 0)} rows",
    })
    _add_section(sections, "Databases", {
        "Column names": ", ".join(headers),
        "Data types": "Inferred types not available",
    })


def _analyze_sql(text, sections):
    table_match = re.search(r"create\s+table\s+([^\s(]+)", text, flags=re.IGNORECASE)
    columns = re.findall(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s+([A-Za-z0-9()]+)", text, flags=re.MULTILINE)
    constraints = re.findall(r"\b(primary key|foreign key|unique|not null|check|default)\b", text, flags=re.IGNORECASE)
    _add_section(sections, "2. Structural Metadata", {
        "File structure": "SQL schema definition",
        "Data organization": "Table and column declarations",
    })
    _add_section(sections, "Databases", {
        "Table name": table_match.group(1) if table_match else "-",
        "Column names": ", ".join(column for column, _ in columns),
        "Data types": ", ".join(sorted(set(dtype for _, dtype in columns))),
        "Constraints": ", ".join(sorted(set(item.upper() for item in constraints))),
    })


def _analyze_email(data, text, sections):
    message = BytesParser(policy=policy.default).parsebytes(data)
    _add_section(sections, "1. Descriptive Metadata", {
        "Title": message.get("Subject"),
        "Author": message.get("From"),
        "Subject": message.get("Subject"),
    })
    _add_section(sections, "Cybersecurity", {
        "Email headers": " | ".join(f"{key}: {value}" for key, value in message.items()),
    })
    _add_section(sections, "Raw Text Preview", {
        "First 500 characters": text[:500],
    })


def analyze_uploaded_file(file_storage):
    data = file_storage.read()
    file_storage.stream.seek(0)

    file_name = file_storage.filename or "uploaded-file"
    mime_type = file_storage.mimetype or "application/octet-stream"
    extension = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""

    sections = {}
    warnings = []

    _add_section(sections, "File Systems", {
        "File name": file_name,
        "Size": _format_size(len(data)),
        "Type": mime_type,
    })

    if mime_type.startswith("image/"):
        _analyze_image(data, file_name, mime_type, sections, warnings)
    elif mime_type == "application/pdf" or extension == "pdf":
        _analyze_pdf(data, mime_type, sections, warnings)
    elif mime_type.startswith("text/") or extension in {"html", "htm", "json", "xml", "csv", "sql", "log", "txt", "eml"}:
        text = data.decode("utf-8", errors="replace")
        _add_section(sections, "3. Administrative Metadata", {
            "File size": _format_size(len(data)),
            "File type/format": mime_type,
        })
        _add_section(sections, "Cybersecurity", _extract_text_indicators(text))

        if extension in {"html", "htm"}:
            _analyze_html(text, sections)
        elif extension == "json":
            _analyze_json(text, sections)
        elif extension == "xml":
            _analyze_xml(text, sections)
        elif extension == "csv":
            _analyze_csv(text, sections)
        elif extension == "sql":
            _analyze_sql(text, sections)
        elif extension == "eml":
            _analyze_email(data, text, sections)

        _add_section(sections, "Raw Text Preview", {
            "First 500 characters": text[:500],
        })
    elif mime_type.startswith("video/"):
        _add_section(sections, "3. Administrative Metadata", {
            "File size": _format_size(len(data)),
            "File type/format": mime_type,
        })
        warnings.append("Deep video metadata is limited because ffprobe/MediaInfo is not installed on the backend.")
    else:
        _add_section(sections, "3. Administrative Metadata", {
            "File size": _format_size(len(data)),
            "File type/format": mime_type,
        })
        warnings.append("This file type has limited backend extraction support.")

    return {
        "sections": sections,
        "warnings": warnings,
    }
