# audiohouse

Invoice split optimizer for Audio House purchases. The app splits item quantities
across two invoices to maximize total savings from volume discounts and cashback
redemption.

## What The Solver Does

The solver uses a mixed-integer linear program in `solver.py`.

- Every item has a unit price, quantity, cashback eligibility flag, and discount
  eligibility flag.
- Each unit is assigned to exactly one of two invoices.
- Units of the same item may be split across invoices.
- Invoice 1 is used to earn cashback from cashback-eligible spend.
- Invoice 2 is used to redeem cashback, limited by the cashback redemption cap.

## Savings Rules

Volume discounts apply independently to both invoices:

- Only discount-eligible item spend counts toward the threshold.
- Each complete `$2,500` block earns a `$300` discount.
- Non-discount-eligible items are still paid in full and still contribute to the
  invoice gross total used for the cashback cap.

Cashback generation applies to invoice 1:

- Only cashback-eligible spend on invoice 1 generates cashback.
- Each complete `$200` block earns `$154` cashback.
- Earned cashback is rounded down to the nearest `$20` block.

Cashback redemption applies to invoice 2:

- The user may enter optional additional cashback already available.
- Additional cashback is a single request-level field, not an item-level field.
- Additional cashback is rounded down to the nearest `$20` block before use.
- Redeemable cashback is limited to the lesser of available cashback and the
  invoice 2 cap.
- The invoice 2 cap is `20%` of invoice 2 after its volume discount, rounded
  down to the nearest `$20` block.

The objective is:

```text
maximize invoice_1_discount + invoice_2_discount + cashback_redeemed
```

## API

`POST /api/optimize`

```json
{
  "additional_cashback": 120,
  "items": [
    {
      "id": 1,
      "name": "Sofa",
      "price": 2600,
      "quantity": 2,
      "cashback_eligible": true,
      "discount_eligible": true
    }
  ]
}
```

`additional_cashback` is optional and defaults to `0`.

The response includes invoice assignments and totals:

```json
{
  "invoice_1": [],
  "invoice_2": [],
  "totals": {
    "cashback_earned": 0,
    "additional_cashback": 120,
    "cashback_available": 120,
    "cashback_cap": 0,
    "cashback_redeemed": 0,
    "total_pay": 0,
    "total_saved": 0
  }
}
```

## Local Development

Install dependencies, then run the FastAPI app:

```bash
uvicorn main:app --reload --port 6969
```

The static UI is in `index.html` and posts to `/api/optimize`.

## Tests

Run the solver tests with:

```bash
python -m unittest discover -s tests
```
