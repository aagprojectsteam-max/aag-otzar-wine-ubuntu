(function(){
  if(window.__AAG_POPUP_FIX_V2__) return;
  window.__AAG_POPUP_FIX_V2__=true;

  let preservedSelection=null;

  function editableTarget(start){
    const e=start && start.closest ? start.closest('input,textarea,[contenteditable="true"]') : null;
    if(!e) return null;
    if((e.tagName==='INPUT'||e.tagName==='TEXTAREA') && (e.disabled||e.type==='password')) return null;
    return e;
  }

  function closeBookMenusOutside(target){
    for(const menu of document.querySelectorAll('.flex-column.menu')){
      const r=menu.getBoundingClientRect();
      if(r.width<=0||r.height<=0||menu.contains(target)) continue;
      const vue=menu.__vue__;
      if(vue && vue.$options && vue.$options.name==='BaseContextMenu'){
        if(typeof vue.closeMenu==='function') vue.closeMenu();
        else if('show' in vue) vue.show=false;
      }
    }
  }

  function selectedText(el){
    if(el.tagName==='INPUT'||el.tagName==='TEXTAREA')
      return el.value.slice(el.selectionStart||0,el.selectionEnd||0);
    const s=window.getSelection();
    return s && el.contains(s.anchorNode) ? s.toString() : '';
  }

  function fireInput(el,inputType,data){
    try{
      el.dispatchEvent(new InputEvent('input',{bubbles:true,inputType:inputType,data:data}));
    }catch(_){
      el.dispatchEvent(new Event('input',{bubbles:true}));
    }
  }

  function replaceSelection(el,text,inputType){
    el.focus({preventScroll:true});
    if(el.tagName==='INPUT'||el.tagName==='TEXTAREA'){
      if(el.readOnly||el.disabled) return false;
      const a=el.selectionStart||0,b=el.selectionEnd||a;
      el.setRangeText(text,a,b,'end');
      fireInput(el,inputType||'insertText',text);
      return true;
    }
    if(!el.isContentEditable) return false;
    const s=window.getSelection();
    if(!s||!s.rangeCount) return false;
    const r=s.getRangeAt(0);r.deleteContents();
    if(text){
      const n=document.createTextNode(text);r.insertNode(n);r.setStartAfter(n);r.collapse(true);
      s.removeAllRanges();s.addRange(r);
    }
    fireInput(el,inputType||'insertText',text);
    return true;
  }

  function selectAll(el){
    el.focus({preventScroll:true});
    if(el.tagName==='INPUT'||el.tagName==='TEXTAREA'){
      el.setSelectionRange(0,el.value.length);return;
    }
    const r=document.createRange();r.selectNodeContents(el);
    const s=window.getSelection();s.removeAllRanges();s.addRange(r);
  }

  function showTextMenu(ev,el){
    document.getElementById('aag-text-context-menu')?.remove();

    const m=document.createElement('div');
    m.id='aag-text-context-menu';
    Object.assign(m.style,{
      position:'fixed',zIndex:'2147483646',minWidth:'128px',
      background:'#fff',border:'1px solid #d6d6d6',borderRadius:'3px',
      boxShadow:'0 4px 14px rgba(0,0,0,.22)',padding:'4px 0',
      fontFamily:'Arial, sans-serif',fontSize:'15px',color:'#222',
      direction:'rtl',textAlign:'right',userSelect:'none'
    });

    const readOnly=!!(el.readOnly||el.disabled);
    const defs=[
      ['העתק','copy',()=>selectedText(el).length>0],
      ['גזור','cut',()=>!readOnly&&selectedText(el).length>0],
      ['הדבק','paste',()=>!readOnly],
      ['בחר הכל','all',()=>true]
    ];

    for(const [label,act,enabled] of defs){
      const item=document.createElement('div');
      item.textContent=label;item.dataset.action=act;
      const ok=enabled();item.dataset.enabled=ok?'1':'0';
      Object.assign(item.style,{
        padding:'7px 18px',cursor:'default',whiteSpace:'nowrap',
        opacity:ok?'1':'.42'
      });
      if(ok){
        item.addEventListener('mouseenter',()=>item.style.background='#eee');
        item.addEventListener('mouseleave',()=>item.style.background='transparent');
      }
      item.addEventListener('mousedown',e=>{e.preventDefault();e.stopPropagation();});
      item.addEventListener('click',async e=>{
        e.preventDefault();e.stopPropagation();
        if(item.dataset.enabled!=='1') return;
        try{
          if(act==='copy'){
            await navigator.clipboard.writeText(selectedText(el));
          }else if(act==='cut'){
            const text=selectedText(el);
            if(text){
              await navigator.clipboard.writeText(text);
              replaceSelection(el,'','deleteByCut');
            }
          }else if(act==='paste'){
            replaceSelection(el,await navigator.clipboard.readText(),'insertFromPaste');
          }else if(act==='all'){
            selectAll(el);
          }
        }catch(err){
          console.error('[AAG_TEXT_MENU]',act,String(err));
        }
        m.remove();
      });
      m.appendChild(item);
    }

    document.body.appendChild(m);
    let x=ev.clientX,y=ev.clientY;
    const r=m.getBoundingClientRect();
    x=Math.max(4,Math.min(x,innerWidth-r.width-4));
    y=Math.max(4,Math.min(y,innerHeight-r.height-4));
    m.style.left=x+'px';m.style.top=y+'px';
  }

  document.addEventListener('mousedown',function(e){
    const edit=editableTarget(e.target);
    if(e.button===2 && edit && (edit.tagName==='INPUT'||edit.tagName==='TEXTAREA')){
      const a=edit.selectionStart||0,b=edit.selectionEnd||0;
      preservedSelection=(b>a)?{el:edit,a:a,b:b}:null;
    }else if(e.button!==2){
      preservedSelection=null;
    }

    const custom=document.getElementById('aag-text-context-menu');
    if(custom && !custom.contains(e.target)) custom.remove();
    closeBookMenusOutside(e.target);
  },true);

  document.addEventListener('contextmenu',function(e){
    const el=editableTarget(e.target);
    if(!el) return;
    e.preventDefault();e.stopImmediatePropagation();

    if(preservedSelection && preservedSelection.el===el && el.setSelectionRange){
      el.setSelectionRange(preservedSelection.a,preservedSelection.b);
    }
    preservedSelection=null;

    closeBookMenusOutside(el);
    showTextMenu(e,el);
  },true);

  document.addEventListener('keydown',function(e){
    if(e.key==='Escape') document.getElementById('aag-text-context-menu')?.remove();
  },true);

  window.addEventListener('blur',function(){
    document.getElementById('aag-text-context-menu')?.remove();
  },true);
})();
