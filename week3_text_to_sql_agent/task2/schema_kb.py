"""
schema_kb.py
------------
Schema Knowledge Base for the ClassicModels PostgreSQL database.

This is the "brain" the rule-based decomposer (Task 2) and SQL generator
(Task 3/4) use to map plain-English words in a question to real table and
column names. Keeping this in one shared file means Task 2, Task 3 and
Task 4 all agree on the same vocabulary instead of repeating it.

All column names are double-quoted because the schema uses camelCase
identifiers (e.g. "customerName"), which Postgres folds to lowercase
unless quoted.
"""

# table_name -> list of plain-English phrases that refer to it
# (ordered longest-phrase-first is handled automatically in decomposer.py)
TABLE_SYNONYMS = {
    "orderdetails": ["order details", "order detail", "orderdetails", "order lines", "order line"],
    "productlines": ["product lines", "product line", "productlines", "productline"],
    "products": ["products", "product"],
    "customers": ["customers", "customer"],
    "employees": ["employees", "employee"],
    "offices": ["offices", "office"],
    "payments": ["payments", "payment"],
    "orders": ["orders", "order"],
}

# table_name -> { plain-English column phrase : real quoted column name }
TABLE_COLUMNS = {
    "products": {
        "name": '"productName"', "names": '"productName"',
        "code": '"productCode"', "codes": '"productCode"',
        "vendor": '"productVendor"',
        "scale": '"productScale"',
        "description": '"productDescription"',
        "stock": '"quantityInStock"', "quantity in stock": '"quantityInStock"',
        "buy price": '"buyPrice"', "price": '"buyPrice"',
        "msrp": '"MSRP"',
        "product line": '"productLine"',
    },
    "customers": {
        "name": '"customerName"', "names": '"customerName"',
        "city": "city", "state": "state", "country": "country",
        "phone": "phone", "phone numbers": "phone", "phone number": "phone",
        "contact first name": '"contactFirstName"',
        "contact last name": '"contactLastName"',
        "credit limit": '"creditLimit"',
        "postal code": '"postalCode"',
    },
    "orders": {
        "number": '"orderNumber"', "numbers": '"orderNumber"',
        "date": '"orderDate"', "dates": '"orderDate"',
        "status": "status", "statuses": "status",
        "required date": '"requiredDate"',
        "shipped date": '"shippedDate"',
        "comments": "comments",
    },
    "employees": {
        "first name": '"firstName"', "first names": '"firstName"',
        "last name": '"lastName"', "last names": '"lastName"',
        "job title": '"jobTitle"', "job titles": '"jobTitle"',
        "email": "email",
        "manager": '"reportsTo"', "managers": '"reportsTo"',
        "extension": "extension",
    },
    "offices": {
        "city": "city", "country": "country", "countries": "country",
        "state": "state", "phone": "phone",
        "postal code": '"postalCode"', "territory": "territory",
    },
    "productlines": {
        "description": '"textDescription"', "descriptions": '"textDescription"',
        "name": '"productLine"',
    },
    "payments": {
        "amount": "amount", "amounts": "amount",
        "date": '"paymentDate"',
        "check number": '"checkNumber"',
    },
    "orderdetails": {
        "quantity": '"quantityOrdered"', "quantities": '"quantityOrdered"',
        "price": '"priceEach"',
        "line number": '"orderLineNumber"',
    },
}

# Primary key column per table (used for JOIN building + COUNT(*) safety)
PRIMARY_KEYS = {
    "products": '"productCode"',
    "customers": '"customerNumber"',
    "orders": '"orderNumber"',
    "employees": '"employeeNumber"',
    "offices": '"officeCode"',
    "productlines": '"productLine"',
    "payments": '"customerNumber"',  # composite, but fine for join purposes
    "orderdetails": '"orderNumber"',
}

# Foreign-key relationships used to build JOIN ... ON ... clauses.
# Each entry: frozenset({table_a, table_b}) -> (col_on_table_a, col_on_table_b)
# Aliases are assigned dynamically by sql_generator.py, so no alias names
# are hardcoded here -- only the real column names that must be equal.
JOIN_CONDITIONS = {
    frozenset({"orders", "customers"}): ("orders", '"customerNumber"', "customers", '"customerNumber"'),
    frozenset({"payments", "customers"}): ("payments", '"customerNumber"', "customers", '"customerNumber"'),
    frozenset({"orderdetails", "orders"}): ("orderdetails", '"orderNumber"', "orders", '"orderNumber"'),
    frozenset({"orderdetails", "products"}): ("orderdetails", '"productCode"', "products", '"productCode"'),
    frozenset({"products", "productlines"}): ("products", '"productLine"', "productlines", '"productLine"'),
    frozenset({"employees", "offices"}): ("employees", '"officeCode"', "offices", '"officeCode"'),
    frozenset({"customers", "employees"}): ("customers", '"salesRepEmployeeNumber"', "employees", '"employeeNumber"'),
}

# Short alias used for each table when writing JOIN SQL
TABLE_ALIAS = {
    "products": "p", "customers": "c", "orders": "o", "employees": "e",
    "offices": "of", "productlines": "pl", "payments": "pm", "orderdetails": "od",
}
