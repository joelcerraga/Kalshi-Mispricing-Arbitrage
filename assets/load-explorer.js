'use strict';
(() => {
  const button=document.getElementById('load-interactive');
  if(!button)return;
  const status=document.getElementById('interactive-status');
  const panel=document.getElementById('interactive-panel');
  const preview=document.getElementById('preview-stage');
  function supportsWebGL(){
    try{
      const canvas=document.createElement('canvas');
      const gl=canvas.getContext('webgl2')||canvas.getContext('webgl');
      if(!gl)return false;
      const release=gl.getExtension('WEBGL_lose_context');
      if(release)release.loseContext();
      return true;
    }catch{return false;}
  }
  function script(src){return new Promise((resolve,reject)=>{const s=document.createElement('script');s.src=src;s.onload=resolve;s.onerror=()=>reject(new Error('Could not load '+src));document.head.append(s);});}
  button.addEventListener('click',async()=>{
    button.disabled=true;status.textContent='Loading the interactive graph…';
    try{
      const prefix=button.dataset.prefix;
      await script(prefix+'vendor/plotly-3.1.0.min.js');
      await script(prefix+'assets/explorer-data.js');
      window.researchWebGLAvailable=supportsWebGL();
      panel.hidden=false;
      await script(prefix+'assets/explorer.js?v=20261018.2');
      await window.researchFunctions.render();
      preview.hidden=true;
      status.textContent=window.researchWebGLAvailable
        ?'Graph ready. Use the controls below, or hover and drag the plot.'
        :'Interactive 2D view ready. This browser does not support WebGL, so the 3D panel shows a labelled static reference. Controls and CSV export remain available.';
      if(window.Plotly){if(window.researchWebGLAvailable)Plotly.Plots.resize('plot3d');Plotly.Plots.resize('plot2d');}
    }catch(e){panel.hidden=true;status.textContent='The interactive graph could not load. The static preview and research paper remain available.';console.error(e);}
  });
})();
