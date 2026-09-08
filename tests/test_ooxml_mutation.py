import io
import unittest
import zipfile

import openpyxl
from lxml import etree

from core.docgen.template_engine import mutate_xlsx

SHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"

def build_dummy_template():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        # [Content_Types].xml
        ct = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="xml" ContentType="application/xml"/>
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
    <Override PartName="/xl/calcChain.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.calcChain+xml"/>
    <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>"""
        zf.writestr("[Content_Types].xml", ct)

        # xl/_rels/workbook.xml.rels
        rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
    <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/calcChain" Target="calcChain.xml"/>
</Relationships>"""
        zf.writestr("xl/_rels/workbook.xml.rels", rels)

        # xl/workbook.xml
        wb = """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <calcPr calcId="12345"/>
    <sheets>
        <sheet name="pxk" sheetId="1" r:id="rId1"/>
    </sheets>
</workbook>"""
        zf.writestr("xl/workbook.xml", wb)

        # xl/calcChain.xml
        cc = """<?xml version="1.0" encoding="UTF-8"?>
<calcChain xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
    <c r="B15" i="1"/>
</calcChain>"""
        zf.writestr("xl/calcChain.xml", cc)
        
        # _rels/.rels
        rels_root = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""
        zf.writestr("_rels/.rels", rels_root)

        # xl/worksheets/sheet1.xml (pxk)
        ws = """<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
    <sheetData>
        <row r="15">
            <c r="B15"><f>A15*2</f><v>4</v></c>
        </row>
        <row r="28">
            <c r="F28"><f>SUM(F15:F27)</f><v>10</v></c>
        </row>
    </sheetData>
</worksheet>"""
        zf.writestr("xl/worksheets/sheet1.xml", ws)

    return buffer.getvalue()


class TestOOXMLMutation(unittest.TestCase):
    def test_pxk_formula_removal(self):
        tpl = build_dummy_template()
        with open("/tmp/dummy_tpl.xlsx", "wb") as f:
            f.write(tpl)
            
        # 1. PXK original B15 contains formula before mutation
        with zipfile.ZipFile("/tmp/dummy_tpl.xlsx") as zf:
            ws = etree.fromstring(zf.read("xl/worksheets/sheet1.xml"))
            b15 = ws.find(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c[@r='B15']")
            self.assertIsNotNone(b15.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}f"))

        fill = {
            "pxk": {
                "B15": 100,
            }
        }
        
        import hashlib
        sha_before = hashlib.sha256(tpl).hexdigest()
        
        res = mutate_xlsx("/tmp/dummy_tpl.xlsx", fill)
        
        # 7. Source template SHA remains unchanged
        with open("/tmp/dummy_tpl.xlsx", "rb") as f:
            sha_after = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(sha_before, sha_after)

        with open("/tmp/dummy_out.xlsx", "wb") as f:
            f.write(res)
            
        with zipfile.ZipFile(io.BytesIO(res)) as zf:
            # 2. Generated PXK B15 contains explicit value, not formula
            ws = etree.fromstring(zf.read("xl/worksheets/sheet1.xml"))
            b15 = ws.find(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c[@r='B15']")
            self.assertIsNone(b15.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}f"))
            v = b15.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v")
            self.assertEqual(v.text, "100")
            
            # 3. Generated PXK has no dangling calcChain relationship/content-type entry after formula removal
            self.assertNotIn("xl/calcChain.xml", zf.namelist())
            
            rels = etree.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
            has_calc_rel = False
            for rel in rels.findall("{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"):
                if "calcChain" in rel.get("Target"):
                    has_calc_rel = True
            self.assertFalse(has_calc_rel)
            
            ct = etree.fromstring(zf.read("[Content_Types].xml"))
            has_calc_ct = False
            for override in ct.findall("{http://schemas.openxmlformats.org/package/2006/content-types}Override"):
                if "calcChain" in override.get("PartName"):
                    has_calc_ct = True
            self.assertFalse(has_calc_ct)
            
            # 5, 6. Generated PL/HDMB retains formulas
            f28 = ws.find(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c[@r='F28']")
            self.assertIsNotNone(f28.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}f"))

        # 4. Generated workbook remains loadable by openpyxl
        wb = openpyxl.load_workbook("/tmp/dummy_out.xlsx")
        self.assertIn("pxk", wb.sheetnames)

if __name__ == '__main__':
    unittest.main()
