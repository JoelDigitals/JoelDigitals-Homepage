# Migration 0037 - Add missing ReturnRequest columns (database-agnostic, safe)
# Uses RunPython to check column existence before adding — works with SQLite, PostgreSQL, MySQL.

from django.db import migrations, connection


def add_missing_columns(apps, schema_editor):
    db = schema_editor.connection.vendor  # 'sqlite', 'postgresql', 'mysql'

    # Columns to add: (table, column, sql_type_sqlite, sql_type_pg)
    columns = [
        ('shop_ourapps_returnrequest', 'tracking_number',  "VARCHAR(100) NOT NULL DEFAULT ''", "VARCHAR(100) NOT NULL DEFAULT ''"),
        ('shop_ourapps_returnrequest', 'tracking_carrier', "VARCHAR(50) NOT NULL DEFAULT ''",  "VARCHAR(50) NOT NULL DEFAULT ''"),
        ('shop_ourapps_returnrequest', 'tracking_url',     "VARCHAR(200) NOT NULL DEFAULT ''", "VARCHAR(200) NOT NULL DEFAULT ''"),
        ('shop_ourapps_returnrequest', 'return_label_url', "VARCHAR(200) NOT NULL DEFAULT ''", "VARCHAR(200) NOT NULL DEFAULT ''"),
        ('shop_ourapps_returnrequest', 'refund_amount',    "DECIMAL(10,2) NULL",               "NUMERIC(10,2) NULL"),
        ('shop_ourapps_returnrequest', 'refund_method',    "VARCHAR(50) NOT NULL DEFAULT ''",  "VARCHAR(50) NOT NULL DEFAULT ''"),
        ('shop_ourapps_returnrequest', 'refunded_at',      "DATETIME NULL",                    "TIMESTAMP WITH TIME ZONE NULL"),
    ]

    with schema_editor.connection.cursor() as cursor:
        # Get existing columns for the table
        if db == 'sqlite':
            cursor.execute("PRAGMA table_info(shop_ourapps_returnrequest)")
            existing = {row[1] for row in cursor.fetchall()}
        elif db == 'postgresql':
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'shop_ourapps_returnrequest'
            """)
            existing = {row[0] for row in cursor.fetchall()}
        else:  # mysql / mariadb
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = DATABASE()
                AND table_name = 'shop_ourapps_returnrequest'
            """)
            existing = {row[0] for row in cursor.fetchall()}

        # Add each missing column
        for table, col, sqlite_type, pg_type in columns:
            if col not in existing:
                col_type = pg_type if db == 'postgresql' else sqlite_type
                sql = f'ALTER TABLE {table} ADD COLUMN {col} {col_type}'
                cursor.execute(sql)
                print(f'  Added: {table}.{col}')
            else:
                print(f'  Exists: {table}.{col} (skipped)')

        # ShipmentTracking: check if table exists
        if db == 'sqlite':
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='shop_ourapps_shipmenttracking'")
            table_exists = cursor.fetchone() is not None
        elif db == 'postgresql':
            cursor.execute("SELECT to_regclass('shop_ourapps_shipmenttracking')")
            table_exists = cursor.fetchone()[0] is not None
        else:
            cursor.execute("SHOW TABLES LIKE 'shop_ourapps_shipmenttracking'")
            table_exists = cursor.fetchone() is not None

        if not table_exists:
            if db in ('sqlite', 'mysql'):
                cursor.execute("""
                    CREATE TABLE shop_ourapps_shipmenttracking (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        carrier VARCHAR(20) NOT NULL,
                        tracking_number VARCHAR(100) NOT NULL,
                        tracking_url VARCHAR(200) NOT NULL DEFAULT '',
                        dispatched_at DATETIME NULL,
                        estimated_delivery DATE NULL,
                        note VARCHAR(255) NOT NULL DEFAULT '',
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        order_id INTEGER NOT NULL UNIQUE REFERENCES shop_ourapps_order(id) ON DELETE CASCADE
                    )
                """)
            else:  # postgresql
                cursor.execute("""
                    CREATE TABLE shop_ourapps_shipmenttracking (
                        id BIGSERIAL PRIMARY KEY,
                        carrier VARCHAR(20) NOT NULL,
                        tracking_number VARCHAR(100) NOT NULL,
                        tracking_url VARCHAR(200) NOT NULL DEFAULT '',
                        dispatched_at TIMESTAMP WITH TIME ZONE NULL,
                        estimated_delivery DATE NULL,
                        note VARCHAR(255) NOT NULL DEFAULT '',
                        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        order_id BIGINT NOT NULL UNIQUE REFERENCES shop_ourapps_order(id) ON DELETE CASCADE
                    )
                """)
            print('  Created: shop_ourapps_shipmenttracking')
        else:
            print('  Exists: shop_ourapps_shipmenttracking (skipped)')


class Migration(migrations.Migration):

    dependencies = [
        ('shop_ourapps', '0036_remove_order_stripe_session_id_and_more'),
    ]

    operations = [
        migrations.RunPython(add_missing_columns, migrations.RunPython.noop),
    ]
