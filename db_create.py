#!/usr/bin/env python3
import os
from dotenv import load_dotenv
import clickhouse_connect

load_dotenv()

CH_HOST = os.getenv('CH_HOST', 'localhost')
CH_PORT = int(os.getenv('CH_PORT', 8123))
CH_USER = os.getenv('CH_USER')
CH_PASSWORD = os.getenv('CH_PASSWORD')
CH_DATABASE = os.getenv('CH_DATABASE', 'parolam')

CREATE_DATABASE_SQL = f"CREATE DATABASE IF NOT EXISTS {CH_DATABASE}"

CREATE_BREACH_METADATA_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {CH_DATABASE}.breach_metadata
(
    breach_id       UInt32,
    breach_name     String,
    breach_date     Date,
    description     String
)
ENGINE = MergeTree()
ORDER BY breach_id
"""

CREATE_PASSWORD_LEAKS_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {CH_DATABASE}.password_leaks
(
    hash_prefix     FixedString(6),
    hash_suffix     FixedString(34),
    prevalence      UInt64
)
ENGINE = SummingMergeTree()
ORDER BY (hash_prefix, hash_suffix)
"""

CREATE_EMAIL_LEAKS_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {CH_DATABASE}.email_leaks
(
    email_prefix    FixedString(6),
    email_suffix    FixedString(34),
    breach_id       UInt32,
    version         UInt64
)
ENGINE = ReplacingMergeTree(version)
ORDER BY (email_prefix, email_suffix, breach_id)
"""

def setup_database():
    print("ClickHouse veritabanı ve tablo kurulumu başlıyor...")
    try:
        with clickhouse_connect.get_client(
            host=CH_HOST, port=CH_PORT, user=CH_USER, password=CH_PASSWORD
        ) as client:
            print(f"1. Sunucuya bağlanıldı. '{CH_DATABASE}' veritabanı oluşturuluyor...")
            client.command(CREATE_DATABASE_SQL)
            print(f"   '{CH_DATABASE}' veritabanı oluşturuldu.")

            print("\n2. 'breach_metadata' tablosu oluşturuluyor...")
            client.command(CREATE_BREACH_METADATA_TABLE_SQL)
            print("   'breach_metadata' tablosu oluşturuldu.")

            print("\n3. 'password_leaks' tablosu oluşturuluyor...")
            client.command(CREATE_PASSWORD_LEAKS_TABLE_SQL)
            print("   'password_leaks' tablosu oluşturuldu.")

            print("\n4. 'email_leaks' tablosu oluşturuluyor...")
            client.command(CREATE_EMAIL_LEAKS_TABLE_SQL)
            print("   'email_leaks' tablosu oluşturuldu.")

            print("\n✔ Kurulum başarıyla tamamlandı!")
    except Exception as e:
        print(f"❌ Bir hata oluştu: {e}")

if __name__ == "__main__":
    setup_database()
