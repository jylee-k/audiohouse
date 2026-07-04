import unittest

from solver import optimize_invoices


class OptimizeInvoicesTest(unittest.TestCase):
    def test_additional_cashback_increases_redemption_with_same_cap(self):
        items = [
            {
                "id": 1,
                "name": "Eligible item",
                "price": 200,
                "quantity": 1,
                "cashback_eligible": True,
                "discount_eligible": False,
            },
            {
                "id": 2,
                "name": "Cap item",
                "price": 1000,
                "quantity": 1,
                "cashback_eligible": False,
                "discount_eligible": False,
            },
        ]

        without_additional = optimize_invoices(items)
        with_additional = optimize_invoices(items, additional_cashback=100)

        self.assertEqual(without_additional["totals"]["cashback_earned"], 140)
        self.assertEqual(without_additional["totals"]["cashback_redeemed"], 140)
        self.assertEqual(with_additional["totals"]["additional_cashback"], 100)
        self.assertEqual(with_additional["totals"]["cashback_available"], 240)
        self.assertEqual(with_additional["totals"]["cashback_cap"], 200)
        self.assertEqual(with_additional["totals"]["cashback_redeemed"], 200)

    def test_additional_cashback_is_floored_to_twenty_dollar_blocks(self):
        items = [
            {
                "id": 1,
                "name": "Redemption item",
                "price": 1000,
                "quantity": 1,
                "cashback_eligible": False,
                "discount_eligible": False,
            }
        ]

        result = optimize_invoices(items, additional_cashback=55)

        self.assertEqual(result["totals"]["additional_cashback"], 40)
        self.assertEqual(result["totals"]["cashback_redeemed"], 40)


if __name__ == "__main__":
    unittest.main()
