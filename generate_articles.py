"""
SEO Article Generator for honestpartners.ru
Генерирует HTML-статьи про Честный Знак для разных категорий товаров.

Установка:
  pip install anthropic

Запуск (все статьи):
  python generate_articles.py

Запуск (только N новых, для daily cron):
  python generate_articles.py --limit 3

Результат: папка articles/ с HTML-файлами
"""

import os
import re
import sys
import time
import anthropic

# ──────────────────────────────────────────
# НАСТРОЙКИ
# ──────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")  # или вставь ключ прямо сюда
OUTPUT_DIR = "articles"
SITE_URL = "https://www.honestpartners.ru"
BRAND_COLOR = "#10b77f"

# ──────────────────────────────────────────
# ТЕМЫ СТАТЕЙ
# Формат: (slug, title, category, keywords)
# ──────────────────────────────────────────
TOPICS = [
    # ОДЕЖДА
    ("chestnyj-znak-odezhda",          "Честный знак для одежды: пошаговая инструкция для продавцов WB и Ozon", "Одежда", "честный знак одежда, маркировка одежды wb ozon"),
    ("markirovka-odezhdy-wb",          "Маркировка одежды на Wildberries: требования и штрафы в 2025 году",      "Одежда", "маркировка одежды wildberries, честный знак wb"),
    ("kak-poluchit-km-odezhda",        "Как получить коды маркировки для одежды: инструкция для ИП и ООО",       "Одежда", "коды маркировки одежда, км честный знак"),
    ("shtraf-za-markirovku-odezhdy",   "Штраф за отсутствие маркировки одежды: суммы и как избежать",            "Одежда", "штраф маркировка одежда, честный знак нарушения"),

    # ОБУВЬ
    ("chestnyj-znak-obuv",             "Честный знак для обуви: что нужно знать продавцам на маркетплейсах",     "Обувь", "честный знак обувь, маркировка обуви"),
    ("markirovka-obuvi-ozon",          "Маркировка обуви на Ozon: пошаговая инструкция 2025",                    "Обувь", "маркировка обуви ozon, честный знак ozon"),
    ("kody-markirovki-obuv",           "Коды маркировки для обуви: как заказать через Честный ЗНАК",              "Обувь", "коды маркировки обувь, честный знак обувь инструкция"),

    # БАДы
    ("chestnyj-znak-bad",              "Честный знак для БАД: обязательная маркировка биодобавок",               "БАДы", "честный знак БАД, маркировка биодобавок"),
    ("markirovka-bad-2025",            "Маркировка БАД в 2025 году: сроки, штрафы, как подготовиться",           "БАДы", "маркировка бад 2025, честный знак биодобавки"),
    ("km-dlya-bad-wb",                 "КМ для БАД на Wildberries: как оформить без ошибок",                     "БАДы", "коды маркировки бад wb, честный знак бад wb"),

    # ПАРФЮМ
    ("chestnyj-znak-parfyum",          "Честный знак для парфюмерии: маркировка духов и туалетной воды",         "Парфюм", "честный знак парфюм, маркировка парфюмерии"),
    ("markirovka-parfyumerii-ozon-wb", "Маркировка парфюмерии на Ozon и WB: что изменилось в 2025",              "Парфюм", "маркировка парфюм ozon wb, честный знак духи"),
    ("kak-nанести-km-parfyum",         "Как нанести КМ на флакон духов: требования Честного Знака",              "Парфюм", "нанесение кодов маркировки парфюм, км духи"),

    # ИГРУШКИ
    ("chestnyj-znak-igrushki",         "Честный знак для игрушек: маркировка детских товаров",                   "Игрушки", "честный знак игрушки, маркировка детских товаров"),
    ("markirovka-igrushek-2025",       "Маркировка игрушек в 2025 году: сроки и требования",                     "Игрушки", "маркировка игрушек 2025, честный знак игрушки wb"),
    ("km-dlya-igrushek-wb",            "КМ для игрушек на Wildberries: пошаговая инструкция",                    "Игрушки", "коды маркировки игрушки wb, честный знак игрушки wildberries"),

    # ОБЩИЕ
    ("chto-takoe-chestnyj-znak",       "Что такое Честный знак и почему он обязателен для продавцов",            "Общее", "что такое честный знак, честный знак для продавцов"),
    ("chestnyj-znak-wb-ozon-yandex",   "Честный знак на WB, Ozon и Яндекс.Маркет: полное руководство",          "Общее", "честный знак маркетплейсы, маркировка wb ozon яндекс маркет"),
    ("stoimost-km-chestnyj-znak",      "Сколько стоят коды маркировки: цены и как сэкономить",                   "Общее", "стоимость кодов маркировки, цена честный знак км"),
]


