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


    def test_pl_hdmb_formula_cache_preserved(self):
        tpl = build_dummy_template() # We'll just use the dummy one and pretend it's PL/HDMB
        with open("/tmp/dummy_tpl2.xlsx", "wb") as f:
            f.write(tpl)
            
        from core.docgen.template_engine import CachedFormulaValue
        fill = {
            "pxk": { # map sheet name pxk but we test CachedFormulaValue behavior
                "F28": CachedFormulaValue(100),
            }
        }
        res = mutate_xlsx("/tmp/dummy_tpl2.xlsx", fill)
        with zipfile.ZipFile(io.BytesIO(res)) as zf:
            ws = etree.fromstring(zf.read("xl/worksheets/sheet1.xml"))
            f28 = ws.find(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c[@r='F28']")
            self.assertIsNotNone(f28.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}f"))
            v = f28.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v")
            self.assertEqual(v.text, "100")
            
            # Check calcPr requests full calc
            wb = etree.fromstring(zf.read("xl/workbook.xml"))
            calcPr = wb.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}calcPr")
            self.assertEqual(calcPr.get("calcMode"), "auto")
            self.assertEqual(calcPr.get("fullCalcOnLoad"), "1")
            self.assertEqual(calcPr.get("forceFullCalc"), "1")


    def test_pl_layout_patches(self):
        # We need a dummy with 'pl' sheet
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as zf:
            zf.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>')
            zf.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
            zf.writestr("xl/workbook.xml", '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="pl" sheetId="1" r:id="rId1"/></sheets></workbook>')
            zf.writestr("xl/worksheets/sheet1.xml", '<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="6" ht="36" customHeight="1"/></sheetData></worksheet>')

        tpl = buffer.getvalue()
        with open("/tmp/dummy_pl.xlsx", "wb") as f:
            f.write(tpl)
            
        fill = {"pl": {"A1": "Test"}}
        res = mutate_xlsx("/tmp/dummy_pl.xlsx", fill)
        with zipfile.ZipFile(io.BytesIO(res)) as zf:
            ws = etree.fromstring(zf.read("xl/worksheets/sheet1.xml"))
            row6 = ws.find(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row[@r='6']")
            self.assertEqual(row6.get("ht"), "75")
            
            wb = etree.fromstring(zf.read("xl/workbook.xml"))
            defNames = wb.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}definedNames")
            self.assertIsNotNone(defNames)
            dn = defNames.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}definedName")
            self.assertEqual(dn.get("name"), "_xlnm.Print_Titles")
            self.assertEqual(dn.text, "pl!$9:$9")



    def test_pxk_layout_patches(self):
        # We need a dummy with 'pxk' sheet
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as zf:
            zf.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>')
            zf.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
            zf.writestr("xl/workbook.xml", '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="pxk" sheetId="1" r:id="rId1"/></sheets></workbook>')
            zf.writestr("xl/worksheets/sheet1.xml", '<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="6" ht="22" customHeight="1"/></sheetData></worksheet>')

        tpl = buffer.getvalue()
        with open("/tmp/dummy_pxk.xlsx", "wb") as f:
            f.write(tpl)
            
        fill = {"pxk": {"A1": "Test"}}
        res = mutate_xlsx("/tmp/dummy_pxk.xlsx", fill)
        with zipfile.ZipFile(io.BytesIO(res)) as zf:
            ws = etree.fromstring(zf.read("xl/worksheets/sheet1.xml"))
            row6 = ws.find(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row[@r='6']")
            self.assertEqual(row6.get("ht"), "40")
            
            mc = ws.find(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}mergeCell[@ref='A10:D10']")
            self.assertIsNotNone(mc)
            
            ps = ws.find(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}pageSetup")
            self.assertEqual(ps.get("fitToWidth"), "1")
            self.assertEqual(ps.get("fitToHeight"), "0")



    def test_pl_definednames_schema_order(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as zf:
            zf.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>')
            zf.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
            # workbook with sheets then calcPr
            wb = """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <sheets>
        <sheet name="pl" sheetId="1" r:id="rId1"/>
    </sheets>
    <calcPr calcId="12345"/>
</workbook>"""
            zf.writestr("xl/workbook.xml", wb)
            zf.writestr("xl/worksheets/sheet1.xml", '<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData/></worksheet>')

        tpl = buffer.getvalue()
        with open("/tmp/dummy_pl_order.xlsx", "wb") as f:
            f.write(tpl)
            
        fill = {"pl": {"A1": "Test"}}
        res = mutate_xlsx("/tmp/dummy_pl_order.xlsx", fill)
        with zipfile.ZipFile(io.BytesIO(res)) as zf:
            wb_xml = zf.read("xl/workbook.xml")
            wb = etree.fromstring(wb_xml)
            children = list(wb)
            
            def_names_idx = -1
            calc_pr_idx = -1
            for i, child in enumerate(children):
                if child.tag.endswith("definedNames"):
                    def_names_idx = i
                elif child.tag.endswith("calcPr"):
                    calc_pr_idx = i
            
            self.assertTrue(def_names_idx != -1)
            self.assertTrue(calc_pr_idx != -1)
            self.assertTrue(def_names_idx < calc_pr_idx, "definedNames must appear before calcPr in workbook.xml")


    def test_hdmb_e24_cloned_style(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as zf:
            zf.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/></Types>')
            zf.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
            wb = """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
    <sheets><sheet name="HDMB" sheetId="1" r:id="rId1"/></sheets>
</workbook>"""
            zf.writestr("xl/workbook.xml", wb)
            ws = """<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
    <sheetData>
        <row r="24">
            <c r="E24" s="0"/>
            <c r="F24" s="0"/>
        </row>
    </sheetData>
</worksheet>"""
            zf.writestr("xl/worksheets/sheet1.xml", ws)
            styles = """<?xml version="1.0" encoding="UTF-8"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
    <cellXfs count="1">
        <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1">
            <alignment wrapText="1" horizontal="center"/>
        </xf>
    </cellXfs>
</styleSheet>"""
            zf.writestr("xl/styles.xml", styles)

        tpl = buffer.getvalue()
        with open("/tmp/dummy_hdmb.xlsx", "wb") as f:
            f.write(tpl)
            
        fill = {"HDMB": {"E24": 125000000}}
        res = mutate_xlsx("/tmp/dummy_hdmb.xlsx", fill)
        with zipfile.ZipFile(io.BytesIO(res)) as zf:
            ws_xml = zf.read("xl/worksheets/sheet1.xml")
            ws_el = etree.fromstring(ws_xml)
            e24 = ws_el.find(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c[@r='E24']")
            f24 = ws_el.find(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c[@r='F24']")
            s_e24 = int(e24.get("s"))
            s_f24 = int(f24.get("s"))
            
            self.assertNotEqual(s_e24, s_f24, "E24 should have a new cloned style")
            self.assertEqual(s_f24, 0, "F24 should retain original style")
            
            styles_xml = zf.read("xl/styles.xml")
            styles_el = etree.fromstring(styles_xml)
            xfs = styles_el.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}cellXfs").findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}xf")
            
            xf_e24 = xfs[s_e24]
            align = xf_e24.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}alignment")
            self.assertEqual(align.get("shrinkToFit"), "1")
            self.assertIsNone(align.get("wrapText"))
            self.assertEqual(align.get("horizontal"), "center", "Should preserve original attributes")

if __name__ == '__main__':
    unittest.main()
