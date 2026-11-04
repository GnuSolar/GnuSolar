#! /usr/bin/python3

# Fill an Excel form (xlsx) by editing its XML directly, so form controls
# (check boxes), drop downs, the sheet protection and everything else in the
# workbook stay untouched.
#
# data = {
#   'F10' : 'Muster',        # cell value, str or number
#   'AK15' : True,           # check box anchored at this cell
# }
# images = { 'AG136:BG138' : 'signature.png' }   # image fitted into the cells
#                                                  # or ('signature.png', 1.5), scaled
#                                                  # around the center of the cells

import os
import re
import zipfile

from xml.sax.saxutils import escape

NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL_IMAGE = NS_REL + "/image"


# a number for numeric cells, also from text like "10.5" or "10,5"
def number(value):
    if value is None or isinstance(value, (int, float)):
        return value
    try:
        f = float(str(value).strip().replace(",", "."))
    except ValueError:
        return value
    return int(f) if f.is_integer() else f


def _col_index(col):
    n = 0
    for ch in col:
        n = n * 26 + ord(ch) - ord('A') + 1
    return n


def _col_name(index):
    name = ""
    while index:
        index, rest = divmod(index - 1, 26)
        name = chr(ord('A') + rest) + name
    return name


def _split_ref(ref):
    m = re.match(r'\$?([A-Z]+)\$?(\d+)$', ref)
    return m.group(1), int(m.group(2))


def _rels_path(path):
    d, f = os.path.split(path)
    return d + "/_rels/" + f + ".rels"


def _resolve(base, target):
    if target.startswith("/"):
        return target[1:]
    parts = os.path.dirname(base).split("/")
    for p in target.split("/"):
        if p == "..":
            parts.pop()
        else:
            parts.append(p)
    return "/".join(parts)


def _rels(files, path):
    rels = {}
    xml = files.get(_rels_path(path))
    if xml is None:
        return rels
    for m in re.finditer(r'<Relationship [^>]*>', xml.decode("utf-8")):
        t = m.group(0)
        rid = re.search(r'Id="([^"]+)"', t).group(1)
        target = re.search(r'Target="([^"]+)"', t).group(1)
        rels[rid] = _resolve(path, target)
    return rels


def _sheet_path(files, name):
    workbook = files["xl/workbook.xml"].decode("utf-8")
    rels = _rels(files, "xl/workbook.xml")
    for m in re.finditer(r'<sheet [^>]*>', workbook):
        t = m.group(0)
        sheet_name = re.search(r'name="([^"]+)"', t).group(1)
        rid = re.search(r'r:id="([^"]+)"', t).group(1)
        if name is None or sheet_name == escape(name, {"'": "&apos;"}):
            return rels[rid]
    raise KeyError("Sheet not found: " + str(name))


def _cell_xml(ref, style, value):
    s = ' s="%s"' % style if style else ''
    if isinstance(value, bool):
        return '<c r="%s"%s t="b"><v>%d</v></c>' % (ref, s, value)
    if isinstance(value, (int, float)):
        return '<c r="%s"%s><v>%s</v></c>' % (ref, s, value)
    return '<c r="%s"%s t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>' % (ref, s, escape(str(value)))


def _set_cell(xml, ref, value):
    col, row = _split_ref(ref)
    m = re.search(r'<c r="%s"(?: [^>]*?)?(?:/>|>.*?</c>)' % ref, xml, re.S)
    if m:
        style = re.search(r' s="(\d+)"', m.group(0).split(">")[0])
        new = _cell_xml(ref, style.group(1) if style else None, value)
        return xml[:m.start()] + new + xml[m.end():]

    # cell not there, insert it at the right place in the row
    new = _cell_xml(ref, None, value)
    m = re.search(r'<row r="%d"[^>]*?(/>|>(.*?)</row>)' % row, xml, re.S)
    if not m:
        raise KeyError("Row not found for cell " + ref)
    if m.group(1) == "/>":
        start = m.group(0)[:-2]
        return xml[:m.start()] + start + ">" + new + "</row>" + xml[m.end():]
    for c in re.finditer(r'<c r="([A-Z]+)\d+"', m.group(2)):
        if _col_index(c.group(1)) > _col_index(col):
            pos = m.start(2) + c.start()
            return xml[:pos] + new + xml[pos:]
    pos = m.end(2)
    return xml[:pos] + new + xml[pos:]


