import unittest

from games.fusion.tangram_fusion.services.board_service import TangramFusionBoardService


class TangramFusionBoardServiceTests(unittest.TestCase):
    def test_templates_have_no_overlapping_slots(self):
        service = TangramFusionBoardService()
        for template in service.TEMPLATES:
            slots = template["slots"]
            for index in range(len(slots)):
                for other_index in range(index + 1, len(slots)):
                    self.assertFalse(
                        service._polygons_overlap(slots[index]["polygon"], slots[other_index]["polygon"]),
                        f"{template['id']} slots {index} and {other_index} overlap",
                    )

    def test_templates_keep_expected_piece_set(self):
        expected = list(TangramFusionBoardService.PIECE_ORDER)
        service = TangramFusionBoardService()
        for template in service.TEMPLATES:
            self.assertEqual([slot["piece_type"] for slot in template["slots"]], expected)

    def test_round_assigns_balanced_red_blue_sides(self):
        service = TangramFusionBoardService()
        round_data = service.create_round(1)
        self.assertEqual(len(round_data["slot_sides"]), 7)
        self.assertGreaterEqual(round_data["slot_sides"].count("left"), 3)
        self.assertGreaterEqual(round_data["slot_sides"].count("right"), 3)

    def test_round_options_keep_correct_polygon_and_three_candidates(self):
        service = TangramFusionBoardService()
        round_data = service.create_round(2)
        missing = round_data["template"]["slots"][round_data["missing_index"]]
        self.assertEqual(len(round_data["options"]), 3)
        self.assertEqual(round_data["options"][round_data["correct_option"]]["polygon"], missing["polygon"])
