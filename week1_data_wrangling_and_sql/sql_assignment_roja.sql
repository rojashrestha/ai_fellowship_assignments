-- ===================================
-- Name: Roja Shrestha
-- Date: May 1, 2026
-- SQL Assignment - ClassicModels
-- ===================================

-- 1. customers with credit limit over 20000
SELECT * FROM customers WHERE creditLimit > 20000;

-- 2. employees who report to VP Sales
SELECT * FROM employees WHERE reportsTo = (SELECT employeeNumber FROM employees WHERE jobTitle = 'VP Sales');

-- 3. customers in USA who filled state and credit limit between 100k and 200k
SELECT * FROM customers 
WHERE state IS NOT NULL 
AND country = 'USA' 
AND creditLimit BETWEEN 100000 AND 200000;

-- 4. employees who report to any Sales Manager
SELECT e.* 
FROM employees e
WHERE e.reportsTo IN (
    SELECT employeeNumber FROM employees 
    WHERE jobTitle LIKE '%Sales Manager%' OR jobTitle LIKE '%Sale Manager%'
);

-- 5. average credit limit for each country
SELECT country, AVG(creditLimit) as avg_credit_limit
FROM customers
GROUP BY country
ORDER BY avg_credit_limit DESC;

-- 6. total orders per day per customer, only show if more than 10 orders
SELECT orderDate, customerNumber, COUNT(*) AS total_orders
FROM orders
GROUP BY orderDate, customerNumber
HAVING COUNT(*) > 10
ORDER BY orderDate;

-- 7. supervisor name, job title, and how many people work under them (no join)
SELECT 
    (SELECT CONCAT(firstName, ' ', lastName) FROM employees e2 WHERE e2.employeeNumber = e1.reportsTo) AS supervisor_name,
    (SELECT jobTitle FROM employees e2 WHERE e2.employeeNumber = e1.reportsTo) AS supervisor_jobtitle,
    COUNT(*) AS num_supervisees
FROM employees e1
WHERE e1.reportsTo IS NOT NULL
GROUP BY e1.reportsTo;

-- 8. same as above but using join (easier for me)
SELECT 
    CONCAT(s.firstName, ' ', s.lastName) AS supervisor_name,
    s.jobTitle AS supervisor_jobtitle,
    COUNT(e.employeeNumber) AS num_supervisees
FROM employees e
JOIN employees s ON e.reportsTo = s.employeeNumber
GROUP BY e.reportsTo, s.firstName, s.lastName, s.jobTitle;

-- 9. customers with credit limit greater than average (using WITH)
WITH avg_credit AS (
    SELECT AVG(creditLimit) AS avg_limit FROM customers WHERE creditLimit IS NOT NULL
)
SELECT c.*
FROM customers c, avg_credit a
WHERE c.creditLimit > a.avg_limit;

-- 10. rank customers by credit limit, then find the third highest
SELECT customerNumber, customerName, creditLimit,
       RANK() OVER (ORDER BY creditLimit DESC) AS credit_rank
FROM customers
WHERE creditLimit IS NOT NULL;

-- get the third highest
SELECT customerNumber, customerName, creditLimit
FROM (
    SELECT customerNumber, customerName, creditLimit,
           DENSE_RANK() OVER (ORDER BY creditLimit DESC) AS rnk
    FROM customers
    WHERE creditLimit IS NOT NULL
) ranked
WHERE rnk = 3;

-- 11. total employees in each office
SELECT o.officeCode, o.city, COUNT(e.employeeNumber) AS employee_count
FROM offices o
LEFT JOIN employees e ON o.officeCode = e.officeCode
GROUP BY o.officeCode, o.city
ORDER BY employee_count DESC;

-- 12. number of customers assigned to each office (through sales rep)
SELECT o.officeCode, o.city, COUNT(DISTINCT c.customerNumber) AS customer_count
FROM offices o
JOIN employees e ON o.officeCode = e.officeCode
JOIN customers c ON c.salesRepEmployeeNumber = e.employeeNumber
GROUP BY o.officeCode, o.city
ORDER BY customer_count DESC;

