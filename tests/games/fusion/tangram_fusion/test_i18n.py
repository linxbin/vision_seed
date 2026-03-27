import unittest

from core.language_manager import LanguageManager


class TangramFusionI18nTests(unittest.TestCase):
    def test_zh_cn_translations_are_readable(self):
        manager = LanguageManager("zh-CN")
        self.assertEqual(manager.t("tangram_fusion.title"), "融合七巧板")
        self.assertEqual(manager.t("tangram_fusion.template.hexagon"), "六角形")
        self.assertEqual(manager.t("tangram_fusion.play.tip"), "方向键选择  回车/空格确认  Esc 返回")


if __name__ == "__main__":
    unittest.main()
