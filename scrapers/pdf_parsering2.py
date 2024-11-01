import pdfplumber
import pandas as pd
import os
import re


def fill_empty_cells(headers):
    """
    填充表头中的空单元格，将每一行的空值从上一层填补。
    """
    for row in range(1, len(headers)):
        for col in range(len(headers[row])):
            if headers[row][col] is None or headers[row][col] == '':
                headers[row][col] = headers[row - 1][col]  # 从上一层填补
    return headers


def extract_and_structure_data(pdf_path):
    structured_data = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            page_tables = page.extract_tables()
            for table_num, table in enumerate(page_tables, start=1):
                df = pd.DataFrame(table)

                # 删除全为空值的行
                df = df.dropna(how='all').reset_index(drop=True)

                # 初始化变量
                headers = []  # 用于存储多层表头部分
                data_start_index = None

                # 遍历表格行，查找数据部分的起始位置
                for i, row in df.iterrows():
                    # 判断是否为数据行的起始：包含“year”（不区分大小写）
                    if any(isinstance(cell, str) and re.search(r"year", cell, re.IGNORECASE) for cell in row):
                        data_start_index = i
                        break

                    # 将当前行加入表头
                    headers.append(row.tolist())

                # 填充空单元格，从上一层填补，生成紧凑的表头
                headers = fill_empty_cells(headers)
                bottom_layer_header = headers[-1]  # 使用最底层表头作为最终表头

                # 确保找到数据行的起始位置
                if data_start_index is not None:
                    # 从数据行开始提取数据
                    data_rows = df.iloc[data_start_index:].values

                    # 创建 DataFrame，使用填补后的最接近数据的表头
                    table_df = pd.DataFrame(data_rows, columns=bottom_layer_header)

                    # 添加伪索引，以便导出时格式一致
                    table_df.index = range(1, len(table_df) + 1)
                    structured_data.append((page_num, table_num, table_df))

    return structured_data


def save_to_excel(structured_data, output_path):
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        for page_num, table_num, table_df in structured_data:
            sheet_name = f"Page{page_num}_Table{table_num}"
            table_df.to_excel(writer, sheet_name=sheet_name, index=True)  # 保留索引
        print(f"Data saved to {output_path}")


def process_all_pdfs(input_dir='../new/', output_dir='./output/'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(input_dir):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}.xlsx")

            # 提取 PDF 表格数据
            structured_data = extract_and_structure_data(pdf_path)

            # 保存为对应名称的 Excel 文件
            save_to_excel(structured_data, output_path)


if __name__ == '__main__':
    process_all_pdfs()