function setupdropdownmenus() {
  const menus=Array.from(document.querySelectorAll('.itx-menu'));
  menus.forEach(menu => {const btn=menu.querySelector('.itx-menu-btn');
    const panel=menu.querySelector('.itx-menu-panel');
    btn.addEventListener('click',e=>{e.stopPropagation();
      menus.forEach(m=>{if(m!==menu) m.classList.remove('open');});
      menu.classList.toggle('open');});
    panel.addEventListener('mousedown',e=>e.stopPropagation());
    panel.addEventListener('click',e=>e.stopPropagation());
    panel.querySelectorAll('select,input,button').forEach(el => {el.addEventListener('change', () => menu.classList.remove('open'));});});
  document.addEventListener('click',()=>menus.forEach(m => m.classList.remove('open')));}


function syncpanelheight(){const bar =document.getElementById('topbar');
  const dendro=document.querySelector('.dendrogram-container');
  if(!bar || !dendro) return;
  const apply=() => dendro.style.setProperty('--panel-height', bar.getBoundingClientRect().height + 'px');
  apply(); window.addEventListener('resize', apply);
  // slight delay to catch font/layout shifts
  setTimeout(apply, 50); setTimeout(apply, 250);
}

function adjusttreeoffset() {const controlpanel = document.querySelector(".control-panel");
  const dendrogramcontainer = document.querySelector(".dendrogram-container");
  if (controlpanel && dendrogramcontainer) {const height = controlpanel.offsetHeight;
    dendrogramcontainer.style.top = height + "px";
    dendrogramcontainer.style.height = `calc(100vh - ${height}px)`;}
}



