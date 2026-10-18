"""Notebook output adapters for ordinary Jupyter and the dependency-light runner."""
from pathlib import Path
import base64,json,html
from .client import ROOT
_SINK=None

def set_sink(fn):
 global _SINK;_SINK=fn

def emit(bundle):
 if _SINK is not None:_SINK(bundle)
 else:
  from IPython.display import display
  display(bundle,raw=True)

def show_table(df,caption):
 emit({'text/html':'<div class="table-wrap">'+df.to_html(index=False,border=0,float_format=lambda x:f'{x:.5f}')+'</div><p class="caption" style="text-align:center">'+html.escape(caption)+'</p>','text/plain':df.to_string(index=False)})

def show_figure(number):
 f=json.loads((ROOT/'paper/figures.json').read_text())[number-1]
 emit({'image/png':base64.b64encode((ROOT/f['file']).read_bytes()).decode(),'text/plain':f['caption']})
 emit({'text/html':f'<p class="caption" style="text-align:center">Figure {number}. {html.escape(f["caption"])}</p>'})

def equation(number):
 e=json.loads((ROOT/'paper/equations.json').read_text())[number-1]
 emit({'text/html':'<div class="equation" style="text-align:center">\\['+e['latex']+f'\\tag{{{number}}}'+r'\]'+'</div><p class="caption" style="text-align:center">Equation '+str(number)+'. '+html.escape(e['caption'])+'</p>','text/plain':e['latex']+' ('+str(number)+')'})

def read(name):return json.loads((ROOT/name).read_text())
