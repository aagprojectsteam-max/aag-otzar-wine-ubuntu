(function () {
  const MARK="AAG_KINETIC_GPU_20260916";

  let active=null;
  let raf=0;
  let momentumScroller=null;
  let touchBookComponent=null;
  let suppressClickUntil=0;

  // V3 keeps the native page surfaces stable through drag, glide and settle.
  function beginBookTouchScroll(scroller) {
    if (window.__AAG_TOUCH_SCROLL_V3__?.begin(scroller)) touchBookComponent=scroller.__vue__;
  }
  function endBookTouchScroll(scroller, immediate=false) {
    const target=scroller || touchBookComponent?.$refs?.scroller;
    window.__AAG_TOUCH_SCROLL_V3__?.end(target, immediate);
    if (touchBookComponent?.$refs?.scroller===target) touchBookComponent=null;
  }
  function applyTouchPosition(st) {
    if (!st.scroller) return;
    const d=window.devicePixelRatio || 1;
    st.scroller.scrollLeft=Math.round(st.targetX*d)/d;
    st.scroller.scrollTop=Math.round(st.targetY*d)/d;
  }
  function cancelMomentum() {
    if (raf)
      cancelAnimationFrame(raf);

    raf=0;

    /*
     * Cancel a compositor-native smooth scroll at its exact current
     * position.  New finger contact or a genuine mouse action must take
     * control immediately.
     */
    if (momentumScroller) {
      const scroller=momentumScroller;
      momentumScroller=null;

      try {
        const x=scroller.scrollLeft;
        const y=scroller.scrollTop;
        scroller.scrollTo({
          left:x,
          top:y,
          behavior:"auto"
        });
      } catch (_) {}

      endBookTouchScroll(scroller, true);
    } else if (touchBookComponent) {
      endBookTouchScroll(null, true);
    }
  }

  function findScroller(el,dx,dy) {
    for (
      let n=el;
      n && n!==document.documentElement;
      n=n.parentElement
    ) {
      let cs;

      try {
        cs=getComputedStyle(n);
      } catch (_) {
        continue;
      }

      const canY =
        n.scrollHeight > n.clientHeight + 2 &&
        (
          cs.overflowY==="auto" ||
          cs.overflowY==="scroll"
        );

      const canX =
        n.scrollWidth > n.clientWidth + 2 &&
        (
          cs.overflowX==="auto" ||
          cs.overflowX==="scroll"
        );

      if (
        (Math.abs(dy)>=Math.abs(dx) && canY) ||
        (Math.abs(dx)>Math.abs(dy) && canX)
      ) {
        return n;
      }
    }

    /*
     * This fallback is intentionally kept from the
     * previously accepted Otzar kinetic implementation.
     */
    return document.scrollingElement;
  }

  function begin(e) {
    /*
     * Physical touchscreen on this Wine/Xwayland path
     * was previously observed by Chromium as "pen".
     *
     * Real mouse input is deliberately left untouched.
     */
    if (
      e.pointerType!=="pen" ||
      e.button!==0
    ) {
      return;
    }

    cancelMomentum();
    if (active) { cancelAnimationFrame(active.moveRaf); endBookTouchScroll(active.scroller,true); active=null; }

    active={
      id:e.pointerId,
      target:e.target,
      scroller:null,

      sx:e.clientX,
      sy:e.clientY,

      lx:e.clientX,
      ly:e.clientY,
      lt:performance.now(),

      vx:0,
      vy:0,
      dragging:false
    };

    try {
      e.target.setPointerCapture(e.pointerId);
    } catch (_) {}
  }

  function move(e) {
    if (
      !active ||
      e.pointerId!==active.id
    ) {
      return;
    }

    const now=performance.now();
    const dt=Math.max(
      1,
      now-active.lt
    );

    const dx=
      e.clientX-active.lx;

    const dy=
      e.clientY-active.ly;

    const tx=
      e.clientX-active.sx;

    const ty=
      e.clientY-active.sy;

    /*
     * Preserve normal taps.
     * Only become a scroll gesture after 7 CSS px.
     */
    if (
      !active.dragging &&
      Math.hypot(tx,ty)>=7
    ) {
      active.scroller=
        findScroller(
          active.target,
          tx,
          ty
        );

      active.dragging=
        !!active.scroller;

      if (active.dragging) {
        active.baseLeft=active.scroller.scrollLeft;
        active.baseTop=active.scroller.scrollTop;
        active.axis=Math.abs(ty)>Math.abs(tx)*1.25 ? "y" : (Math.abs(tx)>Math.abs(ty)*1.25 ? "x" : "both");
        beginBookTouchScroll(active.scroller);
      }
    }

    if (
      active.dragging &&
      active.scroller
    ) {
      // Absolute finger displacement retains subpixel motion instead of rounding
      // away a fraction on every += scrollTop write. Lock the dominant axis.
      active.targetX=active.baseLeft-(active.axis==="y" ? 0 : tx);
      active.targetY=active.baseTop-(active.axis==="x" ? 0 : ty);
      if (!active.moveRaf) {
        const gesture=active;
        active.moveRaf=requestAnimationFrame(function () {
          gesture.moveRaf=0;
          if (active===gesture) applyTouchPosition(gesture);
        });
      }
      const vx=active.axis==="y" ? 0 : -dx/dt;
      const vy=active.axis==="x" ? 0 : -dy/dt;

      /*
       * Time-aware low-pass velocity estimate.  The old fixed 55/45 mix
       * overreacted to uneven Wine/Xwayland pointer packet spacing,
       * especially on the larger fullscreen surface.
       */
      const alpha=
        1-Math.exp(-dt/22);

      active.vx=
        active.vx*(1-alpha) +
        vx*alpha;

      active.vy=
        active.vy*(1-alpha) +
        vy*alpha;

      e.preventDefault();
      e.stopPropagation();
    }

    active.lx=e.clientX;
    active.ly=e.clientY;
    active.lt=now;
  }

  function finish(e) {
    if (
      !active ||
      e.pointerId!==active.id
    ) {
      return;
    }

    const st=active;
    active=null;

    if (st.moveRaf) { cancelAnimationFrame(st.moveRaf); st.moveRaf=0; }
    if (st.dragging && Number.isFinite(st.targetY)) applyTouchPosition(st);
    // A deliberate slow adjustment, held release, or cancellation is not a flick.
    const flick=e.type!=="pointercancel" && performance.now()-st.lt<80 &&
      Math.hypot(st.vx,st.vy)>=0.25 && Math.hypot(st.lx-st.sx,st.ly-st.sy)>=20;
    if (!flick) { st.vx=0; st.vy=0; }

    if (
      !st.dragging ||
      !st.scroller
    ) {
      return;
    }

    /*
     * Prevent accidental click at the end of a swipe.
     */
    suppressClickUntil=
      performance.now()+350;

    /*
     * AAG_TOUCH_INERTIA_V7_LINEAR_DECEL
     *
     * Constant-deceleration inertial glide.
     *
     * Chromium native smooth-scroll still applies a noticeable ease-out
     * brake near the end.  Instead, preserve the measured release
     * velocity and reduce it linearly to zero over a bounded duration.
     * Position follows easeOutQuad, whose derivative is a straight-line
     * velocity ramp to zero: no terminal phase, no threshold and no
     * browser easing curve.
     */
    const vx=Math.max(
      -55,
      Math.min(
        55,
        st.vx*16.67
      )
    );

    const vy=Math.max(
      -55,
      Math.min(
        55,
        st.vy*16.67
      )
    );

    const speed=
      Math.hypot(vx,vy);

    if (speed>=0.7) {
      /*
       * Keep the low-speed tail short enough that we never spend many
       * frames below one visible pixel of motion.
       */
      const duration=
        Math.max(
          150,
          Math.min(
            390,
            125 + speed*4.8
          )
        );

      const frames=
        duration/16.67;

      /*
       * easeOutQuad has initial normalized derivative 2.
       * distance = initialVelocity * totalFrames / 2 therefore keeps
       * release velocity continuous at pointer-up.
       */
      const distanceX=
        vx*frames/2;

      const distanceY=
        vy*frames/2;

      const startLeft=
        st.scroller.scrollLeft;

      const startTop=
        st.scroller.scrollTop;

      const started=
        performance.now();

      momentumScroller=
        st.scroller;

      function frame(now) {
        if (
          momentumScroller!==st.scroller
        ) {
          raf=0;
          return;
        }

        const t=
          Math.min(
            1,
            (now-started)/duration
          );

        const ease=
          t*(2-t);

        st.scroller.scrollLeft=
          startLeft +
          distanceX*ease;

        st.scroller.scrollTop=
          startTop +
          distanceY*ease;

        if (t>=1) {
          momentumScroller=null;
          raf=0;

          endBookTouchScroll(
            st.scroller
          );

          return;
        }

        raf=
          requestAnimationFrame(
            frame
          );
      }

      raf=
        requestAnimationFrame(
          frame
        );
    } else {
      endBookTouchScroll(
        st.scroller
      );
    }

    e.preventDefault();
    e.stopPropagation();
  }

  document.addEventListener(
    "pointerdown",
    begin,
    true
  );

  document.addEventListener(
    "pointermove",
    move,
    true
  );

  document.addEventListener(
    "pointerup",
    finish,
    true
  );

  document.addEventListener(
    "pointercancel",
    finish,
    true
  );

  /*
   * A new ordinary mouse action stops old momentum.
   */
  document.addEventListener(
    "mousedown",
    function () {
      if (!active)
        cancelMomentum();
    },
    true
  );

  document.addEventListener(
    "click",
    function (e) {
      /*
       * AAG_KINETIC_MOMENTUM_FIX_V2
       *
       * Chromium synthesizes a click immediately after a pen/touch
       * pointerup.  The old code cancelled momentum BEFORE checking
       * whether this was the click generated by the swipe itself.
       *
       * That killed inertia on the very first frame.
       */
      if (
        performance.now() <
        suppressClickUntil
      ) {
        e.preventDefault();
        e.stopImmediatePropagation();
        return;
      }

      /*
       * A genuine later click should stop existing momentum.
       */
      cancelMomentum();
    },
    true
  );

  function cancelFromOtherInput() {
    if (active) {
      const st=active; active=null; cancelAnimationFrame(st.moveRaf);
      if (st.dragging && Number.isFinite(st.targetY)) applyTouchPosition(st);
      endBookTouchScroll(st.scroller,true);
    }
    cancelMomentum();
  }
  document.addEventListener("wheel",cancelFromOtherInput,{capture:true,passive:true});
  document.addEventListener("keydown",cancelFromOtherInput,true);
  window.addEventListener("blur",e=>{if(e.target===window)cancelFromOtherInput();},true);
  console.log("[AAG_KINETIC_GPU] READY V3");
})();
