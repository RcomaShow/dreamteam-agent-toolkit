import unittest
from datetime import date
from decimal import Decimal

from dreamteam.pricing import ExecutionLane, PriceBook, TokenUsage, estimate_cost


class PricingTests(unittest.TestCase):
    def test_snapshot_is_required(self):
        with self.assertRaises(TypeError):
            PriceBook(None)  # type: ignore[arg-type]

    def test_sonnet_intro_and_standard(self):
        self.assertEqual(PriceBook(date(2026, 8, 31)).get("claude-sonnet-5").input_per_mtok, Decimal("2"))
        self.assertEqual(PriceBook(date(2026, 9, 1)).get("claude-sonnet-5").input_per_mtok, Decimal("3"))

    def test_cache_and_batch_are_accounted(self):
        usage = TokenUsage(input_tokens=1_000_000, output_tokens=1_000_000, cache_read_tokens=1_000_000)
        book = PriceBook(date(2026, 7, 17))
        normal = estimate_cost("claude-haiku-4-5", usage, price_book=book)
        batch = estimate_cost("claude-haiku-4-5", usage, price_book=book, lane=ExecutionLane.BATCH)
        self.assertEqual(normal.total_usd, Decimal("6.10"))
        self.assertEqual(batch.total_usd, Decimal("3.050"))
        self.assertEqual(normal.pricing_catalog_id, "anthropic-api-2026-07-17")

    def test_invalid_usage_rejected(self):
        with self.assertRaises(ValueError):
            TokenUsage(input_tokens=-1)
        with self.assertRaises(TypeError):
            TokenUsage(input_tokens=True)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
