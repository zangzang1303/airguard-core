import zipfile, os, csv, xml.sax.saxutils

def escape_xml(s):
    return xml.sax.saxutils.escape(str(s))

def col_to_letter(col_idx):
    # col_idx is 1-indexed
    result = ''
    while col_idx > 0:
        col_idx, remainder = divmod(col_idx - 1, 26)
        result = chr(65 + remainder) + result
    return result

def create_xlsx_from_csvs(csv_files_with_names, output_xlsx_path):
    os.makedirs(os.path.dirname(output_xlsx_path), exist_ok=True)
    
    with zipfile.ZipFile(output_xlsx_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        # 1. [Content_Types].xml
        content_types = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
            '  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
            '  <Default Extension="xml" ContentType="application/xml"/>',
            '  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
            '  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        ]
        for i in range(1, len(csv_files_with_names) + 1):
            content_types.append(f'  <Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')
        content_types.append('</Types>')
        z.writestr('[Content_Types].xml', '\n'.join(content_types))

        # 2. _rels/.rels
        rels = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
            '  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>',
            '</Relationships>'
        ]
        z.writestr('_rels/.rels', '\n'.join(rels))

        # 3. xl/styles.xml
        styles = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
            '  <fonts count="2">',
            '    <font><name val="Calibri"/><sz val="11"/></font>',
            '    <font><b/><name val="Calibri"/><sz val="11"/></font>',
            '  </fonts>',
            '  <fills count="2">',
            '    <fill><patternFill patternType="none"/></fill>',
            '    <fill><patternFill patternType="gray125"/></fill>',
            '  </fills>',
            '  <borders count="1">',
            '    <border><left/><right/><top/><bottom/></border>',
            '  </borders>',
            '  <cellStyleXfs count="1">',
            '    <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>',
            '  </cellStyleXfs>',
            '  <cellXfs count="2">',
            '    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>',
            '    <xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0"/>',
            '  </cellXfs>',
            '</styleSheet>'
        ]
        z.writestr('xl/styles.xml', '\n'.join(styles))

        # 4. xl/workbook.xml
        wb_xml = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">',
            '  <sheets>'
        ]
        for i, (name, _) in enumerate(csv_files_with_names, 1):
            wb_xml.append(f'    <sheet name="{escape_xml(name)}" sheetId="{i}" r:id="rId{i}"/>')
        wb_xml.append('  </sheets>')
        wb_xml.append('</workbook>')
        z.writestr('xl/workbook.xml', '\n'.join(wb_xml))

        # 5. xl/_rels/workbook.xml.rels
        wb_rels = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        ]
        for i in range(1, len(csv_files_with_names) + 1):
            wb_rels.append(f'  <Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>')
        wb_rels.append(f'  <Relationship Id="rId{len(csv_files_with_names) + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>')
        wb_rels.append('</Relationships>')
        z.writestr('xl/_rels/workbook.xml.rels', '\n'.join(wb_rels))

        # 6. Worksheets
        for i, (name, csv_path) in enumerate(csv_files_with_names, 1):
            rows_xml = []
            if os.path.exists(csv_path):
                with open(csv_path, 'r', encoding='utf-8-sig') as cf:
                    reader = csv.reader(cf)
                    for r_idx, row in enumerate(reader, 1):
                        cells_xml = []
                        for c_idx, val in enumerate(row, 1):
                            if val:
                                col_letter = col_to_letter(c_idx)
                                cell_ref = f"{col_letter}{r_idx}"
                                # inline string
                                cells_xml.append(f'<c r="{cell_ref}" t="inlineStr"><is><t>{escape_xml(val)}</t></is></c>')
                        if cells_xml:
                            rows_xml.append(f'<row r="{r_idx}">' + ''.join(cells_xml) + '</row>')
            
            ws_xml = [
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
                '  <sheetData>',
                '    ' + '\n    '.join(rows_xml),
                '  </sheetData>',
                '</worksheet>'
            ]
            z.writestr(f'xl/worksheets/sheet{i}.xml', '\n'.join(ws_xml))

    print(f'Successfully created {output_xlsx_path} ({os.path.getsize(output_xlsx_path)} bytes)')

if __name__ == '__main__':
    sheets_def = [
        ('Tổng hợp', 'scratch/updated_sheets/01_tong_hop.csv'),
        ('Thành viên nhóm', 'scratch/updated_sheets/02_thanh_vien_nhom.csv'),
        ('Danh sách User Story', 'scratch/updated_sheets/03_danh_sach_user_story.csv'),
        ('Lộ trình', 'scratch/updated_sheets/04_lo_trinh.csv'),
        ('Đường link quan trọng', 'scratch/updated_sheets/05_duong_link_quan_trong.csv'),
        ('Backlog', 'scratch/updated_sheets/06_backlog.csv'),
        ('Đặc tả tính năng', 'scratch/updated_sheets/07_dac_ta_tinh_nang.csv'),
        ('Theo dõi lỗi', 'scratch/updated_sheets/08_theo_doi_loi.csv'),
        ('Tài liệu quan trọng', 'scratch/updated_sheets/09_tai_lieu_quan_trong.csv'),
        ('Hướng dẫn sử dụng', 'scratch/updated_sheets/10_huong_dan_su_dung.csv'),
        ('Lộ Trình 6 Tuần (tham khảo)', 'scratch/updated_sheets/11_lo_trinh_6_tuan.csv'),
        ('Mẫu Báo Cáo Tuần', 'scratch/updated_sheets/12_mau_bao_cao_tuan.csv'),
        ('Project Charter', 'scratch/updated_sheets/13_project_charter.csv'),
        ('API Convention', 'scratch/updated_sheets/14_api_convention.csv'),
        ('Agent Tools', 'scratch/updated_sheets/15_agent_tools.csv'),
        ('Agent Definition', 'scratch/updated_sheets/16_agent_definition.csv'),
        ('Cập nhật 01-09', 'scratch/updated_sheets/17_cap_nhat_01_09.csv')
    ]
    create_xlsx_from_csvs(sheets_def, 'docs/Tu_Ky_Si_Khai_Huyen_P074_Updated.xlsx')
    create_xlsx_from_csvs(sheets_def, 'reports/Tu_Ky_Si_Khai_Huyen_P074_Updated.xlsx')
