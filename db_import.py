#!/usr/bin/env python3
import argparse
import hashlib
import re
import time
import os
from datetime import date
from pathlib import Path
from typing import Iterator, List, Tuple
from dotenv import load_dotenv

import clickhouse_connect
from tqdm.auto import tqdm

load_dotenv()

CH_HOST = os.getenv('CH_HOST')
CH_PORT = int(os.getenv('CH_PORT', 8123))
CH_USER = os.getenv('CH_USER')
CH_PASSWORD = os.getenv('CH_PASSWORD')
CH_DATABASE = os.getenv('CH_DATABASE', 'parolam')

def get_or_create_breach_id(client: clickhouse_connect.driver.Client, breach_name: str, breach_date: date) -> int:
    print(f"'{breach_name}' sızıntısı için ID kontrol ediliyor...")
    result = client.query(
        'SELECT breach_id FROM breach_metadata WHERE breach_name = %(name)s LIMIT 1',
        parameters={'name': breach_name}
    )
    if result.result_rows:
        breach_id = result.result_rows[0][0]
        print(f"Mevcut sızıntı bulundu. ID: {breach_id}")
        return breach_id
    
    print("Sızıntı bulunamadı, yeni kayıt oluşturuluyor...")
    max_id_result = client.query('SELECT max(breach_id) FROM breach_metadata')
    next_id = (max_id_result.result_rows[0][0] or 0) + 1
    new_breach_data = [[next_id, breach_name, breach_date, '']]
    client.insert(
        'breach_metadata', 
        new_breach_data, 
        column_names=['breach_id', 'breach_name', 'breach_date', 'description']
    )
    print(f"Yeni sızıntı oluşturuldu. ID: {next_id}")
    return next_id

def split_hash(hex_hash: str) -> Tuple[str, str]:
    return hex_hash[:6], hex_hash[6:]

DELIM = re.compile(r"[:,;\t]")
def iter_lines(fp: Path) -> Iterator[Tuple[str, str]]:
    with fp.open(encoding="utf-8", errors="ignore") as f:
        for raw in f:
            p = DELIM.split(raw.strip(), maxsplit=1)
            if len(p) == 2 and p[0] and p[1]:
                yield p[0], p[1]

def main():
    parser = argparse.ArgumentParser(description="Sızıntı verilerini yeni ClickHouse şemasına aktarır.")
    parser.add_argument("--input", required=True, help="İçe aktarılacak .txt dosyalarını içeren klasör.")
    parser.add_argument("--batch-size", type=int, default=int(os.getenv('BATCH_SIZE', 100000)), help="ClickHouse'a tek seferde gönderilecek satır sayısı.")
    args = parser.parse_args()

    email_batch: List[Tuple[str, str, int, int]] = []
    password_batch: List[Tuple[str, str, int]] = []
    
    try:
        client = clickhouse_connect.get_client(
            host=CH_HOST, port=CH_PORT, user=CH_USER, password=CH_PASSWORD, database=CH_DATABASE
        )
        client.ping()
    except Exception as e:
        print(f"❌ ClickHouse'a bağlanılamadı: {e}")
        return

    breach_name = os.getenv('DEFAULT_BREACH_NAME', 'Collection-1')
    if not breach_name:
        print("❌ Sızıntı adı boş olamaz.")
        return
    
    while True:
        date_input = os.getenv('DEFAULT_BREACH_DATE', '19-01-2019')
        try:
            day, month, year = map(int, date_input.split('-'))
            breach_date = date(year, month, day)
            break
        except (ValueError, TypeError):
            print("❌ Geçersiz tarih formatı. Lütfen gün-ay-yıl formatında girin (örn: 15-07-2025)")
    
    breach_id = get_or_create_breach_id(client, breach_name, breach_date)

    def flush_batches():
        nonlocal email_batch, password_batch
        if email_batch:
            client.insert('email_leaks', email_batch, column_names=['email_prefix', 'email_suffix', 'breach_id', 'version'])
            email_batch.clear()
        if password_batch:
            client.insert('password_leaks', password_batch, column_names=['hash_prefix', 'hash_suffix', 'prevalence'])
            password_batch.clear()

    files_to_process = sorted(Path(args.input).rglob("*.txt"), key=lambda x: (x.parent.name, int(x.stem) if x.stem.isdigit() else float('inf')))
    if not files_to_process:
        print(f"❌ '{args.input}' klasöründe hiç .txt dosyası bulunamadı.")
        return

    total_rows_processed = 0
    print("\nVeri aktarımı başlıyor...")

    total_lines = 0
    for file_path in files_to_process:
        try:
            total_lines += sum(1 for _ in file_path.open(encoding="utf-8", errors="ignore"))
        except Exception as e:
            print(f"⚠️ '{file_path.name}' satır sayısı hesaplanırken hata: {e}")

    with tqdm(total=total_lines, desc="Veri işleniyor", unit="satır") as pbar:
        for file_path in files_to_process:
            pbar.set_postfix_str(f"Dosya: {file_path.name}")
            try:
                for email, password in iter_lines(file_path):
                    email_hash = hashlib.sha1(email.encode('utf-8')).hexdigest().upper()
                    email_prefix, email_suffix = split_hash(email_hash)
                    
                    password_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
                    pw_prefix, pw_suffix = split_hash(password_hash)
                    
                    email_batch.append((email_prefix, email_suffix, breach_id, int(time.time())))
                    password_batch.append((pw_prefix, pw_suffix, 1))
                    
                    if len(email_batch) >= args.batch_size:
                        flush_batches()
                        total_rows_processed += args.batch_size
                        pbar.set_postfix_str(f"Dosya: {file_path.name} | Toplam: {total_rows_processed:,}")
                    pbar.update(1)
            except Exception as e:
                print(f"\n⚠️ '{file_path.name}' işlenirken bir hata oluştu: {e}")
                continue

    print("\nSon kalan veriler gönderiliyor...")
    remaining_count = len(email_batch)
    if remaining_count > 0:
        flush_batches()
        total_rows_processed += remaining_count

    print(f"\n✔ Aktarım tamamlandı! Toplam {total_rows_processed:,} satır işlendi.")

if __name__ == "__main__":
    main()