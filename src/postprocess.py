import re
from html import unescape
from typing import List, Tuple
import urllib.parse
from . import config


def _slugify_telegraph(text: str) -> str:
    """
    Создает 'slug' для якоря, который будет использоваться в ID, заменяя пробелы на дефисы.
    Это имитирует базовую логику Telegra.ph.
    """
    return text.replace(' ', '-')

def _extract_username_from_tme(url: str) -> str:
    """Возвращает username телеграм-канала из ссылки t.me, иначе пустую строку."""
    m = re.search(r"https?://t\.me/([^/]+)/", url)
    return m.group(1).lower() if m else ""


def _split_news_blocks(html: str) -> Tuple[str, List[dict]]:
    """Разбивает HTML статьи на префикс (до первой новости) и список блоков новостей."""
    blocks = []
    h4_pattern = re.compile(r"<h4>(.*?)</h4>", re.DOTALL | re.IGNORECASE)
    positions = [(m.start(), m.end(), m.group(1)) for m in h4_pattern.finditer(html)]

    if not positions:
        return html, []

    prefix = html[: positions[0][0]]
    for idx, (start, end, h4_inner) in enumerate(positions):
        next_start = positions[idx + 1][0] if idx + 1 < len(positions) else len(html)
        block_html = html[start:next_start]
        href_match = re.search(r"<a\s+href=\"([^\"]+)\"", h4_inner, re.IGNORECASE)
        href = href_match.group(1) if href_match else ""
        title_text = unescape(re.sub(r"<[^>]+>", "", h4_inner).strip())

        blocks.append({
            "h4_inner": h4_inner,
            "href": href,
            "title": title_text,
            "html": block_html,
        })

    return prefix, blocks


def _prepare_anchors(blocks: List[dict]) -> List[dict]:
    """Добавляет id к тегу <h4> каждого блока, имитируя логику Telegra.ph."""
    updated = []
    for block in blocks:
        # Создаем якорь на основе текста заголовка
        anchor_id = _slugify_telegraph(block["title"])
        # Заменяем первый тег <h4> на <h4 id=\"...\">
        new_html = re.sub(r"<h4>", f"<h4 id=\"{anchor_id}\">", block["html"], count=1, flags=re.IGNORECASE)
        updated.append({**block, "anchor_id": anchor_id, "html": new_html})
    return updated


def _build_toc(blocks: List[dict]) -> str:
    """Строит HTML-навигацию по заголовкам в разрешённом формате."""
    if not blocks:
        return ""
    
    # Определяем стиль навигации из конфигурации
    nav_style = getattr(config, 'NAVIGATION_STYLE', 'list').lower()
    
    lines = []
    for b in blocks:
        # URL-кодируем якорь для href, чтобы ссылка была валидной
        encoded_anchor = urllib.parse.quote(b['anchor_id'])
        internal = f"<a href=\"#{encoded_anchor}\">{b['title']}</a>"
        external = f" — [<a href=\"{b['href']}\">источник</a>]" if b.get("href") else ""
        
        if nav_style == "list":
            lines.append(f"<li>{internal}{external}</li>")
        else:  # paragraph style
            lines.append(f"• {internal}{external}")
    
    title = config.NAVIGATION_TITLE or "Навигация"
    
    if nav_style == "list":
        # Используем ul/li с пустыми p тегами для изоляции от конфликтов с CSS Telegra.ph
        # Пустые <p></p> теги помогают избежать применения стилей к ul/li элементам
        items = "".join(lines)
        return f"<h3>{title}</h3><p></p><ul>{items}</ul><p></p><br>"
    else:
        # Используем p с <br> для совместимости со старым форматом
        items = "<br>".join(lines)
        return f"<h3>{title}</h3><p>{items}</p><br>"

def _reorder_sections(html: str) -> str:
    """Переупорядочивает секции в правильном порядке."""
    # Ищем все секции h3 и их содержимое
    h3_pattern = re.compile(r'<h3[^>]*>(.*?)</h3>', re.DOTALL | re.IGNORECASE)
    sections = []
    
    # Находим все секции
    for match in h3_pattern.finditer(html):
        section_title = match.group(1).strip()
        section_start = match.start()
        
        # Находим конец секции (следующий h3 или конец документа)
        next_h3 = h3_pattern.search(html, section_start + 1)
        section_end = next_h3.start() if next_h3 else len(html)
        
        section_content = html[section_start:section_end]
        sections.append({
            'title': section_title,
            'content': section_content,
            'start': section_start,
            'end': section_end
        })
    
    if not sections:
        return html
    
    # Определяем правильный порядок секций
    section_order = [
        "Официальные источники",
        "Срочно к действию", 
        "Другие источники",
        "Стратегические инсайты"
    ]
    
    # Сортируем секции по правильному порядку
    ordered_sections = []
    for target_title in section_order:
        for section in sections:
            if target_title.lower() in section['title'].lower():
                ordered_sections.append(section)
                break
    
    # Добавляем секции, которые не попали в список
    for section in sections:
        if section not in ordered_sections:
            ordered_sections.append(section)
    
    # Собираем HTML заново
    prefix_end = sections[0]['start'] if sections else len(html)
    prefix = html[:prefix_end]
    
    body_parts = [prefix]
    for section in ordered_sections:
        body_parts.append(section['content'])
    
    return "".join(body_parts)


def add_navigation_and_split(html: str, official_channels: List[str]) -> str:
    """Добавляет раздел «Навигация» и разбивает новости на два раздела по источнику."""
    official_set = {c.lower() for c in official_channels}

    prefix, blocks = _split_news_blocks(html)
    if not blocks:
        return html

    # Готовим якоря, совместимые с Telegra.ph
    blocks = _prepare_anchors(blocks)

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

    # Собираем контент без навигации
    body_parts: List[str] = [prefix]
    if config.ENABLE_SECTION_SPLIT:
        if official_blocks:
            body_parts.append(f"<h3>{config.OFFICIAL_SECTION_TITLE}</h3>")
            body_parts.extend(official_blocks)
        if other_blocks:
            body_parts.append(f"<h3>{config.OTHER_SECTION_TITLE}</h3>")
            body_parts.extend(other_blocks)
    else:
        body_parts.extend([b["html"] for b in blocks])

    body_html = "".join(body_parts)
    
    # Переупорядочиваем секции в правильном порядке (если включено)
    if getattr(config, 'ENABLE_SECTION_REORDER', True):
        body_html = _reorder_sections(body_html)

    # Вставляем навигацию строго ПЕРЕД первым <h3>
    if toc_html:
        first_h3 = re.search(r"<h3[^>]*>", body_html, re.IGNORECASE)
        if first_h3:
            insert_at = first_h3.start()
            return body_html[:insert_at] + toc_html + body_html[insert_at:]
        else:
            return toc_html + body_html

    return body_html



