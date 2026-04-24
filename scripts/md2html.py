#!/usr/bin/env python3
"""
Markdown -> mdnice-styled HTML renderer (self-contained).

Usage:
    python scripts/md2html.py <input.md> [--theme 橙心] [-o output.html]

Themes live in ../assets/mdnice_themes/*.html (mdnice editor exports).
Dependencies: mistune>=3, pygments.
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

try:
    import mistune
    import pygments
    from pygments.lexers import get_lexer_by_name, guess_lexer
    from pygments.formatters import HtmlFormatter
except ImportError as e:
    sys.stderr.write(
        f"Missing dependency: {e}. Install with:\n"
        f"  pip install 'mistune>=3' pygments\n"
    )
    sys.exit(2)


THEMES_DIR = Path(__file__).resolve().parent.parent / "assets" / "mdnice_themes"


class Render(mistune.HTMLRenderer):
    def __init__(self, theme: str):
        super().__init__(escape=True, allow_harmful_protocols=None)
        theme_file = THEMES_DIR / f"{theme}.html"
        if not theme_file.exists():
            available = sorted(p.stem for p in THEMES_DIR.glob("*.html"))
            raise ValueError(
                f"Theme '{theme}' not found. Available: {', '.join(available)}"
            )
        self.theme = self._load_theme(theme_file)

    @staticmethod
    def _clean(text: str) -> str:
        return (
            text.replace(' id="nice"', "")
            .replace(' data-tool="mdnice编辑器"', "")
            .replace(' data-website="https://www.mdnice.com"', "")
            .strip()
        )

    def _load_theme(self, theme_file: Path) -> dict:
        with open(theme_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        c = self._clean
        return {
            "section": c(re.findall(r"<section [^>]*>", lines[0])[0]),
            "h1": c(re.findall(r"<h1.*</h1>", lines[0])[0]),
            "h2": c(re.findall(r"<h2.*</h2>", lines[1])[0]),
            "h3": c(re.findall(r"<h3.*</h3>", lines[2])[0]),
            "h4": c(re.findall(r"<h4.*</h4>", lines[3])[0]),
            "h5": c(re.findall(r"<h5.*</h5>", lines[4])[0]),
            "hr": c(re.findall(r"<hr.*>\n", lines[5])[0]),
            "strong": c(re.findall(r"<strong.*</strong>", lines[6])[0]),
            "italic": c(re.findall(r"<em.*</em>", lines[7])[0]),
            "p": c(re.findall(r"<p.*</p>", lines[8])[0]),
            "img": c(re.findall(r"<figure.*</figure>", lines[9])[0]),
            "link": c(re.findall(r"<a.*</a>", lines[10])[0]),
            "ol": c(re.findall(r"<ol.*>\n", lines[11])[0]),
            "li": c(re.findall(r"<li.*</li>", lines[12])[0]),
            "ul": c(re.findall(r"<ul.*>\n", lines[13])[0]),
        }

    def heading(self, text, level):
        return self.theme[f"h{level}"].replace("【文本】", text) + "\n"

    def thematic_break(self) -> str:
        return self.theme["hr"] + "\n"

    def emphasis(self, text):
        return self.theme["italic"].replace("【文本】", text)

    def strong(self, text):
        return self.theme["strong"].replace("【文本】", text)

    def paragraph(self, text):
        return self.theme["p"].replace("【文本】", text) + "\n"

    def link(self, text, url, title=None):
        return self.theme["link"].replace("@LINK", self.safe_url(url)).replace(
            "【文本】", text
        )

    def image(self, text, url, title=None):
        return self.theme["img"].replace("@LINK", self.safe_url(url)).replace(
            "【文本】", text or ""
        )

    def list(self, text, ordered, **attrs):
        if ordered:
            return self.theme["ol"] + text + "</ol>\n"
        return self.theme["ul"] + text + "</ul>\n"

    def list_item(self, text):
        text = re.sub(r"^<p[^>]*>(.*?)</p>\s*$", r"\1", text.strip(), flags=re.DOTALL)
        return self.theme["li"].replace("【文本】", text)

    def block_quote(self, text):
        return (
            '<blockquote style="border-left: 4px solid rgb(239, 112, 96); '
            "margin: 10px 0; padding: 10px 15px; background-color: rgb(255, 249, 249); "
            'color: rgb(111, 111, 111); font-size: 15px; line-height: 1.8em;">'
            + text
            + "</blockquote>\n"
        )

    def codespan(self, text):
        return (
            '<code style="font-size: 14px; padding: 2px 6px; margin: 0 3px; '
            "background-color: rgba(239, 112, 96, 0.1); border-radius: 4px; "
            'color: rgb(239, 112, 96); font-family: Consolas, Monaco, Menlo, monospace;">'
            + text
            + "</code>"
        )

    def table(self, text):
        return (
            '<table style="border-collapse: collapse; margin: 10px auto; width: 100%; '
            'text-align: center; font-size: 14px;">'
            + text
            + "</table>\n"
        )

    def table_head(self, text):
        return "<thead>" + text + "</thead>\n"

    def table_body(self, text):
        return "<tbody>" + text + "</tbody>\n"

    def table_row(self, text):
        return '<tr style="border-top: 1px solid #dfe2e5;">' + text + "</tr>\n"

    def table_cell(self, text, align=None, head=False):
        tag = "th" if head else "td"
        style = "border: 1px solid #dfe2e5; padding: 6px 12px; line-height: 1.5em; "
        if head:
            style += (
                "font-weight: bold; background-color: rgb(239, 112, 96); color: white; "
            )
        else:
            style += "color: rgb(63, 63, 63); "
        if align:
            style += f"text-align: {align}; "
        return f'<{tag} style="{style}">{text}</{tag}>\n'

    def block_code(self, code, info=None):
        if info:
            lexer = get_lexer_by_name(info.split(None, 1)[0], stripall=True)
        else:
            try:
                lexer = guess_lexer(code)
            except Exception:
                lexer = get_lexer_by_name("text", stripall=True)
        code_html = pygments.highlight(
            code,
            lexer,
            HtmlFormatter(style="monokai", noclasses=True, nobackground=True, nowrap=True),
        )
        return (
            '<pre class="custom" style="border-radius: 5px; '
            'box-shadow: rgba(0,0,0,0.55) 0px 2px 10px; margin: 10px 0; padding: 0;">'
            '<code class="hljs" style="display:block; overflow-x:auto; padding:16px; '
            "color:#abb2bf; background:#282c34; border-radius:5px; "
            'font-family: Consolas, Monaco, Menlo, monospace; font-size: 12px;">'
            + code_html
            + "</code></pre>\n"
        )


def md_to_html(md_text: str, theme: str = "橙心") -> str:
    renderer = Render(theme=theme)
    md = mistune.create_markdown(renderer=renderer, plugins=["table", "strikethrough"])
    return renderer.theme["section"] + "\n" + md(md_text) + "</section>"


def main():
    parser = argparse.ArgumentParser(description="Render Markdown -> mdnice-styled HTML")
    parser.add_argument("input", nargs="?", help="Input .md file")
    parser.add_argument("--theme", default="橙心", help="mdnice theme name (default: 橙心)")
    parser.add_argument("-o", "--output", help="Output .html path (default: <input>_<theme>.html)")
    parser.add_argument("--list-themes", action="store_true", help="List available themes and exit")
    args = parser.parse_args()

    if args.list_themes:
        for p in sorted(THEMES_DIR.glob("*.html")):
            print(p.stem)
        return

    if not args.input:
        parser.error("input is required unless --list-themes is given")

    in_path = Path(args.input)
    md_text = in_path.read_text(encoding="utf-8")
    html = md_to_html(md_text, theme=args.theme)

    out_path = Path(args.output) if args.output else in_path.with_name(
        f"{in_path.stem}_{args.theme}.html"
    )
    out_path.write_text(html, encoding="utf-8")
    print(str(out_path))


if __name__ == "__main__":
    main()
