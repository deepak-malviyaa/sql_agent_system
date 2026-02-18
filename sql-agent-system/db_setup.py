import sqlalchemy
from sqlalchemy import text
import random
from datetime import datetime, timedelta

# 👇 UPDATE THIS WITH YOUR PASSWORD
# Format: postgresql://username:password@localhost:5432/database_name
DB_CONNECTION = "postgresql://user1:password@localhost:5432/entegris_db"

def setup_data():
    try:
        engine = sqlalchemy.create_engine(DB_CONNECTION)
        with engine.connect() as conn:
            print("🛠️  Resetting Database...")
            
            # 1. Drop all tables (reverse order due to foreign keys)
            conn.execute(text("DROP TABLE IF EXISTS product_reviews CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS order_shipments CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS inventory_movements CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS employee_commissions CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS order_items CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS orders CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS product_variants CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS products CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS suppliers CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS customers CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS customer_segments CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS employees CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS departments CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS warehouses CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS sales_data CASCADE;"))
            
            # 2. Create ORIGINAL sales_data table (UNCHANGED - as requested)
            print("📝 Creating Table 'sales_data' (legacy)...")
            conn.execute(text("""    
                CREATE TABLE sales_data (
                    id SERIAL PRIMARY KEY,
                    transaction_date DATE,
                    product_category VARCHAR(50),
                    product_name VARCHAR(100),
                    units_sold INT,
                    unit_price DECIMAL(10, 2),
                    total_revenue DECIMAL(10, 2),
                    country VARCHAR(50),
                    payment_method VARCHAR(20)
                );
            """))
            
            # 3. Create COMPLEX interconnected tables
            print("📝 Creating Table 'customer_segments'...")
            conn.execute(text("""
                CREATE TABLE customer_segments (
                    segment_id SERIAL PRIMARY KEY,
                    segment_name VARCHAR(50) UNIQUE,
                    min_lifetime_value DECIMAL(10, 2),
                    discount_percentage DECIMAL(5, 2),
                    priority_support BOOLEAN
                );
            """))
            
            print("📝 Creating Table 'customers'...")
            conn.execute(text("""
                CREATE TABLE customers (
                    customer_id SERIAL PRIMARY KEY,
                    first_name VARCHAR(50),
                    last_name VARCHAR(50),
                    email VARCHAR(100) UNIQUE,
                    phone VARCHAR(20),
                    country VARCHAR(50),
                    city VARCHAR(50),
                    postal_code VARCHAR(20),
                    signup_date DATE,
                    segment_id INT REFERENCES customer_segments(segment_id),
                    lifetime_value DECIMAL(10, 2) DEFAULT 0,
                    total_orders INT DEFAULT 0,
                    avg_order_value DECIMAL(10, 2) DEFAULT 0,
                    last_order_date DATE,
                    is_active BOOLEAN DEFAULT TRUE,
                    referral_code VARCHAR(20) UNIQUE
                );
            """))
            
            print("📝 Creating Table 'warehouses'...")
            conn.execute(text("""
                CREATE TABLE warehouses (
                    warehouse_id SERIAL PRIMARY KEY,
                    warehouse_name VARCHAR(100),
                    location VARCHAR(100),
                    country VARCHAR(50),
                    capacity INT,
                    current_utilization DECIMAL(5, 2),
                    manager_name VARCHAR(100),
                    is_operational BOOLEAN DEFAULT TRUE
                );
            """))
            
            print("📝 Creating Table 'departments'...")
            conn.execute(text("""
                CREATE TABLE departments (
                    department_id SERIAL PRIMARY KEY,
                    department_name VARCHAR(50),
                    location VARCHAR(50),
                    annual_budget DECIMAL(12, 2),
                    headcount INT,
                    cost_center VARCHAR(20)
                );
            """))
            
            print("📝 Creating Table 'employees'...")
            conn.execute(text("""
                CREATE TABLE employees (
                    employee_id SERIAL PRIMARY KEY,
                    first_name VARCHAR(50),
                    last_name VARCHAR(50),
                    email VARCHAR(100) UNIQUE,
                    department_id INT REFERENCES departments(department_id),
                    position VARCHAR(50),
                    salary DECIMAL(10, 2),
                    commission_rate DECIMAL(5, 2) DEFAULT 0,
                    hire_date DATE,
                    performance_rating DECIMAL(3, 2),
                    manager_id INT REFERENCES employees(employee_id),
                    is_active BOOLEAN DEFAULT TRUE
                );
            """))
            
            print("📝 Creating Table 'suppliers'...")
            conn.execute(text("""
                CREATE TABLE suppliers (
                    supplier_id SERIAL PRIMARY KEY,
                    supplier_name VARCHAR(100),
                    contact_person VARCHAR(100),
                    email VARCHAR(100),
                    phone VARCHAR(20),
                    country VARCHAR(50),
                    lead_time_days INT,
                    quality_rating DECIMAL(3, 2),
                    payment_terms VARCHAR(50),
                    is_preferred BOOLEAN DEFAULT FALSE
                );
            """))
            
            print("📝 Creating Table 'products'...")
            conn.execute(text("""
                CREATE TABLE products (
                    product_id SERIAL PRIMARY KEY,
                    product_name VARCHAR(100),
                    category VARCHAR(50),
                    subcategory VARCHAR(50),
                    base_price DECIMAL(10, 2),
                    cost_price DECIMAL(10, 2),
                    supplier_id INT REFERENCES suppliers(supplier_id),
                    weight_kg DECIMAL(6, 2),
                    dimensions VARCHAR(50),
                    sku_prefix VARCHAR(20),
                    is_active BOOLEAN DEFAULT TRUE,
                    launch_date DATE,
                    discontinue_date DATE
                );
            """))
            
            print("📝 Creating Table 'product_variants'...")
            conn.execute(text("""
                CREATE TABLE product_variants (
                    variant_id SERIAL PRIMARY KEY,
                    product_id INT REFERENCES products(product_id),
                    variant_name VARCHAR(100),
                    sku VARCHAR(50) UNIQUE,
                    color VARCHAR(30),
                    size VARCHAR(20),
                    warehouse_id INT REFERENCES warehouses(warehouse_id),
                    stock_quantity INT,
                    reorder_level INT,
                    reorder_quantity INT,
                    price_adjustment DECIMAL(10, 2) DEFAULT 0,
                    is_available BOOLEAN DEFAULT TRUE
                );
            """))
            
            print("📝 Creating Table 'orders'...")
            conn.execute(text("""
                CREATE TABLE orders (
                    order_id SERIAL PRIMARY KEY,
                    customer_id INT REFERENCES customers(customer_id),
                    employee_id INT REFERENCES employees(employee_id),
                    order_date TIMESTAMP,
                    order_status VARCHAR(20),
                    total_amount DECIMAL(10, 2),
                    discount_amount DECIMAL(10, 2) DEFAULT 0,
                    tax_amount DECIMAL(10, 2) DEFAULT 0,
                    shipping_cost DECIMAL(10, 2) DEFAULT 0,
                    payment_method VARCHAR(20),
                    payment_status VARCHAR(20),
                    shipping_country VARCHAR(50),
                    shipping_city VARCHAR(50),
                    tracking_number VARCHAR(50),
                    estimated_delivery DATE,
                    actual_delivery DATE,
                    notes TEXT
                );
            """))
            
            print("📝 Creating Table 'order_items'...")
            conn.execute(text("""
                CREATE TABLE order_items (
                    order_item_id SERIAL PRIMARY KEY,
                    order_id INT REFERENCES orders(order_id),
                    variant_id INT REFERENCES product_variants(variant_id),
                    quantity INT,
                    unit_price DECIMAL(10, 2),
                    discount_applied DECIMAL(10, 2) DEFAULT 0,
                    line_total DECIMAL(10, 2),
                    fulfillment_status VARCHAR(20) DEFAULT 'pending'
                );
            """))
            
            print("📝 Creating Table 'employee_commissions'...")
            conn.execute(text("""
                CREATE TABLE employee_commissions (
                    commission_id SERIAL PRIMARY KEY,
                    employee_id INT REFERENCES employees(employee_id),
                    order_id INT REFERENCES orders(order_id),
                    commission_amount DECIMAL(10, 2),
                    commission_date DATE,
                    payment_status VARCHAR(20) DEFAULT 'pending',
                    payment_date DATE
                );
            """))
            
            print("📝 Creating Table 'inventory_movements'...")
            conn.execute(text("""
                CREATE TABLE inventory_movements (
                    movement_id SERIAL PRIMARY KEY,
                    variant_id INT REFERENCES product_variants(variant_id),
                    warehouse_id INT REFERENCES warehouses(warehouse_id),
                    movement_type VARCHAR(20),
                    quantity INT,
                    movement_date TIMESTAMP,
                    reference_number VARCHAR(50),
                    reason VARCHAR(100),
                    recorded_by INT REFERENCES employees(employee_id)
                );
            """))
            
            print("📝 Creating Table 'order_shipments'...")
            conn.execute(text("""
                CREATE TABLE order_shipments (
                    shipment_id SERIAL PRIMARY KEY,
                    order_id INT REFERENCES orders(order_id),
                    warehouse_id INT REFERENCES warehouses(warehouse_id),
                    carrier VARCHAR(50),
                    tracking_number VARCHAR(50),
                    shipment_date DATE,
                    estimated_delivery DATE,
                    actual_delivery DATE,
                    shipment_cost DECIMAL(10, 2),
                    weight_kg DECIMAL(8, 2),
                    status VARCHAR(20)
                );
            """))
            
            print("📝 Creating Table 'product_reviews'...")
            conn.execute(text("""
                CREATE TABLE product_reviews (
                    review_id SERIAL PRIMARY KEY,
                    product_id INT REFERENCES products(product_id),
                    customer_id INT REFERENCES customers(customer_id),
                    order_id INT REFERENCES orders(order_id),
                    rating INT CHECK (rating BETWEEN 1 AND 5),
                    review_title VARCHAR(200),
                    review_text TEXT,
                    review_date DATE,
                    is_verified_purchase BOOLEAN DEFAULT FALSE,
                    helpful_votes INT DEFAULT 0
                );
            """))
            
            # 3. Generate Mock Data - COMPLEX REALISTIC BUSINESS DATA
            print("🌱 Seeding legacy sales_data (50 rows)...")
            
            countries = ['USA', 'Germany', 'France', 'India', 'UK', 'Canada']
            products = {
                'Electronics': [('Laptop Pro', 1200), ('Smartphone X', 800), ('Monitor 4K', 400)],
                'Clothing': [('Denim Jacket', 80), ('Running Shoes', 120), ('Cotton T-Shirt', 25)],
                'Home': [('Coffee Maker', 150), ('Smart Bulb', 15), ('Office Chair', 250)]
            }
            methods = ['Credit Card', 'PayPal', 'Bank Transfer']
            
            values_list = []
            values_list.append("('2023-10-01', 'Electronics', 'Laptop Pro', 5, 1200.00, 6000.00, 'Germany', 'Credit Card')")
            values_list.append("('2023-10-05', 'Clothing', 'Running Shoes', 10, 120.00, 1200.00, 'Germany', 'PayPal')")
            values_list.append("('2023-11-12', 'Electronics', 'Smartphone X', 2, 800.00, 1600.00, 'USA', 'Credit Card')")

            for _ in range(50):
                cat = random.choice(list(products.keys()))
                prod, price = random.choice(products[cat])
                qty = random.randint(1, 10)
                total = price * qty
                country = random.choice(countries)
                method = random.choice(methods)
                date = (datetime.now() - timedelta(days=random.randint(1, 365))).strftime('%Y-%m-%d')
                values_list.append(f"('{date}', '{cat}', '{prod}', {qty}, {price}, {total}, '{country}', '{method}')")

            sql = f"""INSERT INTO sales_data 
                (transaction_date, product_category, product_name, units_sold, unit_price, total_revenue, country, payment_method)
                VALUES {", ".join(values_list)};"""
            conn.execute(text(sql))
            
            # === SEED CUSTOMER SEGMENTS ===
            print("🌱 Seeding customer_segments (5 tiers)...")
            conn.execute(text("""
                INSERT INTO customer_segments (segment_name, min_lifetime_value, discount_percentage, priority_support) VALUES
                ('Bronze', 0, 0, FALSE),
                ('Silver', 1000, 5, FALSE),
                ('Gold', 5000, 10, TRUE),
                ('Platinum', 10000, 15, TRUE),
                ('Diamond', 25000, 20, TRUE);
            """))
            
            # === SEED CUSTOMERS ===
            print("🌱 Seeding customers (50 customers)...")
            customer_data = [
                ("Emma", "Wilson", "emma.wilson@email.com", "+1-555-0101", "USA", "New York", "10001", "2024-01-15", 15234.50, 28, 544.09, "2025-12-20"),
                ("Liam", "Schmidt", "liam.schmidt@email.com", "+49-555-0102", "Germany", "Berlin", "10115", "2023-08-22", 8920.00, 15, 594.67, "2025-11-15"),
                ("Olivia", "Martinez", "olivia.martinez@email.com", "+34-555-0103", "Spain", "Madrid", "28001", "2024-03-10", 3450.75, 12, 287.56, "2025-10-05"),
                ("Noah", "Brown", "noah.brown@email.com", "+44-555-0104", "UK", "London", "SW1A", "2023-11-05", 21450.00, 42, 510.71, "2026-01-10"),
                ("Ava", "Johnson", "ava.johnson@email.com", "+1-555-0105", "USA", "Los Angeles", "90001", "2024-06-18", 2100.00, 8, 262.50, "2025-09-12"),
                ("Ethan", "Dubois", "ethan.dubois@email.com", "+33-555-0106", "France", "Paris", "75001", "2023-05-30", 12800.00, 25, 512.00, "2025-12-28"),
                ("Sophia", "Kumar", "sophia.kumar@email.com", "+91-555-0107", "India", "Mumbai", "400001", "2024-02-14", 5600.00, 18, 311.11, "2025-11-20"),
                ("Mason", "Anderson", "mason.anderson@email.com", "+1-555-0108", "Canada", "Toronto", "M5H", "2023-12-01", 18900.00, 35, 540.00, "2025-12-15"),
                ("Isabella", "Chen", "isabella.chen@email.com", "+86-555-0109", "China", "Shanghai", "200000", "2024-04-20", 9200.00, 20, 460.00, "2025-10-30"),
                ("Lucas", "Taylor", "lucas.taylor@email.com", "+61-555-0110", "Australia", "Sydney", "2000", "2023-09-15", 6700.00, 14, 478.57, "2025-08-22")
            ]
            
            for i, (fname, lname, email, phone, country, city, postal, signup, ltv, orders, avg, last_order) in enumerate(customer_data):
                segment = 1 if ltv < 1000 else (2 if ltv < 5000 else (3 if ltv < 10000 else (4 if ltv < 25000 else 5)))
                active = random.choice([True, True, True, False])  # 75% active
                ref_code = f"REF{1000+i}"
                conn.execute(text(f"""
                    INSERT INTO customers (first_name, last_name, email, phone, country, city, postal_code, signup_date, 
                                          segment_id, lifetime_value, total_orders, avg_order_value, last_order_date, 
                                          is_active, referral_code)
                    VALUES ('{fname}', '{lname}', '{email}', '{phone}', '{country}', '{city}', '{postal}', '{signup}', 
                            {segment}, {ltv}, {orders}, {avg}, '{last_order}', {active}, '{ref_code}');
                """))
            
            # Generate 40 more random customers
            names_f = ["James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda", "David", "Barbara"]
            names_l = ["Smith", "Jones", "Davis", "Miller", "Wilson", "Moore", "Taylor", "Anderson", "Thomas", "Jackson"]
            for i in range(40):
                fname = random.choice(names_f)
                lname = random.choice(names_l)
                email = f"{fname.lower()}.{lname.lower()}{i+11}@email.com"
                country = random.choice(countries)
                ltv = round(random.uniform(100, 30000), 2)
                orders = random.randint(1, 50)
                avg = round(ltv / orders, 2)
                signup = (datetime.now() - timedelta(days=random.randint(30, 700))).strftime('%Y-%m-%d')
                last_order = (datetime.now() - timedelta(days=random.randint(1, 90))).strftime('%Y-%m-%d')
                segment = 1 if ltv < 1000 else (2 if ltv < 5000 else (3 if ltv < 10000 else (4 if ltv < 25000 else 5)))
                active = random.choice([True, True, True, False])
                ref_code = f"REF{1010+i}"
                conn.execute(text(f"""
                    INSERT INTO customers (first_name, last_name, email, phone, country, city, postal_code, signup_date, 
                                          segment_id, lifetime_value, total_orders, avg_order_value, last_order_date, 
                                          is_active, referral_code)
                    VALUES ('{fname}', '{lname}', '{email}', '+1-555-{random.randint(1000,9999)}', '{country}', 
                            'City{i}', '{random.randint(10000,99999)}', '{signup}', {segment}, {ltv}, {orders}, {avg}, 
                            '{last_order}', {active}, '{ref_code}');
                """))
            
            # === SEED WAREHOUSES ===
            print("🌱 Seeding warehouses (6 locations)...")
            conn.execute(text("""
                INSERT INTO warehouses (warehouse_name, location, country, capacity, current_utilization, manager_name, is_operational) VALUES
                ('North America Hub', 'Newark, NJ', 'USA', 50000, 72.5, 'Sarah Mitchell', TRUE),
                ('Europe Central', 'Frankfurt', 'Germany', 35000, 85.2, 'Klaus Mueller', TRUE),
                ('UK Distribution', 'Manchester', 'UK', 25000, 68.9, 'James Patterson', TRUE),
                ('Asia Pacific', 'Singapore', 'Singapore', 40000, 91.3, 'Wei Zhang', TRUE),
                ('India Regional', 'Bangalore', 'India', 20000, 45.7, 'Raj Patel', TRUE),
                ('Australia Hub', 'Melbourne', 'Australia', 15000, 52.1, 'Emma Clarke', FALSE);
            """))
            
            # === SEED DEPARTMENTS ===
            print("🌱 Seeding departments (8 departments)...")
            conn.execute(text("""
                INSERT INTO departments (department_name, location, annual_budget, headcount, cost_center) VALUES
                ('Sales', 'New York', 2500000, 45, 'CC-1001'),
                ('Marketing', 'San Francisco', 1800000, 28, 'CC-1002'),
                ('Operations', 'Chicago', 3200000, 65, 'CC-1003'),
                ('Customer Service', 'Austin', 1200000, 52, 'CC-1004'),
                ('IT', 'Seattle', 2800000, 38, 'CC-1005'),
                ('Finance', 'New York', 1500000, 22, 'CC-1006'),
                ('HR', 'Los Angeles', 900000, 15, 'CC-1007'),
                ('Product', 'San Francisco', 3500000, 42, 'CC-1008');
            """))
            
            # === SEED EMPLOYEES ===
            print("🌱 Seeding employees (40 employees with hierarchy)...")
            # First insert managers (no manager_id)
            conn.execute(text("""
                INSERT INTO employees (first_name, last_name, email, department_id, position, salary, commission_rate, 
                                      hire_date, performance_rating, manager_id, is_active) VALUES
                ('Michael', 'Stevens', 'michael.stevens@company.com', 1, 'VP of Sales', 145000, 0, '2020-03-15', 4.8, NULL, TRUE),
                ('Rachel', 'Kim', 'rachel.kim@company.com', 2, 'Marketing Director', 135000, 0, '2019-07-20', 4.6, NULL, TRUE),
                ('David', 'Harper', 'david.harper@company.com', 3, 'Operations Manager', 125000, 0, '2018-11-10', 4.5, NULL, TRUE),
                ('Lisa', 'Thompson', 'lisa.thompson@company.com', 4, 'Customer Service Lead', 95000, 0, '2021-01-05', 4.4, NULL, TRUE),
                ('Tom', 'Wilson', 'tom.wilson@company.com', 5, 'CTO', 180000, 0, '2017-05-12', 4.9, NULL, TRUE);
            """))
            
            # Then insert regular employees with manager references
            sales_team = [
                ("Alex", "Morgan", 1, "Senior Sales Rep", 85000, 3.5, "2021-06-01", 4.3, 1),
                ("Jessica", "Lee", 1, "Sales Rep", 68000, 2.5, "2022-03-15", 4.1, 1),
                ("Chris", "Davis", 1, "Sales Rep", 72000, 2.8, "2021-11-20", 4.4, 1),
                ("Amanda", "Rodriguez", 1, "Inside Sales", 55000, 2.0, "2023-02-10", 3.9, 1),
            ]
            for fname, lname, dept, pos, sal, comm, hire, perf, mgr in sales_team:
                conn.execute(text(f"""
                    INSERT INTO employees (first_name, last_name, email, department_id, position, salary, commission_rate, 
                                          hire_date, performance_rating, manager_id, is_active)
                    VALUES ('{fname}', '{lname}', '{fname.lower()}.{lname.lower()}@company.com', {dept}, '{pos}', 
                            {sal}, {comm}, '{hire}', {perf}, {mgr}, TRUE);
                """))
            
            # Add more employees across departments (simplified)
            for i in range(30):
                dept = random.randint(1, 8)
                sal = random.randint(50000, 120000)
                comm = round(random.uniform(0, 4), 2) if dept == 1 else 0  # Only sales gets commission
                hire = (datetime.now() - timedelta(days=random.randint(365, 2000))).strftime('%Y-%m-%d')
                perf = round(random.uniform(3.0, 5.0), 1)
                mgr = random.randint(1, 5) if dept <= 5 else None
                mgr_value = f"{mgr}" if mgr is not None else "NULL"
                conn.execute(text(f"""
                    INSERT INTO employees (first_name, last_name, email, department_id, position, salary, commission_rate, 
                                          hire_date, performance_rating, manager_id, is_active)
                    VALUES ('Employee', 'Name{i}', 'emp{i}@company.com', {dept}, 'Specialist', {sal}, {comm}, 
                            '{hire}', {perf}, {mgr_value}, TRUE);
                """))
            
            # === SEED SUPPLIERS ===
            print("🌱 Seeding suppliers (15 suppliers)...")
            suppliers = [
                ("TechSource Global", "John Anderson", "john@techsource.com", "+1-555-2001", "USA", 14, 4.5, "Net 30", TRUE),
                ("Electronics Depot", "Maria Garcia", "maria@elecdepot.com", "+1-555-2002", "USA", 7, 4.8, "Net 15", TRUE),
                ("Fashion Wholesale Co", "Pierre Dubois", "pierre@fashionwholesale.fr", "+33-555-2003", "France", 21, 4.2, "Net 45", FALSE),
                ("HomeGoods Direct", "Sarah Chen", "sarah@homegoods.com", "+86-555-2004", "China", 35, 3.9, "Net 60", FALSE),
                ("Quality Apparel Ltd", "James Wilson", "james@qualityapparel.uk", "+44-555-2005", "UK", 18, 4.6, "Net 30", TRUE),
            ]
            for name, contact, email, phone, country, lead, rating, terms, preferred in suppliers:
                conn.execute(text(f"""
                    INSERT INTO suppliers (supplier_name, contact_person, email, phone, country, lead_time_days, 
                                          quality_rating, payment_terms, is_preferred)
                    VALUES ('{name}', '{contact}', '{email}', '{phone}', '{country}', {lead}, {rating}, '{terms}', {preferred});
                """))
            
            # Add 10 more random suppliers
            for i in range(10):
                conn.execute(text(f"""
                    INSERT INTO suppliers (supplier_name, contact_person, email, phone, country, lead_time_days, 
                                          quality_rating, payment_terms, is_preferred)
                    VALUES ('Supplier {i+6}', 'Contact {i+6}', 'contact{i+6}@supplier.com', '+1-555-{2010+i}', 
                            'USA', {random.randint(7, 45)}, {round(random.uniform(3.5, 5.0), 1)}, 'Net 30', FALSE);
                """))
            
            # === SEED PRODUCTS ===
            print("🌱 Seeding products (30 products)...")
            products_list = [
                ("UltraBook Pro 15", "Electronics", "Laptops", 1299.99, 850.00, 1, 1.8, "38x26x2cm", "UB", "2023-01-15", None),
                ("SmartPhone X12", "Electronics", "Phones", 899.99, 620.00, 1, 0.19, "15x7x1cm", "SPX", "2023-03-20", None),
                ("4K Monitor 27inch", "Electronics", "Monitors", 449.99, 280.00, 2, 5.2, "61x46x18cm", "MON", "2022-11-10", None),
                ("Wireless Earbuds Pro", "Electronics", "Audio", 179.99, 95.00, 2, 0.05, "6x5x3cm", "WEP", "2023-06-01", None),
                ("Premium Denim Jacket", "Clothing", "Outerwear", 89.99, 45.00, 3, 0.8, "Standard", "PDJ", "2023-02-14", None),
                ("Running Shoes Elite", "Clothing", "Footwear", 129.99, 65.00, 5, 0.4, "Standard", "RSE", "2023-04-20", None),
                ("Cotton T-Shirt Classic", "Clothing", "Tops", 24.99, 8.00, 3, 0.2, "Standard", "CTC", "2022-08-15", None),
                ("Smart Coffee Maker", "Home", "Kitchen", 159.99, 85.00, 4, 2.1, "30x20x35cm", "SCM", "2023-01-10", None),
                ("LED Smart Bulb 4-Pack", "Home", "Lighting", 39.99, 15.00, 4, 0.3, "6x6x11cm", "LSB", "2022-12-01", None),
                ("Ergonomic Office Chair", "Home", "Furniture", 299.99, 150.00, 4, 15.0, "70x70x120cm", "EOC", "2023-05-15", None),
            ]
            for name, cat, subcat, price, cost, supp, weight, dim, sku_pref, launch, disc in products_list:
                conn.execute(text(f"""
                    INSERT INTO products (product_name, category, subcategory, base_price, cost_price, supplier_id, 
                                         weight_kg, dimensions, sku_prefix, is_active, launch_date, discontinue_date)
                    VALUES ('{name}', '{cat}', '{subcat}', {price}, {cost}, {supp}, {weight}, '{dim}', '{sku_pref}', 
                            TRUE, '{launch}', NULL);
                """))
            
            # Add 20 more simple products
            for i in range(20):
                cat = random.choice(['Electronics', 'Clothing', 'Home'])
                conn.execute(text(f"""
                    INSERT INTO products (product_name, category, subcategory, base_price, cost_price, supplier_id, 
                                         weight_kg, dimensions, sku_prefix, is_active, launch_date, discontinue_date)
                    VALUES ('Product {i+11}', '{cat}', 'Subcategory', {round(random.uniform(20, 500), 2)}, 
                            {round(random.uniform(10, 250), 2)}, {random.randint(1, 15)}, {round(random.uniform(0.1, 10), 2)}, 
                            'Standard', 'PRD', TRUE, '2023-01-01', NULL);
                """))
            
            # === SEED PRODUCT VARIANTS ===
            print("🌱 Seeding product_variants (120 SKUs)...")
            # Generate variants for each product (colors/sizes)
            colors = ['Black', 'White', 'Silver', 'Blue', 'Red', 'Gray']
            sizes = ['S', 'M', 'L', 'XL', 'One Size']
            
            for prod_id in range(1, 31):  # 30 products
                for variant_num in range(1, 5):  # 4 variants each
                    color = random.choice(colors)
                    size = random.choice(sizes) if prod_id % 3 == 0 else 'One Size'
                    warehouse = random.randint(1, 6)
                    stock = random.randint(0, 500)
                    reorder = random.randint(20, 100)
                    price_adj = round(random.uniform(-20, 50), 2)
                    available = stock > 0
                    sku_num = (prod_id * 10) + variant_num
                    
                    conn.execute(text(f"""
                        INSERT INTO product_variants (product_id, variant_name, sku, color, size, warehouse_id, 
                                                     stock_quantity, reorder_level, reorder_quantity, price_adjustment, is_available)
                        VALUES ({prod_id}, 'Variant {variant_num}', 'SKU-{sku_num:05d}', '{color}', '{size}', 
                                {warehouse}, {stock}, {reorder}, {reorder*2}, {price_adj}, {available});
                    """))
            
            # === SEED ORDERS ===
            print("🌱 Seeding orders (100 orders)...")
            order_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
            payment_statuses = ['pending', 'completed', 'failed', 'refunded']
            
            for i in range(100):
                customer_id = random.randint(1, 50)
                employee_id = random.randint(6, 9)  # Sales team
                order_date = (datetime.now() - timedelta(days=random.randint(1, 365))).strftime('%Y-%m-%d %H:%M:%S')
                status = random.choice(order_statuses)
                subtotal = round(random.uniform(50, 2000), 2)
                discount = round(subtotal * random.uniform(0, 0.15), 2)
                tax = round((subtotal - discount) * 0.08, 2)
                shipping = round(random.uniform(5, 25), 2)
                total = round(subtotal - discount + tax + shipping, 2)
                payment_method = random.choice(['Credit Card', 'PayPal', 'Bank Transfer', 'Debit Card'])
                payment_status = 'completed' if status in ['shipped', 'delivered'] else random.choice(payment_statuses)
                country = random.choice(countries)
                tracking = f"TRK{random.randint(100000, 999999)}" if status in ['shipped', 'delivered'] else None
                tracking_value = f"'{tracking}'" if tracking is not None else "NULL"
                actual_delivery = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d') if status == 'delivered' else None
                actual_delivery_value = f"'{actual_delivery}'" if actual_delivery is not None else "NULL"
                
                conn.execute(text(f"""
                    INSERT INTO orders (customer_id, employee_id, order_date, order_status, total_amount, discount_amount, 
                                       tax_amount, shipping_cost, payment_method, payment_status, shipping_country, 
                                       shipping_city, tracking_number, estimated_delivery, actual_delivery, notes)
                    VALUES ({customer_id}, {employee_id}, '{order_date}', '{status}', {total}, {discount}, {tax}, 
                            {shipping}, '{payment_method}', '{payment_status}', '{country}', 'City{i}', 
                            {tracking_value}, 
                            '{ (datetime.now() + timedelta(days=random.randint(3, 14))).strftime('%Y-%m-%d') }', 
                            {actual_delivery_value}, 
                            'Order note {i}');
                """))
            
            # === SEED ORDER ITEMS ===
            print("🌱 Seeding order_items (250 line items)...")
            for order_id in range(1, 101):
                items_count = random.randint(1, 5)  # 1-5 items per order
                for _ in range(items_count):
                    variant_id = random.randint(1, 120)
                    qty = random.randint(1, 5)
                    unit_price = round(random.uniform(20, 500), 2)
                    discount = round(unit_price * qty * random.uniform(0, 0.1), 2)
                    line_total = round((unit_price * qty) - discount, 2)
                    fulfillment = random.choice(['pending', 'processing', 'shipped', 'delivered'])
                    
                    conn.execute(text(f"""
                        INSERT INTO order_items (order_id, variant_id, quantity, unit_price, discount_applied, 
                                                line_total, fulfillment_status)
                        VALUES ({order_id}, {variant_id}, {qty}, {unit_price}, {discount}, {line_total}, '{fulfillment}');
                    """))
            
            # === SEED EMPLOYEE COMMISSIONS ===
            print("🌱 Seeding employee_commissions (80 commissions)...")
            for order_id in random.sample(range(1, 101), 80):  # 80 orders have commissions
                emp_id = random.randint(6, 9)  # Sales team
                order_total_query = conn.execute(text(f"SELECT total_amount FROM orders WHERE order_id = {order_id}"))
                order_total = order_total_query.fetchone()[0]
                commission = round(float(order_total) * random.uniform(0.02, 0.035), 2)
                comm_date = (datetime.now() - timedelta(days=random.randint(1, 90))).strftime('%Y-%m-%d')
                payment_status = random.choice(['pending', 'pending', 'paid', 'paid'])  # 50% paid
                payment_date = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d') if payment_status == 'paid' else None
                payment_date_value = f"'{payment_date}'" if payment_date is not None else "NULL"
                
                conn.execute(text(f"""
                    INSERT INTO employee_commissions (employee_id, order_id, commission_amount, commission_date, 
                                                      payment_status, payment_date)
                    VALUES ({emp_id}, {order_id}, {commission}, '{comm_date}', '{payment_status}', 
                            {payment_date_value});
                """))
            
            # === SEED INVENTORY MOVEMENTS ===
            print("🌱 Seeding inventory_movements (200 movements)...")
            movement_types = ['stock_in', 'stock_out', 'transfer', 'adjustment', 'return']
            for i in range(200):
                variant_id = random.randint(1, 120)
                warehouse_id = random.randint(1, 6)
                movement_type = random.choice(movement_types)
                qty = random.randint(-50, 200) if movement_type == 'adjustment' else random.randint(1, 100)
                movement_date = (datetime.now() - timedelta(days=random.randint(1, 180))).strftime('%Y-%m-%d %H:%M:%S')
                ref_num = f"MV{random.randint(10000, 99999)}"
                reason = f"{movement_type.replace('_', ' ').title()} - Ref {ref_num}"
                recorded_by = random.randint(1, 40)
                
                conn.execute(text(f"""
                    INSERT INTO inventory_movements (variant_id, warehouse_id, movement_type, quantity, movement_date, 
                                                    reference_number, reason, recorded_by)
                    VALUES ({variant_id}, {warehouse_id}, '{movement_type}', {qty}, '{movement_date}', '{ref_num}', 
                            '{reason}', {recorded_by});
                """))
            
            # === SEED ORDER SHIPMENTS ===
            print("🌱 Seeding order_shipments (70 shipments)...")
            carriers = ['FedEx', 'UPS', 'DHL', 'USPS', 'Blue Dart']
            for order_id in random.sample(range(1, 101), 70):
                warehouse_id = random.randint(1, 6)
                carrier = random.choice(carriers)
                tracking = f"{carrier[:3].upper()}{random.randint(1000000, 9999999)}"
                ship_date = (datetime.now() - timedelta(days=random.randint(5, 60))).strftime('%Y-%m-%d')
                est_delivery = (datetime.now() + timedelta(days=random.randint(3, 10))).strftime('%Y-%m-%d')
                actual_delivery_ship = (datetime.now() - timedelta(days=random.randint(1, 15))).strftime('%Y-%m-%d') if random.random() > 0.3 else None
                actual_delivery_ship_value = f"'{actual_delivery_ship}'" if actual_delivery_ship is not None else "NULL"
                cost = round(random.uniform(10, 50), 2)
                weight = round(random.uniform(0.5, 20), 2)
                status = random.choice(['pending', 'in_transit', 'delivered', 'returned'])
                
                conn.execute(text(f"""
                    INSERT INTO order_shipments (order_id, warehouse_id, carrier, tracking_number, shipment_date, 
                                                estimated_delivery, actual_delivery, shipment_cost, weight_kg, status)
                    VALUES ({order_id}, {warehouse_id}, '{carrier}', '{tracking}', '{ship_date}', '{est_delivery}', 
                            {actual_delivery_ship_value}, {cost}, {weight}, '{status}');
                """))
            
            # === SEED PRODUCT REVIEWS ===
            print("🌱 Seeding product_reviews (150 reviews)...")
            review_titles = [
                "Great product!", "Love it!", "Not what I expected", "Amazing quality", "Poor quality",
                "Good value for money", "Exceeded expectations", "Disappointed", "Highly recommend", "Waste of money"
            ]
            for i in range(150):
                product_id = random.randint(1, 30)
                customer_id = random.randint(1, 50)
                order_id = random.randint(1, 100)
                rating = random.choices([1, 2, 3, 4, 5], weights=[5, 8, 15, 30, 42])[0]  # Skewed toward positive
                title = random.choice(review_titles)
                review_text = f"This is a review for product {product_id}. Rating: {rating}/5. {title}"
                review_date = (datetime.now() - timedelta(days=random.randint(1, 200))).strftime('%Y-%m-%d')
                verified = random.choice([True, True, False])  # 67% verified
                helpful = random.randint(0, 50)
                
                conn.execute(text(f"""
                    INSERT INTO product_reviews (product_id, customer_id, order_id, rating, review_title, review_text, 
                                                review_date, is_verified_purchase, helpful_votes)
                    VALUES ({product_id}, {customer_id}, {order_id}, {rating}, '{title}', '{review_text}', 
                            '{review_date}', {verified}, {helpful});
                """))
            
            conn.commit()
            
            print("✅ Database Setup Complete!")
            print(f"📊 Created 15 interconnected tables:")
            print(f"   • sales_data (legacy): 50 rows")
            print(f"   • customer_segments: 5 tiers")
            print(f"   • customers: 50 with loyalty tiers")
            print(f"   • warehouses: 6 locations")
            print(f"   • departments: 8 departments")
            print(f"   • employees: 40 with hierarchy")
            print(f"   • suppliers: 15 suppliers")
            print(f"   • products: 30 products")
            print(f"   • product_variants: 120 SKUs")
            print(f"   • orders: 100 orders")
            print(f"   • order_items: 250+ line items")
            print(f"   • employee_commissions: 80 commissions")
            print(f"   • inventory_movements: 200 movements")
            print(f"   • order_shipments: 70 shipments")
            print(f"   • product_reviews: 150 reviews")
            print(f"\n🎯 Try complex queries like:")
            print(f"   'Show top 5 customers by lifetime value'")
            print(f"   'Which products have stock below reorder level?'")
            print(f"   'Calculate total unpaid commissions by employee'")
            print(f"   'Show average order value by customer segment'")
            print(f"   'Which warehouse has highest utilization?'")
            print(f"   'Products with average rating below 3 stars'")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    setup_data()