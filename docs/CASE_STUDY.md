# Kitchen Numbers: sales, recipe cost and waste

## The question

If I had to choose one area to investigate before the next menu review, where would I start? I used a fictional Mediterranean restaurant to practise answering that question with SQL. This is a portfolio exercise, not an analysis of an employer's records.

## Dataset and method

The database covers 1 July–28 September 2026. It connects orders to menu dishes, dishes to raw ingredient quantities, and ingredients to a separate waste log. Cancelled orders are excluded. Discounts are deducted before calculating revenue. Recipe quantities are multiplied by fixed ingredient prices.

I kept the analysis mostly to joins, COUNT, SUM, AVG, GROUP BY and HAVING. CTEs make order-level averages and date-level joins easier to check. The final running-total query is an optional window-function exercise.

## Results

| Measure | Result |
|---|---:|
| Completed orders | 5,469 |
| Portions sold | 14,497 |
| Net food sales | AED 700,409.00 |
| Average food order | AED 128.07 |
| Theoretical recipe cost | AED 151,387.92 |
| Theoretical recipe cost / sales | 21.61% |
| Recorded waste cost | AED 6,241.95 |
| Waste / sales | 0.89% |

### 1. Start the menu review with the fish sandwich

The crispy fish sandwich sold 724 portions, with a 43.48% theoretical food cost after discounts. That is above this project's 32% review threshold. Its ingredient contribution was AED 27.46 per portion.

Grilled sea bass also crossed the threshold (34.77%), but contributed AED 63.46 per portion. A food-cost percentage alone would hide that difference. I would check portion weights, supplier price and the selling price before deciding what to change. The data does not justify automatically removing either dish.

Evidence: `03_menu.csv` and `08_cost_alerts.csv`.

### 2. Seafood deserves attention in the waste log

Prawns and sea bass together account for AED 3,294.54, or 52.8% of recorded waste cost. Tomatoes have more wasted kilograms than either ingredient, but cost much less. Ranking waste only by weight would send attention to the wrong place if the goal is to reduce cost.

I would first inspect dated seafood waste entries, prep quantities and storage practices. This dataset cannot establish whether storage, forecasting or handling caused those losses.

Evidence: `06_waste_ingredients.csv`.

### 3. Use a small scenario, then measure a trial

Spoilage accounts for AED 2,896.68 and overproduction for AED 1,985.60. Those are useful reasons to investigate, rather than proof of a particular operational fault.

A hypothetical 20% reduction in recorded seafood waste is worth AED 658.91 over a comparable 90-day period, holding prices and volume constant. That is a scenario, not achieved savings. A practical next step would be a two-week seafood prep log comparing portions prepared, sold and discarded.

Evidence: `07_waste_reasons.csv`; scenario = (prawn waste cost + sea bass waste cost) × 20%.

## Calculation choices that matter

- Average order value divides revenue by distinct completed orders. AVG of order-line revenue would answer a different question.
- Total food-cost percentage divides total recipe cost by total net sales. It is not the average of dish percentages.
- Query 10 aggregates sales and waste separately before joining them. Joining both raw tables on a date would duplicate amounts.
- Calendar coverage ends on 28 September. Monthly results should not be described as a full-quarter like-for-like trend.
- Ingredients are priced once for the entire period. There is no supplier-price history or actual inventory reconciliation.

## Limits and next step

The dataset is synthetic, with deliberately uneven menu demand and some seeded service patterns. Food cost excludes wages, energy, rent, packaging and fees. Contribution is not operating profit. The model does not infer actual COGS from purchases and opening/closing stock.

The next useful addition would be dated purchase prices and stock counts. I would add those only after understanding this version and being able to explain the joins and denominators.