# cached values of formulas which just refer to a filled cell (e.g. =F19)
def _update_formula_cache(xml, values):
    def repl(m):
        ref = m.group(2)
        if ref not in values or isinstance(values[ref], bool):
            return m.group(0)
        value = values[ref]
        attrs = re.sub(r' t="[^"]*"', '', m.group(1))
        if isinstance(value, (int, float)):
            return '<c%s><f>%s</f><v>%s</v></c>' % (attrs, ref, value)
        return '<c%s t="str"><f>%s</f><v>%s</v></c>' % (attrs, ref, escape(str(value)))
    xml = re.sub(r'<c( r="[A-Z]+\d+"[^>]*)><f>([A-Z]+\d+)</f>(?:<v>[^<]*</v>)?</c>', repl, xml)

    # and of SUM(A1:B2) over filled numbers, LibreOffice does not recalculate on load
    def repl_sum(m):
        col1, row1 = _split_ref(m.group(2))
        col2, row2 = _split_ref(m.group(3))
        total = 0
        found = False
        for ref, value in values.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            col, row = _split_ref(ref)
            if _col_index(col1) <= _col_index(col) <= _col_index(col2) and row1 <= row <= row2:
                total += value
                found = True
        if not found:
            return m.group(0)
        return '<c%s><f>SUM(%s:%s)</f><v>%s</v></c>' % (m.group(1), m.group(2), m.group(3), total)
    return re.sub(r'<c( r="[A-Z]+\d+"[^>]*)><f>SUM\(([A-Z]+\d+):([A-Z]+\d+)\)</f>(?:<v>[^<]*</v>)?</c>', repl_sum, xml)


def _checkboxes(files, sheet_path, sheet_xml):
    rels = _rels(files, sheet_path)
    boxes = {}
    for m in re.finditer(r'<control shapeId="(\d+)" r:id="([^"]+)"[^>]*>.*?<from><xdr:col>(\d+)</xdr:col>.*?<xdr:row>(\d+)</xdr:row>', sheet_xml, re.S):
        shape_id, rid, col, row = m.groups()
        ref = _col_name(int(col) + 1) + str(int(row) + 1)
        boxes[ref] = (shape_id, rels.get(rid))
    vml = None
    for rid in re.findall(r'<legacyDrawing r:id="([^"]+)"', sheet_xml):
        vml = rels.get(rid)
    return boxes, vml


def _set_checkbox(files, ctrl_path, vml_path, shape_id, checked, linked):
    ctrl = files[ctrl_path].decode("utf-8")
    ctrl = re.sub(r' checked="[^"]*"', '', ctrl)
    if checked:
        ctrl = ctrl.replace("<formControlPr ", '<formControlPr checked="Checked" ', 1)
    files[ctrl_path] = ctrl.encode("utf-8")

    link = re.search(r'fmlaLink="([^"]+)"', ctrl)
    if link:
        sheet, ref = link.group(1).replace("&apos;", "'").rsplit("!", 1)
        linked.append((sheet.strip("'"), ref.replace("$", ""), checked))

    if vml_path:
        vml = files[vml_path].decode("utf-8", errors="surrogateescape")
        m = re.search(r'<v:shape id="_x0000_s%s".*?</v:shape>' % shape_id, vml, re.S)
        if m:
            shape = re.sub(r'\s*<x:Checked>[^<]*</x:Checked>', '', m.group(0))
            if checked:
                shape = shape.replace("</x:ClientData>", "<x:Checked>1</x:Checked></x:ClientData>")
            vml = vml[:m.start()] + shape + vml[m.end():]
            files[vml_path] = vml.encode("utf-8", errors="surrogateescape")


def _image_size(path):
    from PyQt5.QtGui import QImage
    size = QImage(path).size()
    return size.width(), size.height()


# size of a cell range in EMU, from the column widths and row heights
def _range_size(sheet_xml, first, last):
    col1, row1 = _split_ref(first)
    col2, row2 = _split_ref(last)

    fmt = re.search(r'<sheetFormatPr [^>]*>', sheet_xml)
    fmt = fmt.group(0) if fmt else ""
    m = re.search(r'defaultRowHeight="([\d.]+)"', fmt)
    default_height = float(m.group(1)) if m else 15.0
    m = re.search(r'defaultColWidth="([\d.]+)"', fmt) or re.search(r'baseColWidth="([\d.]+)"', fmt)
    default_width = float(m.group(1)) if m else 8.43

    widths = {}
    for c in re.finditer(r'<col [^>]*>', sheet_xml):
        t = c.group(0)
        lo = int(re.search(r'min="(\d+)"', t).group(1))
        hi = int(re.search(r'max="(\d+)"', t).group(1))
        w = float(re.search(r'width="([\d.]+)"', t).group(1))
        for i in range(lo, min(hi, 16384) + 1):
            widths[i] = w

    width = 0
    for i in range(_col_index(col1), _col_index(col2) + 1):
        px = int(widths.get(i, default_width) * 7 + 5)      # Calibri 11, 7px per character
        width += px * 9525
    height = 0
    for r in range(row1, row2 + 1):
        m = re.search(r'<row r="%d"[^>]*?ht="([\d.]+)"' % r, sheet_xml)
        height += (float(m.group(1)) if m else default_height) * 12700
    return width, height


