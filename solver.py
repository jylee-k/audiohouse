from pulp import LpMaximize, LpProblem, LpVariable, lpSum


def optimize_invoices(items):
    """
    items = [
        {
            'id': 1, 'name': 'Sofa', 'price': 2600, 'quantity': 2,
            'cashback_eligible': True,  # counts toward cashback generation
            'discount_eligible': True,  # counts toward $2,500 discount threshold
        }, ...
    ]

    Decision: x[i] = number of units of item i assigned to Invoice 1 (0 <= x[i] <= quantity[i])
    The remaining (quantity[i] - x[i]) units go into Invoice 2.

    Discounts:    $300 off per $2,500 block — ONLY discount_eligible item spend counts
                  toward the threshold. Non-discount-eligible items still appear on the
                  invoice and are paid in full; they simply don't unlock discount blocks.
    Cashback:     Earned from Invoice 1 cashback_eligible spend: $154 per $200 block, floored to $20
    Cashback cap: 20% of Invoice 2 gross total AFTER its discount, floored to $20
                  (gross total includes ALL items, discount-eligible or not)
    Objective:    Maximise total savings (discounts + cashback redeemed)
    """

    prob = LpProblem("Invoice_Optimization", LpMaximize)

    # --- Decision Variables ---
    # x[i]: integer units of item i that go into Invoice 1
    x = [
        LpVariable(f"x_{i}", cat="Integer", lowBound=0, upBound=items[i]["quantity"])
        for i in range(len(items))
    ]

    # --- Floor-division helper variables ---
    d1 = LpVariable("d1", cat="Integer", lowBound=0)   # $2,500 blocks in Invoice 1
    d2 = LpVariable("d2", cat="Integer", lowBound=0)   # $2,500 blocks in Invoice 2
    b1 = LpVariable("b1", cat="Integer", lowBound=0)   # $200 cashback-eligible blocks in Invoice 1

    # --- Invoice Gross Totals (ALL items — used for payment & cashback cap) ---
    t1 = lpSum([items[i]["price"] * x[i] for i in range(len(items))])
    t2 = lpSum([items[i]["price"] * (items[i]["quantity"] - x[i]) for i in range(len(items))])

    # --- Discount-qualifying subtotals (only discount_eligible items) ---
    t1_disc = lpSum(
        [items[i]["price"] * x[i] for i in range(len(items)) if items[i]["discount_eligible"]]
    )
    t2_disc = lpSum(
        [items[i]["price"] * (items[i]["quantity"] - x[i])
         for i in range(len(items)) if items[i]["discount_eligible"]]
    )

    # --- Discount Constraints (floor: d <= t_disc / 2500) ---
    prob += d1 <= t1_disc / 2500
    prob += d2 <= t2_disc / 2500

    # --- Cashback Earned (only Invoice 1 cashback_eligible items) ---
    t1_cashback_eligible = lpSum(
        [items[i]["price"] * x[i] for i in range(len(items)) if items[i]["cashback_eligible"]]
    )
    prob += b1 <= t1_cashback_eligible / 200  # $200 blocks
    raw_cashback = b1 * 154                  # $154 per block

    c_earned = LpVariable("c_earned", cat="Integer", lowBound=0)
    prob += c_earned <= raw_cashback / 20    # floor to $20 blocks
    actual_c_earned = c_earned * 20

    # --- Cashback Cap: 20% of Invoice 2 AFTER its $300/block discount, floored to $20 ---
    t2_after_discount = t2 - d2 * 300
    c_max = LpVariable("c_max", cat="Integer", lowBound=0)
    prob += c_max <= (t2_after_discount * 0.20) / 20   # floor to $20 blocks
    actual_c_max = c_max * 20

    # --- Cashback Redeemed: min(earned, cap) ---
    c_redeemed = LpVariable("c_redeemed", cat="Integer", lowBound=0)
    prob += c_redeemed <= actual_c_earned
    prob += c_redeemed <= actual_c_max

    # --- Objective: Maximise savings ---
    prob += (d1 * 300) + (d2 * 300) + c_redeemed

    prob.solve()

    # --- Extract Results ---
    def _int(v):
        return int(round(v.varValue or 0))

    d1_val = _int(d1)
    d2_val = _int(d2)
    c_earned_val = _int(c_earned) * 20
    c_max_val = _int(c_max) * 20
    c_redeemed_val = _int(c_redeemed)

    invoice_1_items = []
    invoice_2_items = []

    for i, item in enumerate(items):
        qty1 = _int(x[i])
        qty2 = item["quantity"] - qty1
        if qty1 > 0:
            invoice_1_items.append({**item, "quantity": qty1})
        if qty2 > 0:
            invoice_2_items.append({**item, "quantity": qty2})

    inv1_subtotal = sum(it["price"] * it["quantity"] for it in invoice_1_items)
    inv2_subtotal = sum(it["price"] * it["quantity"] for it in invoice_2_items)
    inv1_discount = d1_val * 300
    inv2_discount = d2_val * 300
    inv1_pay = inv1_subtotal - inv1_discount
    inv2_pay = inv2_subtotal - inv2_discount - c_redeemed_val
    total_pay = inv1_pay + inv2_pay
    total_saved = inv1_discount + inv2_discount + c_redeemed_val

    return {
        "invoice_1": invoice_1_items,
        "invoice_2": invoice_2_items,
        "totals": {
            "invoice_1_subtotal": inv1_subtotal,
            "invoice_1_discount": inv1_discount,
            "invoice_1_pay": inv1_pay,
            "invoice_2_subtotal": inv2_subtotal,
            "invoice_2_discount": inv2_discount,
            "invoice_2_after_discount": inv2_subtotal - inv2_discount,
            "cashback_earned": c_earned_val,
            "cashback_cap": c_max_val,
            "cashback_redeemed": c_redeemed_val,
            "invoice_2_pay": inv2_pay,
            "total_pay": total_pay,
            "total_saved": total_saved,
        },
    }