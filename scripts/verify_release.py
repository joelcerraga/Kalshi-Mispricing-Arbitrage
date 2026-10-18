"""Check the staged website, scientific payload and frozen implementation."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import hashlib
import json
from PIL import Image
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
BASE='https://joelcerraga.github.io/Kalshi-Mispricing-Arbitrage/'


class Page(HTMLParser):
    def __init__(self,text):
        super().__init__();self.tags=[];self.ids=[];self.title='';self.in_title=False;self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs);self.tags.append((tag,a))
        if a.get('id'):self.ids.append(a['id'])
        if tag=='title':self.in_title=True
    def handle_endtag(self,tag):
        if tag=='title':self.in_title=False
    def handle_data(self,data):
        if self.in_title:self.title+=data


def main():
    paths=[ROOT/'index.html',ROOT/'explorers/index.html',ROOT/'notebooks/index.html']+sorted((ROOT/'explorers').glob('*/index.html'))
    assert len(paths)==6
    parsed={p.resolve():Page(p.read_text()) for p in paths};links=0;titles=[]
    for p,page in parsed.items():
        assert len(page.ids)==len(set(page.ids)),str(p)
        assert 'main' in page.ids
        titles.append(page.title)
        meta={a.get('property') or a.get('name'):a.get('content') for tag,a in page.tags if tag=='meta'}
        rel=p.relative_to(ROOT).as_posix().removesuffix('index.html')
        expected=BASE+rel
        assert meta['og:url']==expected,(p,meta['og:url'],expected)
        canonical=next(a['href'] for tag,a in page.tags if tag=='link' and a.get('rel')=='canonical')
        assert canonical==expected
        assert meta['twitter:card']=='summary_large_image'
        assert meta['og:image']==meta['twitter:image']
        assert (ROOT/meta['og:image'].removeprefix(BASE)).is_file()
        for tag,a in page.tags:
            if tag=='img':assert 'alt' in a,(p,a)
            if tag=='input':assert a.get('id') in page.ids
            for key in ['href','src']:
                link=a.get(key)
                if not link:continue
                u=urlsplit(link)
                if u.scheme or link.startswith('//'):continue
                target=(p.parent/unquote(u.path)).resolve() if u.path else p
                if target.is_dir():target/= 'index.html'
                assert target.exists(),(p,link)
                if u.fragment and target in parsed:assert unquote(u.fragment) in parsed[target].ids,(p,link)
                links+=1
    assert len(titles)==len(set(titles))
    landing=parsed[paths[0].resolve()];gallery=parsed[paths[1].resolve()]
    def og_image(page):return next(a['content'] for tag,a in page.tags if tag=='meta' and a.get('property')=='og:image')
    assert og_image(landing)!=og_image(gallery)
    thumbs=[]
    for p in (ROOT/'assets/thumbnails').glob('*.jpg'):
        raw=p.read_bytes();im=Image.open(p);dimensions=im.size;im.verify();assert dimensions==(1774,887) and len(raw)<500000
        thumbs.append({'file':str(p.relative_to(ROOT)),'bytes':len(raw),'dimensions':list(dimensions)})
    assert len(thumbs)==2
    for p in (ROOT/'assets').rglob('*.svg'):ET.parse(p)
    text=(ROOT/'assets/explorer-data.js').read_text();data=json.loads(text.removeprefix('window.RESEARCH_DATA=').removesuffix(';\n'))
    assert len(data['books'])==20
    assert sum(len(x['orderbooks']) for x in data['books'])==720
    assert len(data['events'])==268
    for e in data['events']:
        assert len(e['p'])==6 and abs(sum(e['p'])-1)<1e-9
        assert all(0<=p<=1 for p in e['p']) and 0<=e['winner']<6
    assert data['model']['chosen_temperature']==1
    frozen=json.loads((ROOT/'protocol/model-freeze.json').read_text())
    for p,h in frozen['implementation_hashes'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
    report=json.loads((ROOT/'paper/final/verification-report.json').read_text())
    pdf=ROOT/'paper/final/Kalshi-Mispricing-and-Arbitrage-Final-Paper.pdf'
    assert hashlib.sha256(pdf.read_bytes()).hexdigest()==report['pdf_sha256']
    assert report['pages']==39
    books=sorted((ROOT/'notebooks').glob('*.ipynb'));assert len(books)==8
    cells=0
    for p in books:
        nb=json.loads(p.read_text());assert nb['nbformat']==4
        for cell in nb['cells']:
            if cell['cell_type']=='code':
                assert cell['execution_count'] is not None
                assert not any(o.get('output_type')=='error' for o in cell.get('outputs',[]));cells+=1
    assert cells==31
    assert not (ROOT/'data/raw').exists() and not (ROOT/'data/processed').exists()
    assert not (ROOT/'private-archive').exists()
    assert not (ROOT/'docs/kalshi-permission-request.txt').exists()
    result={'status':'passed','html_pages':len(paths),'internal_links_checked':links,'distinct_page_titles':True,
            'separate_social_thumbnails':thumbs,'final_paper_pages':39,'final_paper_unchanged':True,
            'notebooks':len(books),'executed_cells':cells,'book_observations':720,'probability_vectors':268,
            'frozen_implementation_hashes_verified':len(frozen['implementation_hashes']),
            'full_source_cache_included':(ROOT/'private-archive/Complete-Research-Snapshot.zip').is_file(),'real_browser_review_completed':False,
            'publication_status':json.loads((ROOT/'docs/release-status.json').read_text())['stage']}
    out=ROOT/'outputs/validation/release-checks.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