-- 13. total payments received by each office
SELECT 
    o.officeCode,
    o.city,
    o.state,
    o.country,
    SUM(p.amount) AS total_payments
FROM offices o
JOIN employees e ON o.officeCode = e.officeCode
JOIN customers c ON c.salesRepEmployeeNumber = e.employeeNumber
JOIN payments p ON p.customerNumber = c.customerNumber
GROUP BY o.officeCode, o.city, o.state, o.country
ORDER BY total_payments DESC;

-- 14. total sales amount by each office (from order details)
SELECT 
    o.officeCode,
    o.city,
    SUM(od.quantityOrdered * od.priceEach) AS total_sales
FROM offices o
JOIN employees e ON o.officeCode = e.officeCode
JOIN customers c ON c.salesRepEmployeeNumber = e.employeeNumber
JOIN orders ord ON ord.customerNumber = c.customerNumber
JOIN orderdetails od ON od.orderNumber = ord.orderNumber
GROUP BY o.officeCode, o.city
ORDER BY total_sales DESC;

-- 15. pending payment amount for each office (orders - payments)
WITH office_sales AS (
    SELECT 
        o.officeCode,
        SUM(od.quantityOrdered * od.priceEach) AS total_order_amount
    FROM offices o
    JOIN employees e ON o.officeCode = e.officeCode
    JOIN customers c ON c.salesRepEmployeeNumber = e.employeeNumber
    JOIN orders ord ON ord.customerNumber = c.customerNumber
    JOIN orderdetails od ON od.orderNumber = ord.orderNumber
    GROUP BY o.officeCode
),
office_payments AS (
    SELECT 
        o.officeCode,
        SUM(p.amount) AS total_paid
    FROM offices o
    JOIN employees e ON o.officeCode = e.officeCode
    JOIN customers c ON c.salesRepEmployeeNumber = e.employeeNumber
    JOIN payments p ON p.customerNumber = c.customerNumber
    GROUP BY o.officeCode
)
SELECT 
    s.officeCode,
    s.total_order_amount,
    COALESCE(p.total_paid, 0) AS total_paid,
    (s.total_order_amount - COALESCE(p.total_paid, 0)) AS pending_amount
FROM office_sales s
LEFT JOIN office_payments p ON s.officeCode = p.officeCode;

-- 16. credit limit and proportion within each country
SELECT 
    customerName,
    country,
    creditLimit,
    creditLimit / SUM(creditLimit) OVER (PARTITION BY country) AS proportion_in_country
FROM customers
WHERE creditLimit IS NOT NULL
ORDER BY country, proportion_in_country DESC;

-- 17. create a view showing customer name, full address, total orders
CREATE VIEW customer_order_summary AS
SELECT 
    c.customerName,
    CONCAT_WS(', ', c.addressLine1, c.addressLine2, c.city, c.state, c.postalCode, c.country) AS full_address,
    COUNT(o.orderNumber) AS total_orders
FROM customers c
LEFT JOIN orders o ON c.customerNumber = o.customerNumber
GROUP BY c.customerNumber, c.customerName, c.addressLine1, c.addressLine2, 
         c.city, c.state, c.postalCode, c.country;

-- check the view
SELECT * FROM customer_order_summary;

-- 18. update a customer's country (I picked customer 124)
UPDATE customers 
SET country = 'USA' 
WHERE customerNumber = 124;

-- verify
SELECT customerNumber, customerName, country FROM customers WHERE customerNumber = 124;

-- 19. delete payments below 20000
DELETE FROM payments WHERE amount < 20000;

-- 20. add a new payment for customer 103
INSERT INTO payments (customerNumber, checkNumber, paymentDate, amount)
VALUES (103, 'CHK999001', CURDATE(), 15000.00);

-- check it worked
SELECT * FROM payments WHERE customerNumber = 103 ORDER BY paymentDate DESC;