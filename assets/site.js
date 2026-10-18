"use strict";
document.documentElement.classList.add('js');
const menuButton=document.querySelector('.nav-toggle'),menu=document.querySelector('.nav-links');
if(menuButton&&menu)menuButton.addEventListener('click',()=>{const open=menuButton.getAttribute('aria-expanded')!=='true';menuButton.setAttribute('aria-expanded',String(open));menu.classList.toggle('open',open);});
