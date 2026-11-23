"""Check shipped font binaries, style names, character coverage and vertical bounds."""
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
root=Path(__file__).resolve().parent
for style in ('Regular','Italic'):
 maps=[]
 for ext in ('ttf','otf','woff2'):
  p=root/f'NULLFont-{style}.{ext}'
  with TTFont(p,checkChecksums=2) as font:
   # Force table decoding so checksum and outline errors are not hidden by lazy loading.
   for tag in font.keys():font[tag]
   cmap=font.getBestCmap();maps.append(cmap)
   assert all(code in cmap for code in range(32,127)),p
   assert all(ord(ch) in cmap for ch in '\u00a0¥…Φφ⌀Øø'),p
   assert font['name'].getDebugName(1)=='NULL FONT'
   assert font['name'].getDebugName(2)==style
   assert 'SIL Open Font License, Version 1.1' in font['name'].getDebugName(13)
   assert font['name'].getDebugName(14)=='https://openfontlicense.org'
   assert font['post'].italicAngle==(-12 if style=='Italic' else 0)
   assert 'GPOS' in font
   glyphset=font.getGlyphSet()
   for name in font.getGlyphOrder():
    pen=BoundsPen(glyphset);glyphset[name].draw(pen)
    if pen.bounds:
     x0,y0,x1,y1=pen.bounds
     assert y0>=-font['OS/2'].usWinDescent and y1<=font['OS/2'].usWinAscent,(p,name,pen.bounds)
     assert x1>x0 and y1>y0,(p,name)
   for name,expected in [('N',700),('n',560)]:
    pen=BoundsPen(glyphset);glyphset[name].draw(pen);assert pen.bounds[3]-pen.bounds[1]==expected
   assert len({font['hmtx'].metrics[cmap[ord(str(n))]][0] for n in range(10)})==1,'Digits must be tabular'
  print(p.name,'PASS')
 assert maps[0]==maps[1]==maps[2],'Desktop and web coverage differs'
print('PASS: 6 valid fonts, complete printable ASCII, both styles, small caps, tabular digits, no vertical clipping')

from zipfile import ZipFile
expected={'OFL.txt','README.md','brand-glyphs.json','build.py','glyphs.json',
          'null-font.css','requirements.txt','specimen.html','specimen.pdf',
          'specimen.png','validate.py'}
expected.update(f'NULLFont-{style}.{ext}' for style in ('Regular','Italic') for ext in ('ttf','otf','woff2'))
with ZipFile(root/'NULL-FONT.zip') as archive:
 assert len(archive.namelist())==len(expected)
 assert set(archive.namelist())=={'NULL-FONT/'+name for name in expected}
 for name in expected:
  assert archive.read('NULL-FONT/'+name)==(root/name).read_bytes(), 'Stale ZIP entry: '+name
print('PASS: ZIP matches all 17 distributed files, including OFL and sources')
