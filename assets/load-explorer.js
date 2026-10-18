'use strict';
(() => {
  const button=document.getElementById('load-interactive');
  if(!button)return;
  const status=document.getElementById('interactive-status');
  const panel=document.getElementById('interactive-panel');
  const preview=document.getElementById('preview-stage');
  function script(src){return new Promise((resolve,reject)=>{const s=document.createElement('script');s.src=src;s.onload=resolve;s.onerror=()=>reject(new Error('Could not load '+src));document.head.append(s);});}
  button.addEventListener('click',async()=>{
    button.disabled=true;status.textContent='Loading the interactive graph…';
    try{
      const prefix=button.dataset.prefix;
      await script(prefix+'vendor/plotly-3.1.0.min.js');
      await script(prefix+'assets/explorer-data.js');
      panel.hidden=false;
      await script(prefix+'assets/explorer.js');
      await window.researchFunctions.render();
      preview.hidden=true;status.textContent='Graph ready. Use the controls below, or hover and drag the plot.';
      if(window.Plotly){Plotly.Plots.resize('plot3d');Plotly.Plots.resize('plot2d');}
    }catch(e){panel.hidden=true;status.textContent='The interactive graph could not load. The static preview and research paper remain available.';console.error(e);}
  });
})();
