"""Build original NULL FONT outlines into desktop and web fonts (no third-party glyphs)."""
from pathlib import Path
import json,math,copy
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.ttLib import TTFont
from fontTools.agl import UV2AGL
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
OUT=Path(__file__).resolve().parent
UPM=1000; SCALE=7; VERSION='0.1.0'
# Reuse the original NULL CITY letter designs exactly, before the wordmark's positioning.
original=json.loads((OUT/'brand-glyphs.json').read_text())
glyphs={k:dict(width=v['width'],contours=[dict(role='outer',points=v['points'])]) for k,v in original.items()}
def shape(ch,width,points,holes=()):
 glyphs[ch]={'width':width,'contours':[{'role':'outer','points':points}]+[{'role':'hole','points':p} for p in holes]}
def rect(x,y,w,h):return [[x,y],[x+w,y],[x+w,y+h],[x,y+h]]
def octagon(x,y,w,h,c=8):return [[x+c,y],[x+w-c,y],[x+w,y+c],[x+w,y+h-c],[x+w-c,y+h],[x+c,y+h],[x,y+h-c],[x,y+c]]
def multi(ch,width,contours):glyphs[ch]={'width':width,'contours':[{'role':role,'points':pts} for role,pts in contours]}
shape('A',76,[[0,100],[0,20],[20,0],[56,0],[76,20],[76,100],[57,100],[57,65],[19,65],[19,100]],[[[19,46],[57,46],[57,26],[50,19],[26,19],[19,26]]])
upper=[[19,19],[49,19],[57,27],[57,37],[49,43],[19,43]]
lower=[[19,57],[49,57],[57,65],[57,73],[49,81],[19,81]]
shape('B',76,[[0,0],[59,0],[76,17],[76,42],[67,50],[76,58],[76,83],[59,100],[0,100]],[upper,lower])
shape('D',76,[[0,0],[56,0],[76,20],[76,80],[56,100],[0,100]],[[[19,19],[47,19],[57,29],[57,71],[47,81],[19,81]]])
shape('E',70,[[0,0],[70,0],[70,19],[19,19],[19,41],[59,41],[59,59],[19,59],[19,81],[70,81],[70,100],[0,100]])
shape('F',70,[[0,0],[70,0],[70,19],[19,19],[19,41],[59,41],[59,60],[19,60],[19,100],[0,100]])
shape('G',76,[[20,0],[76,0],[76,19],[29,19],[19,29],[19,71],[29,81],[57,81],[57,65],[42,65],[42,46],[76,46],[76,80],[56,100],[20,100],[0,80],[0,20]])
shape('H',76,[[0,0],[19,0],[19,40],[57,40],[57,0],[76,0],[76,100],[57,100],[57,59],[19,59],[19,100],[0,100]])
shape('J',76,[[0,0],[76,0],[76,80],[56,100],[20,100],[0,80],[0,64],[19,64],[19,74],[26,81],[50,81],[57,74],[57,19],[0,19]])
shape('K',78,[[0,0],[19,0],[19,40],[50,0],[76,0],[38,49],[78,100],[52,100],[19,61],[19,100],[0,100]])
shape('M',104,[[0,100],[0,0],[22,0],[52,46],[82,0],[104,0],[104,100],[85,100],[85,34],[52,82],[19,34],[19,100]])
shape('O',76,octagon(0,0,76,100,20),[octagon(19,19,38,62,9)])
shape('P',76,[[0,100],[0,0],[56,0],[76,20],[76,43],[56,63],[19,63],[19,100]],[upper])
glyphs['Q']=copy.deepcopy(glyphs['O']);glyphs['Q']['width']=84;glyphs['Q']['contours'].append(dict(role='outer',points=[[40,68],[59,68],[84,106],[65,106]]))
shape('R',81,[[0,100],[0,0],[59,0],[76,17],[76,47],[60,61],[81,100],[58,100],[38,63],[19,63],[19,100]],[upper])
shape('S',76,[[20,0],[76,0],[76,19],[27,19],[19,27],[19,34],[27,42],[56,42],[76,62],[76,80],[56,100],[0,100],[0,81],[49,81],[57,73],[57,66],[49,58],[20,58],[0,38],[0,20]])
shape('V',76,[[0,0],[20,0],[38,74],[56,0],[76,0],[51,100],[25,100]])
shape('W',112,[[0,0],[20,0],[33,72],[48,25],[64,25],[79,72],[92,0],[112,0],[92,100],[70,100],[56,55],[42,100],[20,100]])
shape('X',80,[[0,0],[23,0],[40,30],[57,0],[80,0],[52,50],[80,100],[57,100],[40,70],[23,100],[0,100],[28,50]])
shape('Z',76,[[0,0],[76,0],[76,18],[24,81],[76,81],[76,100],[0,100],[0,82],[52,19],[0,19]])
glyphs['0']=copy.deepcopy(glyphs['O']);glyphs['0']['contours'].append(dict(role='outer',points=[[19,68],[48,19],[57,19],[57,32],[28,81],[19,81]]))
shape('1',76,[[20,0],[57,0],[57,81],[76,81],[76,100],[10,100],[10,81],[38,81],[38,19],[20,19]])
shape('2',76,[[20,0],[56,0],[76,20],[76,39],[27,81],[76,81],[76,100],[0,100],[0,79],[57,31],[57,27],[49,19],[27,19],[19,27],[0,27],[0,20]])
shape('3',76,[[0,0],[56,0],[76,20],[76,40],[66,50],[76,60],[76,80],[56,100],[0,100],[0,81],[49,81],[57,73],[57,65],[49,58],[22,58],[22,42],[49,42],[57,35],[57,27],[49,19],[0,19]])
shape('4',76,[[0,0],[19,0],[19,42],[47,42],[47,0],[66,0],[66,42],[76,42],[76,61],[66,61],[66,100],[47,100],[47,61],[0,61]])
shape('5',76,[[0,0],[76,0],[76,19],[19,19],[19,41],[56,41],[76,61],[76,80],[56,100],[0,100],[0,81],[49,81],[57,73],[57,68],[49,60],[0,60]])
shape('6',76,[[20,0],[76,0],[76,19],[27,19],[19,27],[19,42],[56,42],[76,62],[76,80],[56,100],[20,100],[0,80],[0,20]],[[[19,61],[49,61],[57,69],[57,73],[49,81],[27,81],[19,73]]])
shape('7',76,[[0,0],[76,0],[76,19],[37,100],[15,100],[55,19],[0,19]])
shape('8',76,octagon(0,0,76,100,20),[upper,lower])
glyphs['9']=copy.deepcopy(glyphs['6'])
for co in glyphs['9']['contours']:co['points']=[[76-x,100-y] for x,y in co['points']]
# Basic punctuation is drawn in the same squared, chamfered vocabulary.
shape('.',22,octagon(2,82,18,18,3))
shape(',',28,[[5,82],[24,82],[24,100],[11,116],[0,116],[9,100],[5,100]])
multi(':',26,[('outer',octagon(4,28,18,18,3)),('outer',octagon(4,82,18,18,3))])
glyphs[';']=copy.deepcopy(glyphs[':']);glyphs[';']['contours'][1]['points']=glyphs[',']['contours'][0]['points']
multi('!',30,[('outer',rect(5,0,19,68)),('outer',octagon(5,82,19,18,3))])
shape('?',76,[[0,20],[20,0],[56,0],[76,20],[76,40],[47,63],[47,70],[28,70],[28,54],[57,31],[57,27],[49,19],[27,19],[19,27],[19,32],[0,32]])
glyphs['?']['contours'].append(dict(role='outer',points=octagon(28,82,19,18,3)))
shape('-',54,rect(0,43,54,17));shape('_',76,rect(0,104,76,16))
multi('=',76,[('outer',rect(0,29,76,17)),('outer',rect(0,61,76,17))])
multi('+',76,[('outer',rect(0,41,76,18)),('outer',rect(29,12,18,76))])
shape('/',70,[[0,100],[20,100],[70,0],[50,0]])
shape('\\',70,[[0,0],[20,0],[70,100],[50,100]])
shape('|',22,rect(0,-5,22,115))
shape('(',42,[[24,-5],[42,-5],[19,20],[19,80],[42,105],[24,105],[0,80],[0,20]])
glyphs[')']=copy.deepcopy(glyphs['('])
for co in glyphs[')']['contours']:co['points']=[[42-x,y] for x,y in co['points']]
shape('[',42,[[0,-5],[42,-5],[42,12],[18,12],[18,88],[42,88],[42,105],[0,105]])
glyphs[']']=copy.deepcopy(glyphs['['])
for co in glyphs[']']['contours']:co['points']=[[42-x,y] for x,y in co['points']]
shape('{',48,[[26,-5],[48,-5],[48,12],[34,12],[29,18],[29,36],[18,50],[29,64],[29,82],[34,88],[48,88],[48,105],[26,105],[10,89],[10,69],[0,57],[0,43],[10,31],[10,11]])
glyphs['}']=copy.deepcopy(glyphs['{'])
for co in glyphs['}']['contours']:co['points']=[[48-x,y] for x,y in co['points']]
shape('<',60,[[42,14],[60,14],[24,50],[60,86],[42,86],[0,50]])
glyphs['>']=copy.deepcopy(glyphs['<'])
for co in glyphs['>']['contours']:co['points']=[[60-x,y] for x,y in co['points']]
shape('^',76,[[0,35],[19,35],[38,15],[57,35],[76,35],[46,0],[30,0]])
shape('~',84,[[0,43],[18,29],[33,29],[55,48],[65,48],[84,35],[84,55],[67,69],[52,69],[29,50],[19,50],[0,63]])
shape("'",22,rect(3,0,16,28))
multi('"',48,[('outer',rect(3,0,16,28)),('outer',rect(29,0,16,28))])
shape('`',35,[[0,0],[18,0],[35,24],[17,24]])
multi('#',84,[('outer',[[20,0],[36,0],[24,100],[8,100]]),('outer',[[61,0],[77,0],[65,100],[49,100]]),('outer',rect(0,27,84,17)),('outer',rect(0,61,84,17))])
glyphs['$']=copy.deepcopy(glyphs['S']);glyphs['$']['contours'].append(dict(role='outer',points=rect(30,-9,16,118)))
multi('%',90,[('outer',octagon(0,0,32,35,7)),('hole',rect(11,10,10,15)),('outer',octagon(58,65,32,35,7)),('hole',rect(69,75,10,15)),('outer',[[10,100],[25,100],[80,0],[65,0]])])
shape('&',91,[[18,0],[49,0],[65,16],[65,32],[41,52],[61,74],[70,57],[87,57],[75,88],[91,100],[64,100],[59,95],[47,100],[20,100],[0,80],[0,64],[18,48],[5,33],[5,13]],[[[24,18],[43,18],[47,22],[47,28],[31,40],[23,31],[23,22]],[[23,60],[45,82],[40,83],[27,83],[19,75],[19,67]]])
multi('@',96,[('outer',[[20,0],[76,0],[96,20],[96,65],[80,81],[65,81],[65,64],[73,64],[78,59],[78,28],[68,18],[28,18],[18,28],[18,72],[28,82],[96,82],[96,100],[20,100],[0,80],[0,20]]),('outer',octagon(30,30,35,44,7)),('hole',octagon(41,41,13,22,3))])
star=[]
for i in range(24):
 a=-math.pi/2+i*math.pi/12;r=36 if i%4 in (0,1) else 15
 star.append([36+r*math.cos(a),50+r*math.sin(a)])
