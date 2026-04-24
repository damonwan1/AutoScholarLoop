from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class PaperFormat:
    key: str
    display_name: str
    page_size: str
    columns: int
    citation_style: str
    latex_documentclass: str
    latex_packages: tuple[str, ...]
    section_style: str
    abstract_style: str
    figure_caption: str
    table_caption: str
    bibliography_note: str
    recommended_sections: tuple[str, ...]
    output_note: str

    def to_markdown(self) -> str:
        return (
            f"# Paper Format Profile: {self.display_name}\n\n"
            f"- key: {self.key}\n"
            f"- page_size: {self.page_size}\n"
            f"- columns: {self.columns}\n"
            f"- citation_style: {self.citation_style}\n"
            f"- section_style: {self.section_style}\n"
            f"- abstract_style: {self.abstract_style}\n"
            f"- figure_caption: {self.figure_caption}\n"
            f"- table_caption: {self.table_caption}\n"
            f"- bibliography_note: {self.bibliography_note}\n"
            f"- output_note: {self.output_note}\n"
            "\n## Recommended Sections\n\n"
            + "\n".join(f"- {section}" for section in self.recommended_sections)
            + "\n"
        )


FORMATS: dict[str, PaperFormat] = {
    "acm": PaperFormat(
        key="acm",
        display_name="ACM-style conference or journal article",
        page_size="US Letter",
        columns=2,
        citation_style="numbered or ACM author-year depending on venue package",
        latex_documentclass=r"\documentclass[sigconf,review]{acmart}",
        latex_packages=(r"\settopmatter{printacmref=false}", r"\renewcommand\footnotetextcopyrightpermission[1]{}"),
        section_style="numbered sections; concise uppercase-like top-level headings in final ACM class",
        abstract_style="single abstract before CCS concepts and keywords",
        figure_caption="Figure N: caption below figure",
        table_caption="Table N: caption above table",
        bibliography_note="Prefer official ACM template and BibTeX style for final submission.",
        recommended_sections=(
            "Abstract",
            "Introduction",
            "Related Work",
            "Method",
            "Experiments",
            "Discussion",
            "Limitations",
            "Conclusion",
        ),
        output_note="Use generated LaTeX as a portable draft; replace with official ACM files before camera-ready.",
    ),
    "ieee": PaperFormat(
        key="ieee",
        display_name="IEEE conference or journal article",
        page_size="US Letter or A4, depending on venue",
        columns=2,
        citation_style="numeric IEEE citations",
        latex_documentclass=r"\documentclass[conference]{IEEEtran}",
        latex_packages=(r"\usepackage{cite}", r"\IEEEoverridecommandlockouts"),
        section_style="Roman-numbered top-level sections in IEEEtran",
        abstract_style="italic-style abstract block followed by index terms when needed",
        figure_caption="Fig. N. caption below figure",
        table_caption="TABLE N caption above table",
        bibliography_note="References usually count toward IEEE page limits.",
        recommended_sections=(
            "Abstract",
            "Introduction",
            "Related Work",
            "System Model or Method",
            "Experiments",
            "Results",
            "Conclusion",
        ),
        output_note="Use IEEEtran-compatible LaTeX; verify final venue class options manually.",
    ),
    "springer_lncs": PaperFormat(
        key="springer_lncs",
        display_name="Springer LNCS proceedings article",
        page_size="A4",
        columns=1,
        citation_style="numbered LNCS citations",
        latex_documentclass=r"\documentclass[runningheads]{llncs}",
        latex_packages=(r"\usepackage{graphicx}", r"\usepackage{booktabs}"),
        section_style="numbered sections and subsections; compact single-column layout",
        abstract_style="Abstract environment with keywords after abstract",
        figure_caption="Fig. N. caption below figure",
        table_caption="Table N. caption above table",
        bibliography_note="Use Springer splncs04 bibliography style for final submission.",
        recommended_sections=(
            "Abstract",
            "Introduction",
            "Related Work",
            "Proposed Method",
            "Experiments",
            "Conclusion",
        ),
        output_note="Generated draft follows LNCS structure; official class file is required for final compile.",
    ),
    "chinese_thesis": PaperFormat(
        key="chinese_thesis",
        display_name="Chinese thesis-style manuscript",
        page_size="A4",
        columns=1,
        citation_style="GB/T 7714-style numeric references",
        latex_documentclass=r"\documentclass[UTF8]{ctexbook}",
        latex_packages=(r"\usepackage{geometry}", r"\geometry{left=3cm,right=2.5cm,top=3cm,bottom=2.5cm}"),
        section_style="chapter/section hierarchy with Chinese thesis numbering",
        abstract_style="Chinese abstract plus optional English abstract and keywords",
        figure_caption="\u56fe N-M caption below figure",
        table_caption="\u8868 N-M caption above table",
        bibliography_note="School-specific thesis rules override this generic profile.",
        recommended_sections=(
            "\u6458\u8981",
            "Abstract",
            "\u7b2c1\u7ae0 \u7eea\u8bba",
            "\u7b2c2\u7ae0 \u76f8\u5173\u5de5\u4f5c",
            "\u7b2c3\u7ae0 \u65b9\u6cd5",
            "\u7b2c4\u7ae0 \u5b9e\u9a8c\u4e0e\u5206\u6790",
            "\u7b2c5\u7ae0 \u603b\u7ed3\u4e0e\u5c55\u671b",
        ),
        output_note="This is a generic thesis profile; university-provided template should override it.",
    ),
}


def get_paper_format(key: str) -> PaperFormat:
    try:
        return FORMATS[key]
    except KeyError as exc:
        supported = ", ".join(sorted(FORMATS))
        raise ValueError(f"Unsupported paper format: {key}. Supported: {supported}") from exc


def write_format_profile(path: Path, paper_format: PaperFormat) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(paper_format), indent=2, ensure_ascii=False), encoding="utf-8")