# ──────────────────────────────────────────
# ШАБЛОН HTML-СТАТЬИ
# ──────────────────────────────────────────
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{title} | Честные Партнёры</title>
<meta name="description" content="{meta_description}"/>
<link rel="canonical" href="{site_url}/articles/{slug}.html"/>
<meta property="og:title" content="{title}"/>
<meta property="og:description" content="{meta_description}"/>
<meta property="og:url" content="{site_url}/articles/{slug}.html"/>
<meta property="og:site_name" content="Честные Партнёры"/>
<link rel="icon" href="../images/logo.jpg"/>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet"/>
<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = {{
    theme: {{
      extend: {{
        colors: {{ primary: '#10b77f', 'primary-dark': '#0ea371' }},
        fontFamily: {{ sans: ['Inter', 'sans-serif'] }}
      }}
    }}
  }}
</script>
<!-- Yandex.Metrika -->
<script type="text/javascript">
(function(m,e,t,r,i,k,a){{m[i]=m[i]||function(){{(m[i].a=m[i].a||[]).push(arguments)}};
m[i].l=1*new Date();k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)}})
(window,document,"script","https://mc.yandex.ru/metrika/tag.js","ym");
ym(106807420,"init",{{clickmap:true,trackLinks:true,accurateTrackBounce:true,webvisor:true}});
</script>
<noscript><div><img src="https://mc.yandex.ru/watch/106807420" style="position:absolute;left:-9999px;" alt=""/></div></noscript>
<!-- Schema.org -->
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{title}",
  "description": "{meta_description}",
  "author": {{ "@type": "Organization", "name": "Честные Партнёры" }},
  "publisher": {{
    "@type": "Organization",
    "name": "Честные Партнёры",
    "url": "{site_url}"
  }},
  "mainEntityOfPage": "{site_url}/articles/{slug}.html"
}}
</script>
</head>
<body class="font-sans bg-white text-gray-900">

<!-- NAV -->
<nav class="sticky top-0 z-50 bg-white border-b border-gray-100 shadow-sm">
  <div class="max-w-3xl mx-auto px-4 h-14 flex items-center justify-between">
    <a href="{site_url}/" class="flex items-center gap-2">
      <img src="../images/logo.jpg" alt="Честные Партнёры" class="h-8 w-auto"/>
      <span class="font-bold text-gray-900 hidden sm:block">Честные Партнёры</span>
    </a>
    <a href="{site_url}/#contact"
       class="bg-primary text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-primary-dark transition-colors">
      Получить КМ
    </a>
  </div>
</nav>

<!-- BREADCRUMB -->
<div class="max-w-3xl mx-auto px-4 pt-4 pb-2">
  <nav class="text-sm text-gray-500 flex gap-1 flex-wrap">
    <a href="{site_url}/" class="hover:text-primary">Главная</a>
    <span>/</span>
    <a href="{site_url}/articles/" class="hover:text-primary">Статьи</a>
    <span>/</span>
    <span class="text-gray-700">{category}</span>
  </nav>
</div>

<!-- ARTICLE -->
<main class="max-w-3xl mx-auto px-4 pb-16">
  <article>
    <header class="py-6 border-b border-gray-100 mb-8">
      <span class="inline-block bg-primary/10 text-primary text-xs font-semibold px-3 py-1 rounded-full mb-3">{category}</span>
      <h1 class="text-2xl sm:text-3xl font-extrabold text-gray-900 leading-tight mb-3">{title}</h1>
      <p class="text-gray-500 text-sm">Честные Партнёры &mdash; сервис маркировки для продавцов WB, Ozon и Яндекс.Маркет</p>
    </header>

    <div class="prose prose-gray max-w-none
                prose-headings:font-bold prose-headings:text-gray-900
                prose-h2:text-xl prose-h2:mt-8 prose-h2:mb-3
                prose-h3:text-lg prose-h3:mt-6 prose-h3:mb-2
                prose-p:text-gray-700 prose-p:leading-relaxed prose-p:mb-4
                prose-li:text-gray-700 prose-ul:my-3 prose-ol:my-3
                prose-strong:text-gray-900
                prose-a:text-primary prose-a:no-underline hover:prose-a:underline">
      {body_html}
    </div>

    <!-- CTA BLOCK -->
    <div class="mt-12 rounded-2xl bg-gradient-to-br from-primary/10 to-emerald-50 border border-primary/20 p-6 sm:p-8">
      <h2 class="text-xl font-extrabold text-gray-900 mb-2">Нужны коды маркировки?</h2>
      <p class="text-gray-600 mb-5">Честные Партнёры выдают КМ <strong>от 1 ₽</strong> — это в 4–6 раз дешевле конкурентов. Работаем с WB, Ozon и Яндекс.Маркет.</p>
      <div class="flex flex-col sm:flex-row gap-3">
        <a href="https://t.me/honestpartners_bot"
           class="inline-flex items-center justify-center gap-2 bg-[#2AABEE] text-white font-semibold px-5 py-3 rounded-xl hover:opacity-90 transition-opacity">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.562 8.248-1.97 9.289c-.145.658-.537.818-1.084.508l-3-2.21-1.447 1.394c-.16.16-.295.295-.605.295l.213-3.053 5.56-5.023c.242-.213-.054-.333-.373-.12l-6.871 4.326-2.962-.924c-.643-.204-.657-.643.136-.953l11.57-4.461c.537-.194 1.006.131.833.932z"/></svg>
          Написать в Telegram
        </a>
        <a href="{site_url}/#contact"
           class="inline-flex items-center justify-center gap-2 bg-primary text-white font-semibold px-5 py-3 rounded-xl hover:bg-primary-dark transition-colors">
          Оставить заявку
        </a>
      </div>
    </div>
  </article>
