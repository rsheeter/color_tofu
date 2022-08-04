from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont, newTable, getTableModule
from fontTools.ttLib.tables._c_m_a_p import cmap_classes
from fontTools.colorLib import builder
from fontTools.ttLib.tables import otTables as ot


def color(hex: str):
  return getTableModule('CPAL').Color.fromHex(hex)

# Make a font that maps all glyphs to test glyph
# Ref https://github.com/fonttools/fonttools/blob/main/Lib/fontTools/fontBuilder.py

def drawTestGlyph(pen):
    pen.moveTo((100, 100))
    pen.lineTo((100, 1000))
    #pen.qCurveTo((200, 900), (400, 900), (500, 1000))
    pen.lineTo((500, 1000))
    pen.lineTo((500, 100))
    pen.closePath()

fb = FontBuilder(1024, isTTF=True)

glyph_order = [".notdef", "the_glyph"]
fb.setupGlyphOrder(glyph_order)
advanceWidths = {n: 600 for n in glyph_order}
familyName = "Not Def"
styleName = "Regular"
version = "0.1"
nameStrings = dict(
    familyName=dict(en=familyName),
    styleName=dict(en=styleName),
    uniqueFontIdentifier="fontBuilder: " + familyName + "." + styleName,
    fullName=familyName + "-" + styleName,
    psName=familyName + "-" + styleName,
    version="Version " + version,
)

pen = TTGlyphPen(None)
drawTestGlyph(pen)
glyphs = {".notdef": TTGlyphPen(None).glyph(), "the_glyph": pen.glyph()}
fb.setupGlyf(glyphs)

metrics = {}
glyphTable = fb.font["glyf"]
for gn, advanceWidth in advanceWidths.items():
    metrics[gn] = (advanceWidth, glyphTable[gn].xMin)

fb.setupHorizontalMetrics(metrics)
fb.setupHorizontalHeader(ascent=824, descent=-200)

# OTS is unhappy if we *only* have format 13
fb.setupCharacterMap({1: "the_glyph"})
#fb.font["cmap"].tables = [t for t in fb.font["cmap"].tables if t.platformID != 3 and t.platEncID != 1]

# format 13: many to one
# https://docs.microsoft.com/en-us/typography/opentype/spec/cmap#format-13-many-to-one-range-mappings
# spec: subtable format 13 should only be used under platform ID 0 and encoding ID 6.
# https://github.com/behdad/tofudetector/blob/master/tofu.ttx uses 3/10 and that seems to work.
cmap_many_to_one = cmap_classes[13](13)
cmap_many_to_one.platformID = 3
cmap_many_to_one.platEncID = 10
cmap_many_to_one.language = 0
cmap_many_to_one.cmap = {cp: "the_glyph" for cp in range(0x10FFFF + 1) if cp > 1}

fb.font["cmap"].tables.append(cmap_many_to_one)

fb.setupNameTable(nameStrings)
fb.setupOS2(sTypoAscender=824, usWinAscent=824, usWinDescent=200)
fb.setupPost(keepGlyphNames=False)

# Colorize the test glyph
cpal = fb.font["CPAL"] = newTable("CPAL")
cpal.version = 0
c1 = 0
c2 = 1
cpal.palettes = [[color('#C90900FF'), color('#ffd700ff')]]
cpal.numPaletteEntries = len(cpal.palettes[0])  # this curiously does not auto-update

colr = fb.font["COLR"] = newTable("COLR")

grad_c1_c2 = {
    "Format": ot.PaintFormat.PaintLinearGradient,
    "ColorLine": {
        "ColorStop": [(0.0, c1), (1.0, c2)],
        "Extend": "reflect",
    },
    "x0": 0,
    "y0": 0,
    "x1": 0,
    "y1": 900,
    "x2": 100,
    "y2": 0,
}


fb.font["COLR"] = builder.buildCOLR({
    "the_glyph": {
      "Format": ot.PaintFormat.PaintGlyph,
      "Paint": grad_c1_c2,
      "Glyph": "the_glyph",
    },
  },
  version=1)

fb.save("notdef.ttf")

