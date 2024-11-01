import pdfplumber
import pandas as pd
import os
import re


def fill_empty_cells(headers):
    """
    Fill empty cells in the header row by carrying values down from the row above.
    """
    for row in range(1, len(headers)):
        for col in range(len(headers[row])):
            if headers[row][col] is None or headers[row][col] == '':
                headers[row][col] = headers[row - 1][col]  # Carry down value from above
    return headers

def extract_and_structure_data(pdf_path):
    structured_data = {}

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            page_tables = page.extract_tables()
            combined_df = pd.DataFrame()  # Initialize an empty DataFrame for combining tables on the page
            headers = None  # Only set headers once per page
            data_start_index = None

            for table_num, table in enumerate(page_tables, start=1):
                try:
                    df = pd.DataFrame(table)

                    # Remove rows that are entirely empty
                    df = df.dropna(how='all').reset_index(drop=True)

                    # Check for headers if not already set for this page
                    if headers is None:
                        headers = []
                        for i, row in df.iterrows():
                            # Determine if this row looks like a header row (contains mostly text)
                            if any(isinstance(cell, str) and re.search(r"\b(year|date|name)\b", cell, re.IGNORECASE) for cell in row):
                                data_start_index = i
                                break
                            # If row has mostly text or identifiable labels, add it to headers
                            if sum(isinstance(cell, str) for cell in row) > len(row) // 2:
                                headers.append(row.tolist())

                        # Fill empty header cells and set bottom layer as final header
                        headers = fill_empty_cells(headers)
                        bottom_layer_header = headers[-1] if headers else [f'Column_{i+1}' for i in range(df.shape[1])]

                    # Extract data rows if data_start_index was identified
                    if data_start_index is not None:
                        data_rows = df.iloc[data_start_index:].values
                        table_df = pd.DataFrame(data_rows, columns=bottom_layer_header)
                        combined_df = pd.concat([combined_df, table_df], ignore_index=True)
                    else:
                        print(f"Warning: No data rows found on Page {page_num}, Table {table_num} of {pdf_path}")

                except Exception as e:
                    print(f"Error processing Page {page_num}, Table {table_num} of {pdf_path}: {e}")

            # Store the combined data from each page in the structured_data dictionary
            if not combined_df.empty:
                structured_data[page_num] = combined_df

    return structured_data

def save_to_excel(structured_data, output_path):
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        for page_num, combined_df in structured_data.items():
            sheet_name = f"Page{page_num}"
            combined_df.to_excel(writer, sheet_name=sheet_name, index=False)  # Save without index
        print(f"Data saved to {output_path}")


def process_all_pdfs(input_dir='../new/', output_dir='./output/'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(input_dir):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}.xlsx")

            # Extract PDF table data
            structured_data = extract_and_structure_data(pdf_path)

            # Save as a single Excel file per PDF
            save_to_excel(structured_data, output_path)


if __name__ == '__main__':
    process_all_pdfs()