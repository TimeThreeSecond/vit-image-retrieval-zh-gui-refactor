"""Internationalization (i18n) for ViT Image Retrieval GUI.

All user-visible strings are defined here in both English (en) and Chinese (zh).
Usage:  from gui.i18n import t
        btn.setText(t("fe_extract_btn", lang))
"""

STR = {
    "en": {
        # ── MainWindow ──
        "window_title": "ViT Image Retrieval System",
        "tab_extraction": "Feature Extraction",
        "tab_retrieval": "Image Retrieval",
        "lang_en": "EN",
        "lang_zh": "中文",

        # ── Feature Extraction Tab ──
        "fe_title": "Feature Extraction",
        "fe_desc": "Select a folder of images to extract ViT features and build a search index.",
        "fe_dir_label": "Image Directory",
        "fe_no_dir": "No directory selected",
        "fe_browse": "Browse...",
        "fe_index_name": "Index Name (optional):",
        "fe_index_placeholder": "e.g., animals, cars, vacation",
        "fe_extract_btn": "Extract Features",
        "fe_warning_no_dir": "Please select a directory first.",
        "fe_success_title": "Success",
        "fe_success_msg": "Feature extraction completed!\n\nIndex:   {index}\nMetadata: {meta}",
        "fe_error_title": "Error",
        "fe_error_msg": "Feature extraction failed:\n{error}",
        "fe_done": "Done! Index: {index}  |  Metadata: {meta}",

        # ── Retrieval Tab ──
        "rt_index_section": "Search Index",
        "rt_no_index": "No index loaded",
        "rt_no_index_guide": "No index files found  —  go to Feature Extraction tab to build one",
        "rt_no_index_tip": "Switch to the 'Feature Extraction' tab, select an image folder, and click 'Extract Features' to create your first index.",
        "rt_latest_btn": "Latest",
        "rt_latest_tip": "Auto-detect the most recent .faiss file in current folder",
        "rt_load_btn": "Load...",
        "rt_load_tip": "Browse and select a .faiss index file manually",
        "rt_query_section": "Query Image",
        "rt_drop_hint": "Drag & drop an image here\nor click Browse to select",
        "rt_selected": "Selected: {name}",
        "rt_no_query": "No image selected",
        "rt_query_browse": "Browse...",
        "rt_query_tip": "Select a query image from your filesystem",
        "rt_topk": "Top-K results:",
        "rt_search_btn": "Search",
        "rt_search_tip": "Requires: (1) a loaded index, (2) a selected query image",
        "rt_shortcuts": "Shortcuts: Ctrl+O = Open image  |  Ctrl+Enter = Search  |  Ctrl+L = Load index",
        "rt_no_search_yet": "No search performed yet.\nSelect a query image and load an index, then click Search.",
        "rt_no_results": "No results returned.",
        "rt_warning_no_query": "Please select a query image first.",
        "rt_warning_no_index": "Please load an index first.",
        "rt_searching": "Searching...",
        "rt_similarity": "Similarity",
        "rt_distance": "Distance",
        "rt_file": "File",
        "rt_load_error": "Failed to load index:\n{error}",
        "rt_search_error": "Search failed:\n{error}",
        "rt_index_loaded": "{name}  ({count} images)",
        "rt_load_error_title": "Error",

        # ── General ──
        "error": "Error",
        "warning": "Warning",
        "success": "Success",
    },

    "zh": {
        # ── MainWindow ──
        "window_title": "ViT 图像检索系统",
        "tab_extraction": "特征提取",
        "tab_retrieval": "图像检索",
        "lang_en": "EN",
        "lang_zh": "中文",

        # ── Feature Extraction Tab ──
        "fe_title": "特征提取",
        "fe_desc": "选择图片文件夹，提取 ViT 特征并建立搜索索引。",
        "fe_dir_label": "图片目录",
        "fe_no_dir": "未选择目录",
        "fe_browse": "浏览...",
        "fe_index_name": "索引名称（可选）：",
        "fe_index_placeholder": "例如：动物、汽车、风景",
        "fe_extract_btn": "开始提取特征",
        "fe_warning_no_dir": "请先选择一个图片目录。",
        "fe_success_title": "提取完成",
        "fe_success_msg": "特征提取完成！\n\n索引：{index}\n元数据：{meta}",
        "fe_error_title": "提取失败",
        "fe_error_msg": "特征提取失败：\n{error}",
        "fe_done": "完成！索引：{index}  |  元数据：{meta}",

        # ── Retrieval Tab ──
        "rt_index_section": "搜索索引",
        "rt_no_index": "未加载索引",
        "rt_no_index_guide": "未找到索引文件 — 请到「特征提取」标签页创建",
        "rt_no_index_tip": "切换到「特征提取」标签页，选择图片文件夹，点击「开始提取特征」来创建索引。",
        "rt_latest_btn": "最新",
        "rt_latest_tip": "自动检测当前文件夹中最新的 .faiss 索引文件",
        "rt_load_btn": "加载...",
        "rt_load_tip": "手动选择 .faiss 索引文件",
        "rt_query_section": "查询图片",
        "rt_drop_hint": "拖拽图片到此处\n或点击「浏览」选择",
        "rt_selected": "已选择：{name}",
        "rt_no_query": "未选择图片",
        "rt_query_browse": "浏览...",
        "rt_query_tip": "从文件系统中选择一张查询图片",
        "rt_topk": "Top-K 结果数：",
        "rt_search_btn": "搜索",
        "rt_search_tip": "需要：（1）已加载索引，（2）已选择查询图片",
        "rt_shortcuts": "快捷键：Ctrl+O = 打开图片  |  Ctrl+Enter = 搜索  |  Ctrl+L = 加载索引",
        "rt_no_search_yet": "尚未执行搜索。\n请加载索引并选择查询图片，然后点击「搜索」。",
        "rt_no_results": "未返回任何结果。",
        "rt_warning_no_query": "请先选择一张查询图片。",
        "rt_warning_no_index": "请先加载索引。",
        "rt_searching": "搜索中...",
        "rt_similarity": "相似度",
        "rt_distance": "距离",
        "rt_file": "文件名",
        "rt_load_error": "加载索引失败：\n{error}",
        "rt_search_error": "搜索失败：\n{error}",
        "rt_index_loaded": "{name}  （{count} 张图片）",
        "rt_load_error_title": "错误",

        # ── General ──
        "error": "错误",
        "warning": "警告",
        "success": "成功",
    },
}


def t(key: str, lang: str = "en", **kwargs) -> str:
    """Get translated text by key and language.

    Args:
        key: Dictionary key in STR.
        lang: Language code ("en" or "zh").
        **kwargs: Optional format arguments (e.g. name=..., count=...).

    Returns:
        Translated string with format arguments applied.
    """
    text = STR.get(lang, STR["en"]).get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text


def toggle_lang(current: str) -> str:
    """Toggle between 'en' and 'zh'."""
    return "zh" if current == "en" else "en"
