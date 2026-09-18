(function(){
  window.__AAG_SCALE15_DRAG_SNAP_PHASE__ = true;
  let active=false, halfGutter=0;
  function isHorizontalGutter(el){
    return !!(el && el.matches && el.matches(".gutter.gutter-horizontal"));
  }
  document.addEventListener("mousedown", function(event){
    if(!isHorizontalGutter(event.target)) return;
    halfGutter=event.target.getBoundingClientRect().width/2;
    active=true;
  }, true);
  window.addEventListener("mouseup", function(){ active=false; }, true);
  window.addEventListener("blur", function(){ active=false; }, true);
  window.addEventListener("mousemove", function(event){
    if(!active) return;
    const predictedLeft=event.clientX-halfGutter;
    const physicalLeft=predictedLeft*window.devicePixelRatio;
    if(Math.abs(physicalLeft-Math.round(physicalLeft))>0.001){
      event.preventDefault();
      event.stopImmediatePropagation();
    }
  }, true);
})();