</main>

<!-- FOOTER -->
<footer class="border-t border-gray-100 py-6 text-center text-sm text-gray-500">
  <div class="max-w-3xl mx-auto px-4">
    <a href="{site_url}/" class="font-semibold text-gray-700 hover:text-primary">Честные Партнёры</a>
    &nbsp;&middot;&nbsp;
    <a href="{site_url}/privacy.html" class="hover:text-primary">Политика конфиденциальности</a>
    &nbsp;&middot;&nbsp;
    ИП Галеев Р.А. &middot; ИНН 165914859807
  </div>
</footer>

</body>
</html>
"""


# ──────────────────────────────────────────
# ПРОМПТ ДЛЯ CLAUDE
# ──────────────────────────────────────────
def build_prompt(title: str, category: str, keywords: str) -> str:
    return f"""Напиши SEO-статью для сайта сервиса маркировки "Честные Партнёры".

Тема: {title}
Категория: {category}
Ключевые слова: {keywords}
Сайт: https://www.honestpartners.ru/

ТРЕБОВАНИЯ:
- Язык: русский, деловой но понятный
- Объём: 600–900 слов
- Структура: введение, 3–5 разделов с подзаголовками H2, заключение
- Используй актуальные данные про систему "Честный ЗНАК" в России
- Упомяни что маркировка обязательна, есть штрафы за нарушение
- В конце — 1 абзац про то, что "Честные Партнёры" помогают получить КМ от 1 ₽
- НЕ упоминай конкурентов по имени

ФОРМАТ ОТВЕТА:
Верни ТОЛЬКО HTML-разметку (без тегов html/head/body).
Используй теги: <h2>, <h3>, <p>, <ul>, <li>, <strong>, <ol>.
Первый тег должен быть <p> с введением (НЕ <h2>).
НЕ добавляй атрибуты class или style — стили уже заданы.