shape('*',72,star)
# Lowercase is a true 80% small-cap design, not a missing-glyph fallback.
for ch in 'abcdefghijklmnopqrstuvwxyz':
 glyphs[ch]=copy.deepcopy(glyphs[ch.upper()]);glyphs[ch]['width']*=.8
 for co in glyphs[ch]['contours']:co['points']=[[x*.8,20+y*.8] for x,y in co['points']]
glyphs[' ']={'width':28,'contours':[],'space':True}
shape('°',38,octagon(0,0,34,35,8),[rect(11,10,12,15)])
glyphs['¥']=copy.deepcopy(glyphs['Y'])
for y in (58,79):glyphs['¥']['contours'].append(dict(role='outer',points=rect(8,y,64,10)))
for char,base,scale in [('×','X',.65),('−','-',1),('–','-',1.4),('—','-',2.1)]:
 glyphs[char]=copy.deepcopy(glyphs[base]);glyphs[char]['width']*=scale
 for co in glyphs[char]['contours']:co['points']=[[x*scale,(y-50)*(.65 if char=='×' else 1)+50] for x,y in co['points']]
multi('÷',76,[('outer',rect(0,43,76,15)),('outer',octagon(29,11,18,18,3)),('outer',octagon(29,72,18,18,3))])
multi('…',74,[('outer',octagon(x,82,18,18,3)) for x in (0,28,56)])
shape('•',32,octagon(6,40,20,20,4))
for ch,base in [('‘',"'"),('’',"'"),('“','"'),('”','"')]:glyphs[ch]=copy.deepcopy(glyphs[base])
# Engineering labels used by the controller project: phi and diameter signs.
glyphs['Φ']=copy.deepcopy(glyphs['O']);glyphs['Φ']['contours'].append(dict(role='outer',points=rect(29,-8,18,116)))
glyphs['φ']=copy.deepcopy(glyphs['Φ'])
for co in glyphs['φ']['contours']:co['points']=[[x*.8,20+y*.8] for x,y in co['points']]
glyphs['φ']['width']*=.8
for ch in ('Ø','⌀'):glyphs[ch]=copy.deepcopy(glyphs['0'])
glyphs['ø']=copy.deepcopy(glyphs['Ø']);glyphs['ø']['width']*=.8
for co in glyphs['ø']['contours']:co['points']=[[x*.8,20+y*.8] for x,y in co['points']]
# Original design data is readable and editable without font tooling.
(OUT/'glyphs.json').write_text(json.dumps({'design_height':100,'units_per_em':UPM,'cap_height':700,'small_cap_height':560,'glyphs':glyphs},ensure_ascii=False,indent=2)+'\n')
assert all(chr(i) in glyphs for i in range(32,127))
notdef={'width':76,'contours':[dict(role='outer',points=rect(0,0,76,100)),dict(role='hole',points=rect(16,16,44,68))]}
chars=sorted(glyphs,key=ord)
names={ch:UV2AGL.get(ord(ch),f'uni{ord(ch):04X}') for ch in chars}
order=['.notdef']+[names[ch] for ch in chars]
# Normalize contour winding so counters stay open, including after the Y flip.
def outlines(spec,italic):
 result=[]
 for co in spec['contours']:
  pts=[]
  for x,y in co['points']:
   uy=(100-y)*SCALE
   ux=x*SCALE+5+(math.tan(math.radians(12))*uy if italic else 0)
   pts.append((round(ux),round(uy)))
  area=sum(pts[i][0]*pts[(i+1)%len(pts)][1]-pts[(i+1)%len(pts)][0]*pts[i][1] for i in range(len(pts)))
  if (area<0)!=(co['role']=='outer'):pts.reverse()
  result.append(pts)
 return result
