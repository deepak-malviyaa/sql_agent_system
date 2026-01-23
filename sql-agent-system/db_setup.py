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
            
            # 1. Drop old table
            conn.execute(text("DROP TABLE IF EXISTS sales_data CASCADE;"))
            
            # 2. Create new table
            # We use meaningful column names to help the AI understand
            print("📝 Creating Table 'sales_data'...")
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
            
            # 3. Generate Mock Data
            print("🌱 Seeding 50 rows of data...")
            
            countries = ['USA', 'Germany', 'France', 'India', 'UK', 'Canada']
            products = {
                'Electronics': [('Laptop Pro', 1200), ('Smartphone X', 800), ('Monitor 4K', 400)],
                'Clothing': [('Denim Jacket', 80), ('Running Shoes', 120), ('Cotton T-Shirt', 25)],
                'Home': [('Coffee Maker', 150), ('Smart Bulb', 15), ('Office Chair', 250)]
            }
            methods = ['Credit Card', 'PayPal', 'Bank Transfer']
            
            values_list = []
            
            # Hardcoded specific data to ensure specific questions work
            # (Ensures "Revenue from Germany" isn't zero)
            values_list.append("('2023-10-01', 'Electronics', 'Laptop Pro', 5, 1200.00, 6000.00, 'Germany', 'Credit Card')")
            values_list.append("('2023-10-05', 'Clothing', 'Running Shoes', 10, 120.00, 1200.00, 'Germany', 'PayPal')")
            values_list.append("('2023-11-12', 'Electronics', 'Smartphone X', 2, 800.00, 1600.00, 'USA', 'Credit Card')")

            # Random generation for the rest
            for _ in range(50):
                cat = random.choice(list(products.keys()))
                prod, price = random.choice(products[cat])
                qty = random.randint(1, 10)
                total = price * qty
                country = random.choice(countries)
                method = random.choice(methods)
                date = (datetime.now() - timedelta(days=random.randint(1, 365))).strftime('%Y-%m-%d')
                
                values_list.append(f"('{date}', '{cat}', '{prod}', {qty}, {price}, {total}, '{country}', '{method}')")

            # Insert all data
            sql = f"""
                INSERT INTO sales_data 
                (transaction_date, product_category, product_name, units_sold, unit_price, total_revenue, country, payment_method)
                VALUES {", ".join(values_list)};
            """
            conn.execute(text(sql))
            conn.commit()
            
            print("✅ Database Setup Complete! Table 'sales_data' is ready.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    setup_data()