Пример структуры:
<p>Введение...</p>
<h2>Раздел 1</h2>
<p>Текст...</p>
<ul><li>Пункт</li></ul>
<h2>Раздел 2</h2>
<p>Текст...</p>
...
<h2>Заключение</h2>
<p>Текст про Честные Партнёры...</p>
"""


def extract_meta_description(body_html: str) -> str:
    """Берём первый <p> как meta description, обрезаем до 160 символов."""
    match = re.search(r"<p>(.*?)</p>", body_html, re.DOTALL)
    if match:
        text = re.sub(r"<[^>]+>", "", match.group(1)).strip()
        return text[:157] + "..." if len(text) > 160 else text
    return "Честный знак — маркировка товаров для продавцов на WB, Ozon и Яндекс.Маркет от 1 ₽ за код."


def generate_article(client: anthropic.Anthropic, topic: tuple) -> str:
    slug, title, category, keywords = topic

    print(f"  Генерирую: {title[:60]}...")

    message = client.messages.create(
        model="claude-haiku-4-5",   # Haiku — быстро и дёшево для контента
        max_tokens=2048,
        messages=[{"role": "user", "content": build_prompt(title, category, keywords)}],
    )

    body_html = message.content[0].text.strip()
    meta_description = extract_meta_description(body_html)

    html = HTML_TEMPLATE.format(
        title=title,
        slug=slug,
        category=category,
        meta_description=meta_description,
        body_html=body_html,
        site_url=SITE_URL,
    )

    return html


def main():
    # Парсим --limit N из аргументов
    limit = None
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            limit = int(sys.argv[idx + 1])

    if not ANTHROPIC_API_KEY:
        print("ОШИБКА: Установи переменную среды ANTHROPIC_API_KEY")
        print("  Windows: set ANTHROPIC_API_KEY=sk-ant-...")
        print("  или вставь ключ в строку ANTHROPIC_API_KEY в начале скрипта")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    mode = f"(лимит: {limit} новых)" if limit else f"(всего тем: {len(TOPICS)})"
    print(f"\nСтарт генерации статей {mode}\n")

    all_existing = []   # уже были раньше
    new_generated = []  # сгенерировали сейчас
    new_count = 0

    for i, topic in enumerate(TOPICS, 1):
        slug, title, category, _ = topic
        output_path = os.path.join(OUTPUT_DIR, f"{slug}.html")

        if os.path.exists(output_path):
            all_existing.append((slug, title, category))
            continue

        if limit and new_count >= limit:
            break

        print(f"[{new_count + 1}/{limit or len(TOPICS)}]", end=" ")
        try:
            html = generate_article(client, topic)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)
            new_generated.append((slug, title, category))
            new_count += 1
            print(f"  Сохранено: {slug}.html")

            if new_count < (limit or len(TOPICS)):
                time.sleep(1.5)

        except Exception as e:
            print(f"  ОШИБКА: {e}")
            time.sleep(3)

    if not new_generated:
        print("Нет новых тем для генерации — все статьи уже созданы.")
    else:
        print(f"\nНовых статей: {len(new_generated)}")

    # Обновляем индекс (объединяем старые + новые)
    all_articles = all_existing + new_generated
    generate_index(all_articles)
    print(f"Всего статей на сайте: {len(all_articles)}")


def generate_index(articles: list) -> None:
    """Страница списка всех статей."""
    cards = ""
    by_category = {}
    for slug, title, category in articles:
        by_category.setdefault(category, []).append((slug, title))

    for category, items in by_category.items():
        cards += f'<div class="mb-8"><h2 class="text-lg font-bold text-gray-900 mb-3 pb-2 border-b">{category}</h2><ul class="space-y-2">'
        for slug, title in items:
            cards += f'<li><a href="{slug}.html" class="text-primary hover:underline font-medium">{title}</a></li>'
        cards += "</ul></div>"

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Статьи о маркировке Честный Знак | Честные Партнёры</title>
<meta name="description" content="Полезные статьи о маркировке Честный Знак для продавцов на Wildberries, Ozon и Яндекс.Маркет."/>
<link rel="canonical" href="{SITE_URL}/articles/"/>
<link rel="icon" href="../images/logo.jpg"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet"/>
<script src="https://cdn.tailwindcss.com"></script>
<script>tailwind.config={{theme:{{extend:{{colors:{{primary:'#10b77f'}},fontFamily:{{sans:['Inter','sans-serif']}}}}}}}}</script>
</head>
<body class="font-sans bg-gray-50">
<nav class="sticky top-0 z-50 bg-white border-b shadow-sm">
  <div class="max-w-3xl mx-auto px-4 h-14 flex items-center justify-between">
    <a href="{SITE_URL}/" class="flex items-center gap-2">
      <img src="../images/logo.jpg" alt="Честные Партнёры" class="h-8 w-auto"/>
      <span class="font-bold hidden sm:block">Честные Партнёры</span>
    </a>
    <a href="{SITE_URL}/#contact" class="bg-primary text-white text-sm font-semibold px-4 py-2 rounded-lg hover:opacity-90">Получить КМ</a>
  </div>
</nav>
<main class="max-w-3xl mx-auto px-4 py-10">
  <h1 class="text-2xl font-extrabold text-gray-900 mb-2">Статьи о маркировке Честный Знак</h1>
  <p class="text-gray-500 mb-8">Полезные материалы для продавцов на WB, Ozon и Яндекс.Маркет</p>
  {cards}
</main>
<footer class="border-t bg-white py-6 text-center text-sm text-gray-500">
  <a href="{SITE_URL}/" class="font-semibold text-gray-700 hover:text-primary">Честные Партнёры</a>
  &nbsp;&middot;&nbsp; ИП Галеев Р.А. &middot; ИНН 165914859807
</footer>
</body>
</html>"""

    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print("  Создан: articles/index.html")


if __name__ == "__main__":
    main()
