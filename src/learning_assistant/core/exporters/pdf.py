"""
PDF Exporter for Learning Assistant.

This module provides PDF output generation (optional dependency).
"""

from pathlib import Path
from typing import Any

from loguru import logger

from learning_assistant.core.exporters.base import BaseExporter
from learning_assistant.core.exporters.markdown import MarkdownExporter


class PDFExporter(BaseExporter):
    """
    PDF exporter (optional).

    Converts Markdown to PDF using optional dependencies.
    Falls back to Markdown output if PDF libraries not available.
    """

    def __init__(self, template_dir: Path | None = None) -> None:
        """
        Initialize PDF exporter.

        Args:
            template_dir: Directory containing templates
        """
        super().__init__(template_dir)

        # Check for PDF libraries
        self.pdf_available = self._check_pdf_libraries()

        # Use Markdown exporter as fallback
        self.md_exporter = MarkdownExporter(template_dir)

        logger.info(f"PDFExporter initialized (PDF available: {self.pdf_available})")

    def _check_pdf_libraries(self) -> bool:
        """
        Check if PDF generation libraries are available.

        Returns:
            True if PDF libraries available, False otherwise
        """
        import importlib.util

        weasyprint_spec = importlib.util.find_spec("weasyprint")
        if weasyprint_spec is not None:
            return True

        logger.warning(
            "PDF libraries not available. Install with: pip install weasyprint"
        )
        return False

    def export(
        self,
        data: dict[str, Any],
        output_path: Path,
        **kwargs: Any,
    ) -> None:
        """
        Export data to PDF file.

        Args:
            data: Data to export
            output_path: Output PDF file path
            **kwargs: Additional parameters
        """
        if not self.pdf_available:
            logger.warning("PDF export not available, falling back to Markdown")
            # Fall back to Markdown
            md_path = output_path.with_suffix(".md")
            self.md_exporter.export(data, md_path, **kwargs)
            return

        # Generate PDF
        self._export_pdf(data, output_path, **kwargs)

    def _export_pdf(
        self,
        data: dict[str, Any],
        output_path: Path,
        **kwargs: Any,
    ) -> None:
        """
        Generate PDF using WeasyPrint.

        Args:
            data: Data to export
            output_path: Output PDF file path
            **kwargs: Additional parameters
        """
        try:
            import weasyprint  # type: ignore[import-untyped]
            from weasyprint.text.css import CSS  # type: ignore[import-untyped]

            # Generate Markdown
            md_content = self.md_exporter.export_to_string(data, **kwargs)

            # Convert Markdown to HTML
            html_content = self._markdown_to_html(md_content)

            # Generate PDF
            self.ensure_output_dir(output_path)

            html = weasyprint.HTML(string=html_content)
            css = CSS(string=self._get_pdf_css())

            html.write_pdf(output_path, stylesheets=[css])

            logger.info(f"PDF exported to: {output_path}")

        except Exception as e:
            logger.error(f"PDF export failed: {e}")
            raise

    def _markdown_to_html(self, md_content: str) -> str:
        """
        Convert Markdown to HTML.

        Args:
            md_content: Markdown content

        Returns:
            HTML content
        """
        try:
            import markdown  # type: ignore[import-untyped]

            html_body = markdown.markdown(
                md_content, extensions=["tables", "fenced_code"]
            )

            html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body>
{html_body}
</body>
</html>
"""
            return html

        except ImportError:
            logger.warning("Markdown library not available, using simple conversion")
            # Simple fallback
            return f"<html><body><pre>{md_content}</pre></body></html>"

    def _get_pdf_css(self) -> str:
        """
        Get CSS for PDF styling.

        Returns:
            CSS string
        """
        return """
        body {
            font-family: "Microsoft YaHei", "SimSun", Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            margin: 2cm;
        }

        h1 {
            font-size: 24pt;
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }

        h2 {
            font-size: 18pt;
            color: #34495e;
            margin-top: 20px;
        }

        h3 {
            font-size: 14pt;
            color: #7f8c8d;
        }

        blockquote {
            border-left: 4px solid #3498db;
            padding-left: 10px;
            color: #7f8c8d;
            font-style: italic;
        }

        code {
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: "Courier New", monospace;
        }

        ul, ol {
            margin-left: 20px;
        }

        li {
            margin-bottom: 5px;
        }

        hr {
            border: none;
            border-top: 1px solid #bdc3c7;
            margin-top: 30px;
        }
        """

    def export_to_string(
        self,
        data: dict[str, Any],
        **kwargs: Any,
    ) -> str:
        """
        Export data to string (returns Markdown for PDF).

        Args:
            data: Data to export
            **kwargs: Additional parameters

        Returns:
            Markdown string (PDF binary not returned)
        """
        return self.md_exporter.export_to_string(data, **kwargs)