def draw(pen,contours,reverse=False):
 for points in contours:
  if reverse:points=list(reversed(points))
  pen.moveTo(points[0])
  for point in points[1:]:pen.lineTo(point)
  pen.closePath()
features='feature kern {\n'+'\n'.join(f'pos {a} {b} {v};' for a,b,v in [('A','V',-65),('V','A',-65),('A','W',-40),('W','A',-40),('T','A',-45),('T','O',-25),('Y','A',-50),('L','V',-40),('L','T',-25)])+'\n} kern;'
for italic in (False,True):
 style='Italic' if italic else 'Regular';ps=f'NULLFont-{style}'
 specs={'.notdef':notdef,**{names[ch]:glyphs[ch] for ch in chars}}
 paths={name:outlines(spec,italic) for name,spec in specs.items()}
 advances={name:round((spec['width']+(0 if spec.get('space') else 10))*SCALE) for name,spec in specs.items()}
 metrics={name:(advances[name],min((x for contour in paths[name] for x,y in contour),default=0)) for name in order}
 for ext in ('ttf','otf'):
  fb=FontBuilder(UPM,isTTF=ext=='ttf');fb.setupGlyphOrder(order);fb.setupCharacterMap({ord(ch):names[ch] for ch in chars}|{160:'space'})
  if ext=='ttf':
   table={}
   for name in order:
    pen=TTGlyphPen(None);draw(pen,paths[name]);g=pen.glyph()
    if g.numberOfContours>0:g.flags[0]|=0x40
    table[name]=g
   fb.setupGlyf(table)
  else:
   table={}
   for name in order:
    pen=T2CharStringPen(advances[name],None);draw(pen,paths[name],reverse=True);table[name]=pen.getCharString()
   fb.setupCFF(ps,{'FullName':f'NULL FONT {style}','FamilyName':'NULL FONT','Weight':'Regular','version':VERSION,'ItalicAngle':-12 if italic else 0},table,{})
  fb.setupHorizontalMetrics(metrics)
  fb.setupHorizontalHeader(ascent=850,descent=-200,lineGap=100,caretSlopeRise=1000 if italic else 1,caretSlopeRun=213 if italic else 0)
  fb.setupNameTable({'familyName':'NULL FONT','styleName':style,'uniqueFontIdentifier':f'GOROman:{ps}:{VERSION}','fullName':f'NULL FONT {style}','psName':ps,'version':'Version '+VERSION,'copyright':'Copyright 2026 GOROman.','licenseDescription':'This Font Software is licensed under the SIL Open Font License, Version 1.1. See OFL.txt.','licenseInfoURL':'https://openfontlicense.org','manufacturer':'GOROman','designer':'GOROman','description':'Original geometric display lettering derived from the NULL CITY wordmark. Lowercase uses small capitals.'})
  fb.setupOS2(sTypoAscender=850,sTypoDescender=-200,sTypoLineGap=100,usWinAscent=850,usWinDescent=200,sxHeight=560,sCapHeight=700,usWeightClass=400,usWidthClass=5,fsSelection=1 if italic else 64,fsType=0,achVendID='NULL')
  fb.setupPost(italicAngle=-12 if italic else 0);fb.font['head'].macStyle=2 if italic else 0;fb.font['head'].fontRevision=.1
  addOpenTypeFeaturesFromString(fb.font,features)
  fb.font.recalcTimestamp=False;fb.font['head'].created=fb.font['head'].modified=3877545600
  fb.save(OUT/(ps+'.'+ext))
  check=TTFont(OUT/(ps+'.'+ext));assert all(i in check.getBestCmap() for i in range(32,127));assert check['name'].getDebugName(1)=='NULL FONT';check.close()
 web=TTFont(OUT/(ps+'.ttf'),recalcTimestamp=False);web.flavor='woff2';web.save(OUT/(ps+'.woff2'));web.close()
 print(ps, len(order),'glyphs / TTF + OTF + WOFF2')
print('Built 2 styles, 6 font files. Original NULL CITY glyphs retained.')

# Fixed timestamps, ordering and permissions make the distribution reproducible.
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
PACKAGE_FILES = (
 'OFL.txt', 'README.md', 'brand-glyphs.json', 'build.py', 'glyphs.json',
 'null-font.css', 'requirements.txt', 'specimen.html', 'specimen.pdf',
 'specimen.png', 'validate.py',
 *(f'NULLFont-{style}.{ext}' for style in ('Regular','Italic') for ext in ('ttf','otf','woff2')),
)
with ZipFile(OUT/'NULL-FONT.zip','w',compression=ZIP_DEFLATED,compresslevel=9) as archive:
 for filename in sorted(PACKAGE_FILES):
  info=ZipInfo('NULL-FONT/'+filename, date_time=(2026,1,1,0,0,0))
  info.compress_type=ZIP_DEFLATED;info.create_system=3;info.external_attr=0o100644<<16
  archive.writestr(info,(OUT/filename).read_bytes())
print('Built deterministic NULL-FONT.zip including OFL and sources.')
