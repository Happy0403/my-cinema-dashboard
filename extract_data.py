import pdfplumber
import pandas as pd
import sys

def extract_pdf_data(pdf_path, csv_path):
    print(f"Reading {pdf_path}...")
    headers = ["No", "邦題", "原題", "公開年", "評価", "殿堂入り", "鑑賞日", "鑑賞場所", "上映方式"]
    all_rows = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            print(f"Extracting table from page {i+1}...")
            table = page.extract_table()
            
            if table:
                for row in table:
                    # Basic validation: ensure row has enough columns and 'No' is digit
                    if len(row) >= 12 and row[1] and str(row[1]).strip().isdigit():
                        no = str(row[1]).strip()
                        
                        # sometimes 邦題 is split across col 2 and 3 due to newlines wrap
                        title_pt1 = str(row[2] or '').replace('\n', '')
                        title_pt2 = str(row[3] or '').replace('\n', '')
                        title = (title_pt1 + title_pt2).strip()
                        
                        original_title = str(row[4] or '').replace('\n', '').strip()
                        year = str(row[5] or '').replace('\n', '').strip()
                        rating = str(row[6] or '').replace('\n', '').strip()
                        
                        # 殿堂入り is col 7
                        hall_of_fame_raw = str(row[7] or '').strip()
                        hall_of_fame = hall_of_fame_raw in ['*', '★', '☆', '1']
                        
                        # 鑑賞日 col 9, 鑑賞場所 col 10, 上映方式 col 11
                        date = str(row[9] or '').replace('\n', '').strip() if len(row) > 9 else ""
                        location = str(row[10] or '').replace('\n', '').strip() if len(row) > 10 else ""
                        format_ = str(row[11] or '').replace('\n', '').strip() if len(row) > 11 else ""
                        
                        all_rows.append([
                            no, title, original_title, year, rating, hall_of_fame, date, location, format_
                        ])

    if not all_rows:
        print("No valid data rows found in the PDF.")
        return
        
    df = pd.DataFrame(all_rows, columns=headers)
    df.replace('', pd.NA, inplace=True)
    
    # Convert 'No' to integer for proper sorting later
    df['No'] = pd.to_numeric(df['No'], errors='coerce').astype('Int64')
    
    print("Initial Data Sample:")
    print(df.head())
    
    print(f"Writing to {csv_path}...")
    df.to_csv(csv_path, index=False, encoding='utf-8-sig') # utf-8-sig for excel compatibility
    print("Extraction complete!")

if __name__ == "__main__":
    pdf_file = "🎥映画記録 - 鑑賞記録.pdf"
    csv_file = "movies_data.csv"
    extract_pdf_data(pdf_file, csv_file)