def _add_image(files, sheet_path, sheet_xml, cells, image_path, nr, scale=1.0):
    ext = os.path.splitext(image_path)[1].lower().lstrip(".")
    if ext == "jpg":
        ext = "jpeg"
    if ext not in ("png", "jpeg"):
        raise ValueError("Unsupported image type, use png or jpg: " + image_path)

    rels = _rels(files, sheet_path)
    drawing = None
    for rid in re.findall(r'<drawing r:id="([^"]+)"', sheet_xml):
        drawing = rels.get(rid)
    if drawing is None:
        raise ValueError("Sheet without drawing, can not add image")

    # the image
    media = "xl/media/gnusolar%d.%s" % (nr, ext)
    f = open(image_path, "rb")
    files[media] = f.read()
    f.close()

    types = files["[Content_Types].xml"].decode("utf-8")
    if 'Extension="%s"' % ext not in types:
        types = types.replace("<Default ", '<Default Extension="%s" ContentType="image/%s"/><Default ' % (ext, ext), 1)
        files["[Content_Types].xml"] = types.encode("utf-8")

    # relation from the drawing to the image
    rels_path = _rels_path(drawing)
    rid = "rIdGnuSolar%d" % nr
    rel = '<Relationship Id="%s" Type="%s" Target="../media/%s"/>' % (rid, REL_IMAGE, os.path.basename(media))
    if rels_path in files:
        xml = files[rels_path].decode("utf-8").replace("</Relationships>", rel + "</Relationships>")
    else:
        xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + rel + "</Relationships>"
    files[rels_path] = xml.encode("utf-8")

    # fit into the cells, keeping the aspect ratio
    first, last = (cells.split(":") + [cells])[:2]
    box_w, box_h = _range_size(sheet_xml, first, last)
    img_w, img_h = _image_size(image_path)
    # scale the height only, the width stays within the cells (page border)
    fit = min(box_w / img_w, box_h * scale / img_h)
    cx, cy = int(img_w * fit), int(img_h * fit)
    col, row = _split_ref(first)

    # center vertically on the cells, a bigger image starts in a row above
    row -= 1
    row_off = (box_h - cy) // 2
    while row_off < 0 and row > 0:
        row -= 1
        row_off += _range_size(sheet_xml, "A%d" % (row + 1), "A%d" % (row + 1))[1]
    row_off = int(max(row_off, 0))

    anchor = ('<xdr:oneCellAnchor><xdr:from><xdr:col>%d</xdr:col><xdr:colOff>0</xdr:colOff><xdr:row>%d</xdr:row><xdr:rowOff>%d</xdr:rowOff></xdr:from>'
              '<xdr:ext cx="%d" cy="%d"/>'
              '<xdr:pic><xdr:nvPicPr><xdr:cNvPr id="%d" name="GnuSolar Image %d"/><xdr:cNvPicPr><a:picLocks noChangeAspect="1"/></xdr:cNvPicPr></xdr:nvPicPr>'
              '<xdr:blipFill><a:blip xmlns:r="%s" r:embed="%s"/><a:stretch><a:fillRect/></a:stretch></xdr:blipFill>'
              '<xdr:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="%d" cy="%d"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></xdr:spPr></xdr:pic>'
              '<xdr:clientData/></xdr:oneCellAnchor>') % (
              _col_index(col) - 1, row, row_off, cx, cy, 10000 + nr, nr, NS_REL, rid, cx, cy)
    xml = files[drawing].decode("utf-8").replace("</xdr:wsDr>", anchor + "</xdr:wsDr>")
    files[drawing] = xml.encode("utf-8")


def single_form_fill(in_file, data, out_file, sheet=None, images={}):
    zin = zipfile.ZipFile(in_file)
    infos = zin.infolist()
    files = {i.filename: zin.read(i.filename) for i in infos}
    zin.close()

    # remove all values which are None
    data = {k: v for k, v in data.items() if v is not None and k}

    sheet_path = _sheet_path(files, sheet)
    xml = files[sheet_path].decode("utf-8")
    boxes, vml = _checkboxes(files, sheet_path, xml)

    linked = []
    for ref, value in data.items():
        if isinstance(value, bool) and ref in boxes:
            shape_id, ctrl = boxes[ref]
            _set_checkbox(files, ctrl, vml, shape_id, value, linked)
        else:
            xml = _set_cell(xml, ref, value)
    xml = _update_formula_cache(xml, data)

    for nr, (cells, image) in enumerate(images.items()):
        image_path, scale = image if isinstance(image, tuple) else (image, 1.0)
        _add_image(files, sheet_path, xml, cells, image_path, nr + 1, scale)
    files[sheet_path] = xml.encode("utf-8")

    # cells linked to check boxes
    for sheet_name, ref, checked in linked:
        path = _sheet_path(files, sheet_name)
        files[path] = _set_cell(files[path].decode("utf-8"), ref, checked).encode("utf-8")

    # let Excel / LibreOffice recalculate the formulas
    workbook = files["xl/workbook.xml"].decode("utf-8")
    workbook = re.sub(r'<calcPr([^>]*?)\s*/>', lambda m: '<calcPr%s fullCalcOnLoad="1"/>' % re.sub(r' fullCalcOnLoad="[^"]*"', '', m.group(1)), workbook)
    files["xl/workbook.xml"] = workbook.encode("utf-8")

    zout = zipfile.ZipFile(out_file, "w", zipfile.ZIP_DEFLATED)
    written = set()
    for info in infos:
        zout.writestr(info, files[info.filename])
        written.add(info.filename)
    for name, content in files.items():
        if name not in written:
            zout.writestr(name, content)
    zout.close()
