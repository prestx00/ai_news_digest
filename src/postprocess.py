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
    # Паттерн для поиска h4 тегов, включая те, что с атрибутами
    h4_pattern = re.compile(r"(<h4[^>]*>.*?</h4>)", re.DOTALL | re.IGNORECASE)
    # Паттерн для извлечения содержимого и атрибутов из h4 тега
    h4_content_pattern = re.compile(r"<h4[^>]*>(.*?)</h4>", re.DOTALL | re.IGNORECASE)
    
    # Находим все полные блоки h4
    all_h4_tags = [m.group(1) for m in h4_pattern.finditer(html)]
    if not all_h4_tags:
        return html, []

    # Находим позиции, чтобы отделить префикс
    first_h4_match = h4_pattern.search(html)
    prefix = html[:first_h4_match.start()] if first_h4_match else html
    
    # Разделяем основной контент по h4 тегам
    # В `split` первый элемент будет пустой строкой, если html начинается с h4, отбрасываем его
    content_after_prefix = html[first_h4_match.start():]
    split_content = h4_pattern.split(content_after_prefix)[1:]
    
    # Собираем блоки: тег h4 + следующий за ним контент
    news_html_blocks = [tag + content for tag, content in zip(split_content[::2], split_content[1::2])]

    for block_html in news_html_blocks:
        h4_tag_match = h4_pattern.search(block_html)
        if not h4_tag_match:
            continue
        
        h4_full_tag = h4_tag_match.group(1)
        h4_inner_match = h4_content_pattern.search(h4_full_tag)
        h4_inner = h4_inner_match.group(1) if h4_inner_match else ""

        href_match = re.search(r"<a\s+href=\"([^\"]+)\"", h4_inner, re.IGNORECASE)
        href = href_match.group(1) if href_match else ""
        
        title_text = unescape(re.sub(r"<[^>]+>", "", h4_inner).strip())
        
        category_match = re.search(r"data-category=\"([^\"]+)\"", h4_full_tag, re.IGNORECASE)
        category = category_match.group(1) if category_match else "Без категории"

        blocks.append({
            "h4_inner": h4_inner,
            "href": href,
            "title": title_text,
            "html": block_html.strip(),
            "category": category,
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
    """Строит HTML-навигацию по заголовкам в разрешённом формате с категориями."""
    if not blocks:
        return ""

    # Группируем блоки по категориям
    categorized_blocks = {}
    category_order = [] # Сохраняем порядок категорий, как они появляются в статье
    for block in blocks:
        category = block.get("category", "Другие источники")
        if category not in categorized_blocks:
            categorized_blocks[category] = []
            category_order.append(category)
        categorized_blocks[category].append(block)

    # Определяем стиль навигации из конфигурации
    nav_style = getattr(config, 'NAVIGATION_STYLE', 'list').lower()
    
    toc_parts = []
    title = config.NAVIGATION_TITLE or "Навигация"
    toc_parts.append(f"<h3>{title}</h3>")

    # Используем сохраненный порядок категорий
    for category in category_order:
        cat_blocks = categorized_blocks[category]
        toc_parts.append(f"<p><strong>{category}</strong></p>")
        lines = []
        for b in cat_blocks:
            # URL-кодируем якорь для href, чтобы ссылка была валидной
            encoded_anchor = urllib.parse.quote(b['anchor_id'])
            internal = f"<a href=\"#{encoded_anchor}\">{b['title']}</a>"
            external = f" — [<a href=\"{b['href']}\">источник</a>]" if b.get("href") else ""
            
            if nav_style == "list":
                lines.append(f"<li>{internal}{external}</li>")
            else:  # paragraph style
                lines.append(f"• {internal}{external}")
        
        if nav_style == "list":
            items = "".join(lines)
            toc_parts.append(f"<p></p><ul>{items}</ul><p></p>")
        else:
            items = "<br>".join(lines)
            toc_parts.append(f"<p>{items}</p>")

    toc_parts.append("<br>")
    return "".join(toc_parts)




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

    # Вставляем навигацию
    if toc_html:
        # Если разделение на секции включено, ищем <h3> для вставки навигации.
        # Иначе, ищем первую новость (<h4>), чтобы вставить навигацию перед ней.
        if config.ENABLE_SECTION_SPLIT:
            insertion_marker = re.search(r"<h3[^>]*>", body_html, re.IGNORECASE)
        else:
            insertion_marker = re.search(r"<h4[^>]*>", body_html, re.IGNORECASE)

        if insertion_marker:
            insert_at = insertion_marker.start()
            return body_html[:insert_at] + toc_html + body_html[insert_at:]
        else:
            # Если маркер не найден (например, нет новостей), добавляем TOC в конец.
            return body_html + toc_html

    return body_html



