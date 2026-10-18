"""Check final paper registers, layout, links and frozen research integrity."""
from pathlib import Path
import argparse,hashlib,json,re
import fitz

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
p=argparse.ArgumentParser();p.add_argument('--visual-reviewed',action='store_true');args=p.parse_args()
pdf=HERE/'Kalshi-Mispricing-and-Arbitrage-Final-Paper.pdf'
doc=fitz.open(pdf);reg=json.loads((HERE/'paper-registers.json').read_text())
aux=(HERE/'main.aux').read_text();log=(HERE/'main.log').read_text()
for warning in ['Overfull','undefined','Missing character','LaTeX Font Warning']:assert warning not in log,warning
labels={m.group(1):(m.group(2),m.group(3)) for m in re.finditer(r'\\newlabel\{([^}]+)\}\{\{([^}]+)\}\{([^}]+)\}',aux)}
expected={'fig:':len(reg['figures']),'tab:':len(reg['tables']),'eq:':len(reg['equations']),'code:':len(reg['codes'])}
for prefix,count in expected.items():
    chosen={k:v for k,v in labels.items() if k.startswith(prefix)}
    assert len(chosen)==count,(prefix,len(chosen),count)
    assert sorted(int(v[0]) for v in chosen.values())==list(range(1,count+1))
    for key,(number,page_label) in chosen.items():
        kind={'fig:':'Figure','tab:':'Table','eq:':'Equation','code:':'Code listing'}[prefix]
        found=[i for i,page in enumerate(doc) if page.get_label()==page_label and re.search(rf'{kind}\s+{number}\.',page.get_text())]
        assert len(found)==1,(key,number,page_label,found)
body='\n'.join((HERE/f).read_text() for f in ['abstract.tex','body.tex','appendix.tex'])
assert not re.search(r'\b(user requests?|user instructions?|you requested|you asked|prompted by)\b',body,re.I)
refs=json.loads((HERE/'references.json').read_text())
assert set(re.findall(r'\\src\{([^}]+)\}',body))=={r['id'] for r in refs}
for r in refs:
    if r['id'].startswith('kalshi'):
        year=re.search(r'Kalshi \((2026[a-z])\)',r['harvard']).group(1)
        for display in re.findall(r'\\src\{'+r['id']+r'\}\{([^}]+)\}',body):assert year in display,(r['id'],display,year)
pages=[];centres=[]
for i,page in enumerate(doc):
    assert abs(page.rect.width-595.276)<.1 and abs(page.rect.height-841.89)<.1
    assert not page.rotation
    assert '??' not in page.get_text()
    spans=[]
    for block in page.get_text('dict')['blocks']:
        if 'lines' not in block:continue
        lines=block['lines']
        for line in lines:
            x0,y0,x1,y1=line['bbox'];assert x0>=52 and x1<=543 and y0>=15 and y1<=825,(i+1,line)
            spans.extend(line['spans'])
        first=''.join(s['text'] for s in lines[0]['spans']).strip() if lines else ''
        if re.match(r'^(Figure|Table|Equation|Code listing)\s+\d+\.',first):
            rows=[]
            for line in lines:
                text=''.join(s['text'] for s in line['spans']).strip();box=list(line['bbox'])
                if not text:continue
                if rows and abs(rows[-1][1][3]-box[3])<3:
                    a,b=rows[-1];rows[-1]=(a+' '+text,[min(b[0],box[0]),min(b[1],box[1]),max(b[2],box[2]),max(b[3],box[3])])
                else:rows.append((text,box))
            for text,box in rows:
                if len(text)>25:
                    offset=(box[0]+box[2])/2-page.rect.width/2
                    assert abs(offset)<1.3,(i+1,text,offset)
                    centres.append({'page':i+1,'offset_pt':round(offset,3),'text':text[:70]})
    bodyspans=[s for s in spans if s['bbox'][1]>60 and s['bbox'][3]<790]
    pages.append({'physical_page':i+1,'printed_label':page.get_label(),'words':len(page.get_text().split()),'body_bottom_pt':round(max((s['bbox'][3] for s in bodyspans),default=0),2)})
for path,digest in reg['frozen_files'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
full='\n'.join(page.get_text() for page in doc)
for value in ['56,006','1,620','0.718589','0.408273','1.034401','5.307','0.0355','3,000']:
    assert value in full,value
report={'status':'passed','pages':len(doc),'a4_portrait_pages':len(doc),'numbered_exhibits':expected,'references':len(refs),'all_register_page_targets_verified':True,'no_overfull_boxes_or_undefined_references':True,'text_inside_page_margins':True,'frozen_files_unchanged':len(reg['frozen_files']),'caption_line_centre_offsets_pt':centres,'pages_audit':pages,'visual_review_completed':args.visual_reviewed,'pdf_sha256':hashlib.sha256(pdf.read_bytes()).hexdigest()}
(HERE/'verification-report.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ['caption_line_centre_offsets_pt','pages_audit']},indent=2))
print('Caption maximum centre offset:',max(abs(x['offset_pt']) for x in centres),'pt')
