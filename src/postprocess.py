import re
from html import unescape
from typing import List, Tuple
from . import config


def _extract_username_from_tme(url: str) -> str:
    """Возвращает username телеграм-канала из ссылки t.me, иначе пустую строку."""
    m = re.search(r"https?://t\.me/([^/]+)/", url)
    return m.group(1).lower() if m else ""


def _split_news_blocks(html: str) -> Tuple[str, List[dict]]:
    """Разбивает HTML статьи на префикс (до первой новости) и список блоков новостей.

    Блок новости определяется как:
      <h4>...</h4> [включая последующие <p>... и завершающий <br>] до следующего <h4> или конца текста.
    """
    blocks = []

    # Найдем все заголовки h4
    h4_pattern = re.compile(r"<h4>(.*?)</h4>", re.DOTALL | re.IGNORECASE)
    positions = [(m.start(), m.end(), m.group(1)) for m in h4_pattern.finditer(html)]

    if not positions:
        return html, []

    prefix = html[: positions[0][0]]
    for idx, (start, end, h4_inner) in enumerate(positions):
        next_start = positions[idx + 1][0] if idx + 1 < len(positions) else len(html)
        block_html = html[start:next_start]

        # Извлекаем href из <h4><a href="...">
        href_match = re.search(r"<a\s+href=\"([^\"]+)\"", h4_inner, re.IGNORECASE)
        href = href_match.group(1) if href_match else ""

        # Текст заголовка без тегов
        title_text = re.sub(r"<[^>]+>", "", h4_inner).strip()
        title_text = unescape(title_text)

        blocks.append({
            "h4_inner": h4_inner,
            "href": href,
            "title": title_text,
            "html": block_html,
        })

    return prefix, blocks


def _inject_ids(blocks: List[dict]) -> List[dict]:
    """Добавляет id к тегу <h4> каждого блока и возвращает новый html блока."""
    updated = []
    for i, block in enumerate(blocks, start=1):
        anchor_id = f"n{i}"
        # Заменяем первый тег <h4> на <h4 id="nX">
        new_html = re.sub(r"<h4>", f"<h4 id=\"{anchor_id}\">", block["html"], count=1, flags=re.IGNORECASE)
        updated.append({**block, "anchor_id": anchor_id, "html": new_html})
    return updated


def _build_toc(blocks: List[dict]) -> str:
    """Строит HTML-навигацию по заголовкам в разрешённом формате.

    На каждый пункт даём 2 ссылки:
    - на якорь внутри статьи (#id)
    - на исходный источник поста (если есть)
    Это обеспечивает кликабельность даже если атрибут id будет вырезан движком.
    """
    if not blocks:
        return ""
    lines = []
    for b in blocks:
        internal = f"<a href=\"#{b['anchor_id']}\">{b['title']}</a>"
        external = f" — <a href=\"{b['href']}\">источник</a>" if b.get("href") else ""
        lines.append(f"• {internal}{external}")
    items = "<br>".join(lines)
    title = config.NAVIGATION_TITLE or "Навигация"
    return f"<h3>{title}</h3><p>{items}</p><br>"


def add_navigation_and_split(html: str, official_channels: List[str]) -> str:
    """Добавляет раздел «Навигация» и разбивает новости на два раздела по источнику.

    - official_channels: список username телеграм-каналов (без @), считающихся официальными.
    """
    official_set = {c.lower() for c in official_channels}

    prefix, blocks = _split_news_blocks(html)
    if not blocks:
        # Ничего не нашли — просто вернём исходный html
        return html

    blocks = _inject_ids(blocks)

    # TOC
    toc_html = _build_toc(blocks) if config.ENABLE_TOC else ""

    # Разделение на группы
    official_blocks = []
    other_blocks = []
    for b in blocks:
        username = _extract_username_from_tme(b["href"]) if b["href"] else ""
        if username in official_set:
            official_blocks.append(b["html"])
        else:
            other_blocks.append(b["html"])

    # Удаляем оригинальные секции h3 из префикса (если требуется)
    if config.STRIP_ORIGINAL_SECTIONS:
        def strip_original_sections(s: str) -> str:
            sections = config.STRIP_H3_TITLES or []
            for name in sections:
                s = re.sub(rf"<h3>[^<]*{re.escape(name)}[^<]*</h3>", "", s, flags=re.IGNORECASE)
            return s

        prefix = strip_original_sections(prefix)

    # Собираем новую структуру
    rebuilt = [prefix, toc_html]

    if config.ENABLE_SECTION_SPLIT:
        if official_blocks:
            rebuilt.append(f"<h3>{config.OFFICIAL_SECTION_TITLE}</h3>")
            rebuilt.extend(official_blocks)

        if other_blocks:
            rebuilt.append(f"<h3>{config.OTHER_SECTION_TITLE}</h3>")
            rebuilt.extend(other_blocks)
    else:
        # Если секции выключены — восстанавливаем исходный порядок без заголовков
        rebuilt.extend([b["html"] for b in blocks])

    return "".join(rebuilt)


