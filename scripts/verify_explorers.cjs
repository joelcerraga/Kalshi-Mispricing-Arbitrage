'use strict';
// Document/plot stubs verify graph logic and control transitions, not rendering.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
class Element{
  constructor(id=''){this.id=id;this.value=({temperature:'1',discount:'.1',legs:'6'})[id]||'';this.children=[];this.hidden=false;this.dataset={};this.classList={toggle(){}};this._text='';}
  set textContent(x){this._text=String(x);}get textContent(){return this._text+this.children.map(c=>c.textContent).join(' ');}
  replaceChildren(...xs){this.children=xs;if((this.id==='ticker'||this.id==='event')&&xs.length)this.value=xs[0].value;}
  append(...xs){this.children.push(...xs);}click(){}
}
async function main(){
  const elements=new Map();const el=id=>{if(!elements.has(id))elements.set(id,new Element(id));return elements.get(id);};
  const checks=[];const check=(name,ok)=>{assert.ok(ok,name);checks.push({name,passed:true});};
  const sandbox={console,Promise,Math,Number,String,Date,Array,Object,Blob,URL,setTimeout:()=>0,document:{body:{dataset:{explorer:'book'}},getElementById:el,createElement:()=>new Element(),querySelectorAll:()=>[]},Plotly:{react:async(id,data,layout)=>{el(id).data=data;el(id).layout=layout;}}};
  sandbox.window=sandbox;vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(path.join(root,'assets/explorer-data.js'),'utf8'),sandbox);
  vm.runInContext(fs.readFileSync(path.join(root,'assets/explorer.js'),'utf8'),sandbox);
  const f=sandbox.researchFunctions;await f.render();
  check('Twenty depth traces',el('plot3d').data.length===20);
  check('Depth axis title',el('plot3d').layout.scene.zaxis.title.text==='Cumulative contracts');
  check('Default summary finite',!el('stats').textContent.includes('Infinity'));
  const oneSided=sandbox.RESEARCH_DATA.books.at(-1).orderbooks.find(o=>!o.orderbook_fp.yes_dollars.length||!o.orderbook_fp.no_dollars.length);
  el('ticker').value=oneSided.ticker;await f.render();check('One-sided spread unavailable',el('stats').textContent.includes('Unavailable'));
  check('Book mode visible selector',!el('ticker-control').hidden&&el('event-control').hidden);
  await f.changeMode('probability');
  check('Probability mode controls',el('ticker-control').hidden&&!el('event-control').hidden&&!el('temperature-control').hidden);
  check('Probability surface',el('plot3d').data[0].type==='surface');
  check('Probability rows normalised',el('plot3d').data[0].z.every(row=>Math.abs(row.reduce((a,b)=>a+b,0)-1)<1e-10));
  for(const t of [.25,1,4]){el('temperature').value=String(t);await f.render();check('Slider temperature '+t,el('temperature-value').textContent===t.toFixed(2));}
  const p=[.1,.2,.7];check('Identity calibration',f.calibrated(p,1).every((v,i)=>Math.abs(v-p[i])<1e-12));
  check('Low temperature concentrates',f.calibrated(p,.5)[2]>.7);
  check('High temperature flattens',f.calibrated(p,4)[2]<.7);
  el('reset').onclick();await f.render();check('Calibration reset',el('temperature').value==='1');
  await f.changeMode('laboratory');check('Synthetic mode controls',!el('discount-control').hidden&&!el('legs-control').hidden&&el('event-control').hidden);
  check('Loss surface bounded',el('plot3d').data[0].z.every(row=>row.every(x=>x>=-1e-12&&x<=1+1e-12)));
  const full=f.lab(.1,1,6);check('Full basket cost',Math.abs(full.cost-.95355)<1e-12);check('Full basket expected payoff',Math.abs(full.expected-.04645)<1e-12);check('Full discounted basket no loss',full.loss===0);
  check('No discount loses fees on full fill',Math.abs(f.lab(0,1,6).loss-1)<1e-12);
  const empty=f.lab(.1,0,6);check('No fills means zero payout and loss',empty.loss===0&&empty.expected===0&&empty.allFilled===0);
  check('Independent full-fill probability',Math.abs(f.lab(.1,.9,6).allFilled-.9**6)<1e-12);
  el('legs').value='8';el('discount').value='.05';await f.render();check('Eight-leg redraw',el('plot2d').layout.title.text.startsWith('8 equal-price legs'));
  el('reset').onclick();await f.render();check('Laboratory reset',el('legs').value==='6'&&el('discount').value==='.1');
  check('Depth sweep arithmetic',Math.abs(f.cost([[.4,2],[.5,8]],5).vwap-.46)<1e-12);
  check('Insufficient depth rejected',f.cost([[.4,2]],3)===null);
  check('Ready state after transitions',sandbox.researchReady===true);
  sandbox.researchWebGLAvailable=false;
  await f.render();
  check('WebGL fallback explicitly labelled',el('plot3d').textContent.includes('Static reference'));
  check('WebGL fallback preserves interactive 2D',el('plot2d').layout.title.text.startsWith('6 equal-price legs'));
  el('legs').value='3';await f.render();
  check('WebGL fallback responds to controls',el('plot2d').layout.title.text.startsWith('3 equal-price legs'));
  await f.changeMode('book');check('WebGL fallback changes reference by mode',el('plot3d').children[0].src.endsWith('liquidity.svg'));
  const report={status:'passed',checks:checks.length,method:'Node.js document/plot stubs; no real-browser rendering',results:checks};
  fs.writeFileSync(path.join(root,'outputs/validation/explorer-logic-checks.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({status:report.status,checks:report.checks,method:report.method},null,2));
}
main().catch(e=>{console.error(e);process.exitCode=1;});
