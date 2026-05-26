"""Детальний інспектор рядків Budget"""
import openpyxl

EXCEL_PATH = r"D:\ГО Талан UA\Гранти\Конкурс IREX\2. Project Budget_Бюджет проєкту_шаблон_upd_VK_11.25 - Copy.xlsm"

wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True, keep_vba=True)
ws = wb['Budget']

print(f"\n=== Детальні рядки Budget (rows 10-65) ===\n")
for r in range(10, 66):
    row_vals = [ws.cell(row=r, column=c).value for c in range(2, 12)]
    # print columns B to K (which are 2 to 11 in 1-based indexing)
    row_str = [str(x) if x is not None else "" for x in row_vals]
    if any(row_str):
        print(f"Row {r:02d}: B='{row_str[0]}' | C='{row_str[1]}' | D='{row_str[2]}' | E='{row_str[3]}' | F='{row_str[4]}' | G='{row_str[5]}' | H='{row_str[6]}' | I='{row_str[7]}' | J='{row_str[8]}' | K='{row_str[9]}'")

wb.close()
