-- Q1: Customers whose high-value completed orders
-- total more than INR 8000.

SELECT
    customer_id,
    SUM(order_amount) AS total_spend
FROM orders
WHERE status = 'completed'
  AND order_amount > 500
GROUP BY customer_id
HAVING SUM(order_amount) > 8000
ORDER BY total_spend DESC;

-- Q2: Revenue by city and product category

SELECT
    c.city,
    p.category,
    ROUND(SUM(o.order_amount), 2) AS total_revenue
FROM orders o
JOIN customers c
    ON o.customer_id = c.customer_id
JOIN products p
    ON o.product_id = p.product_id
WHERE o.status = 'completed'
GROUP BY c.city, p.category
ORDER BY c.city, p.category;

-- Q3: Products priced above the average catalogue price.
SELECT
    product_id,
    product_name,
    category,
    price_inr
FROM products
WHERE price_inr > (
    SELECT AVG(price_inr)
    FROM products
)
ORDER BY price_inr DESC;

-- Q4: Customers with no completed orders.
SELECT
    c.customer_id,
    c.city
FROM customers c
LEFT JOIN orders o
    ON c.customer_id = o.customer_id
    AND o.status = 'completed'
WHERE o.order_id IS NULL
ORDER BY c.customer_id;

-- Q5: Customers whose completed-order spend is above average.
WITH customer_spend AS (
    SELECT
        customer_id,
        SUM(order_amount) AS total_spend
    FROM orders
    WHERE status = 'completed'
    GROUP BY customer_id
),
average_spend AS (
    SELECT AVG(total_spend) AS avg_spend
    FROM customer_spend
)
SELECT
    cs.customer_id,
    ROUND(cs.total_spend, 2) AS total_spend
FROM customer_spend cs
CROSS JOIN average_spend av
WHERE cs.total_spend > av.avg_spend
ORDER BY cs.total_spend DESC;

-- Q6: Rank customers by completed-order spend within each city.
WITH customer_city_spend AS (
    SELECT
        c.city,
        o.customer_id,
        SUM(o.order_amount) AS total_spend
    FROM orders o
    JOIN customers c
        ON o.customer_id = c.customer_id
    WHERE o.status = 'completed'
    GROUP BY c.city, o.customer_id
)
SELECT
    city,
    customer_id,
    ROUND(total_spend, 2) AS total_spend,
    RANK() OVER (
        PARTITION BY city ORDER BY total_spend DESC
    ) AS rank_position,
    DENSE_RANK() OVER (
        PARTITION BY city ORDER BY total_spend DESC
    ) AS dense_rank_position,
    ROW_NUMBER() OVER (
        PARTITION BY city ORDER BY total_spend DESC
    ) AS row_number_position
FROM customer_city_spend
ORDER BY city, rank_position, customer_id;

-- Q7: Daily completed revenue and cumulative running total.
WITH daily_revenue AS (
    SELECT
        DATE(order_ts) AS order_day,
        SUM(order_amount) AS daily_revenue
    FROM orders
    WHERE status = 'completed'
    GROUP BY DATE(order_ts)
)
SELECT
    order_day,
    ROUND(daily_revenue, 2) AS daily_revenue,
    ROUND(
        SUM(daily_revenue) OVER (
            ORDER BY order_day
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ),
        2
    ) AS running_total
FROM daily_revenue
ORDER BY order_day;

--Q8 test
WITH customer_city_spend AS (
    SELECT
        c.city,
        o.customer_id,
        SUM(o.order_amount) AS total_spend
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    WHERE o.status = 'completed'
    GROUP BY c.city, o.customer_id
),
ranked AS (
    SELECT
        RANK() OVER (
            PARTITION BY city ORDER BY total_spend DESC
        ) AS rank_position,
        ROW_NUMBER() OVER (
            PARTITION BY city ORDER BY total_spend DESC
        ) AS row_number_position
    FROM customer_city_spend
)
SELECT COUNT(*) AS differing_rows
FROM ranked
WHERE rank_position <> row_number_position;