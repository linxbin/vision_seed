class LanguageManager:
    """多语言管理器 - 管理当前语言并提供文案翻译。"""

    DEFAULT_LANGUAGE = "en-US"
    SUPPORTED_LANGUAGES = ("en-US", "zh-CN")

    TRANSLATIONS = {
        "en-US": {
            "menu.title": "VisionSeed",
            "menu.start_training": "Start Training",
            "menu.configuration": "Configuration",
            "menu.view_history": "View History",
            "menu.exit": "Exit",
            "config.title": "Game Configuration",
            "config.info": "Click cards to select difficulty  Enter/ESC: Start/Return",
            "config.difficulty_level": "Difficulty Level",
            "config.font_preview": "Font Size Preview",
            "config.question_count": "Question Count",
            "config.range": "Range: {min_questions}-{max_questions}",
            "config.status": "Current: Level {level} ({size}px), Questions: {questions}",
            "config.sound_on": "Sound: ON (M)",
            "config.sound_off": "Sound: OFF (M)",
            "config.language": "Language: {language} (L)",
            "config.start_game": "Start Game",
            "config.back": "Back",
            "config.lang_en": "English",
            "config.lang_zh": "Chinese",
            "report.title": "Training Report",
            "report.total_questions": "Total Questions: {total}",
            "report.correct": "Correct: {correct}",
            "report.wrong": "Wrong: {wrong}",
            "report.time_used": "Time Used: {duration} s",
            "report.return_hint": "Press any key to return",
            "history.title": "Training History",
            "history.info_with_records": "Left/Right: Navigate  R: Refresh  ESC/Back: Return",
            "history.info_empty": "No records. Press R to refresh, ESC/Back to return.",
            "history.header.datetime": "Date & Time",
            "history.header.level": "Level",
            "history.header.questions": "Questions",
            "history.header.correct": "Correct",
            "history.header.accuracy": "Accuracy",
            "history.header.duration": "Duration",
            "history.invalid_date": "Invalid Date",
            "history.page_info": "Page {current} of {total}",
            "history.back": "Back",
        },
        "zh-CN": {
            "menu.title": "VisionSeed",
            "menu.start_training": "开始训练",
            "menu.configuration": "参数配置",
            "menu.view_history": "训练历史",
            "menu.exit": "退出",
            "config.title": "训练配置",
            "config.info": "点击卡片选择难度  回车/ESC: 开始/返回",
            "config.difficulty_level": "难度等级",
            "config.font_preview": "字号预览",
            "config.question_count": "题目数量",
            "config.range": "范围: {min_questions}-{max_questions}",
            "config.status": "当前: 等级 {level} ({size}px), 题数: {questions}",
            "config.sound_on": "音效: 开 (M)",
            "config.sound_off": "音效: 关 (M)",
            "config.language": "语言: {language} (L)",
            "config.start_game": "开始训练",
            "config.back": "返回",
            "config.lang_en": "英文",
            "config.lang_zh": "中文",
            "report.title": "训练报告",
            "report.total_questions": "总题数: {total}",
            "report.correct": "正确: {correct}",
            "report.wrong": "错误: {wrong}",
            "report.time_used": "用时: {duration} 秒",
            "report.return_hint": "按任意键返回",
            "history.title": "训练历史",
            "history.info_with_records": "左右键: 翻页  R: 刷新  ESC/返回: 回菜单",
            "history.info_empty": "暂无记录。按 R 刷新，ESC/返回 回菜单。",
            "history.header.datetime": "日期时间",
            "history.header.level": "等级",
            "history.header.questions": "题数",
            "history.header.correct": "正确",
            "history.header.accuracy": "正确率",
            "history.header.duration": "用时",
            "history.invalid_date": "无效日期",
            "history.page_info": "第 {current}/{total} 页",
            "history.back": "返回",
        },
    }

    def __init__(self, language=DEFAULT_LANGUAGE):
        self.current_language = self.DEFAULT_LANGUAGE
        self.set_language(language)

    def set_language(self, language):
        if language in self.SUPPORTED_LANGUAGES:
            self.current_language = language
        else:
            self.current_language = self.DEFAULT_LANGUAGE
        return self.current_language

    def cycle_language(self):
        if self.current_language == "en-US":
            self.current_language = "zh-CN"
        else:
            self.current_language = "en-US"
        return self.current_language

    def get_language(self):
        return self.current_language

    def t(self, key, **kwargs):
        language_map = self.TRANSLATIONS.get(self.current_language, {})
        fallback_map = self.TRANSLATIONS[self.DEFAULT_LANGUAGE]
        template = language_map.get(key, fallback_map.get(key, key))
        if kwargs:
            try:
                return template.format(**kwargs)
            except (KeyError, ValueError):
                return template
        return template
