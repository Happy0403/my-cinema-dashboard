import pdfplumber

with pdfplumber.open("🎥映画記録 - 鑑賞記録.pdf") as pdf:
    # default settings
    table = pdf.pages[0].extract_table()
    for row in table[:10]:
        print(row)
