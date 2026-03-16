import ast
import unittest
from pathlib import Path

from core.game_metrics import METRIC_LABEL_KEYS
from core.language_manager import LanguageManager


ROOT = Path(__file__).resolve().parents[2]


class I18nCoverageTests(unittest.TestCase):
    def test_literal_translation_keys_exist_in_all_languages(self):
        translations = LanguageManager.TRANSLATIONS
        all_keys = set()
        for mapping in translations.values():
            all_keys.update(mapping.keys())

        used_keys = set()

        class Visitor(ast.NodeVisitor):
            def visit_Call(self, node):
                if isinstance(node.func, ast.Attribute) and node.func.attr == "t" and node.args:
                    arg = node.args[0]
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        used_keys.add(arg.value)
                self.generic_visit(node)

        for base in (ROOT / "core", ROOT / "scenes", ROOT / "games"):
            for path in base.rglob("*.py"):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                Visitor().visit(tree)

        undefined = sorted(
            key for key in used_keys if key not in all_keys and not key.startswith("license.err.")
        )
        self.assertEqual(undefined, [], f"Undefined translation keys: {undefined}")

        for language in LanguageManager.SUPPORTED_LANGUAGES:
            missing = sorted(key for key in used_keys if key in all_keys and key not in translations[language])
            self.assertEqual(missing, [], f"Missing {language} translations for: {missing}")

    def test_dynamic_translation_keys_exist_in_all_languages(self):
        translations = LanguageManager.TRANSLATIONS
        dynamic_keys = {
            "snake_focus.stage.warmup",
            "snake_focus.stage.steady",
            "snake_focus.stage.challenge",
            "snake_focus.goal.warmup",
            "snake_focus.goal.steady",
            "snake_focus.goal.challenge",
            "catch_fruit.reward",
            "catch_fruit.next_goal",
            "precision_aim.reward",
            "precision_aim.next_goal",
            *METRIC_LABEL_KEYS.values(),
        }

        for language in LanguageManager.SUPPORTED_LANGUAGES:
            missing = sorted(key for key in dynamic_keys if key and key not in translations[language])
            self.assertEqual(missing, [], f"Missing {language} dynamic translations for: {missing}")

    def test_all_saved_training_metrics_have_label_mapping(self):
        metric_keys = set()

        for path in (ROOT / "games").rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Dict):
                    for key_node, value_node in zip(node.keys, node.values):
                        if (
                            isinstance(key_node, ast.Constant)
                            and key_node.value == "training_metrics"
                            and isinstance(value_node, ast.Dict)
                        ):
                            for metric_key in value_node.keys:
                                if isinstance(metric_key, ast.Constant) and isinstance(metric_key.value, str):
                                    metric_keys.add(metric_key.value)

        missing = sorted(key for key in metric_keys if key not in METRIC_LABEL_KEYS)
        self.assertEqual(missing, [], f"Missing metric label mappings for: {missing}")


if __name__ == "__main__":
    unittest.main()
