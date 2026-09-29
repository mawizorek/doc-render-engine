"""The CSS and JS `tally.py` appends ONCE per page that draws a worksheet.

A module of its own because `assets.py` is at the read ceiling, and because these
two strings are the part of the feature most likely to be edited by hand.

🚫 NO `[type=...]{` WITHOUT A SPACE, NO `](`, NO `!!!` -- this text lands in the
markdown before conversion. ⚠️ `@media` IS SAFE HERE: hook 03 resolved every `@id`
long before 05b runs, the same reason `forms._RESET_CSS` can carry it.

THE BROWSER HALF, IN ONE BREATH: inputs are `[data-k]`, results are
`output[data-expr]` holding POSTFIX tokens compiled at build time (`$slug`, numbers,
`+ - * /`, `neg`). One pass in page order; a result stays BLANK until one of its
`data-deps` inputs has a value, so an untouched sheet reads empty rather than
$0.00 everywhere. A check row shows a tick at zero, otherwise over or short.
Drafts save per page and worksheet in localStorage until Clear.
"""

CSS = (
    "<style>.dr-tally{font-variant-numeric:tabular-nums;margin:1rem 0}"
    ".dr-tally__grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(18rem,1fr));gap:1rem}"
    ".dr-tally__sec{border:1px solid var(--dr-border,var(--md-default-fg-color--lightest));"
    "border-radius:.4rem;padding:.6rem .8rem;margin:0;min-width:0}"
    ".dr-tally__sec legend{font-weight:700;padding:0 .3rem}"
    ".dr-tally__row{display:grid;grid-template-columns:1fr 9rem;gap:.4rem;align-items:center;"
    "padding:.25rem 0;border-bottom:1px dashed var(--dr-border,var(--md-default-fg-color--lightest))}"
    ".dr-tally__row:last-child{border-bottom:0}"
    ".dr-tally__row--priced{grid-template-columns:1fr 4.5rem 5.5rem}"
    ".dr-tally__row--wide{grid-template-columns:1fr}"
    ".dr-tally__row small{opacity:.7;font-weight:400}"
    ".dr-tally__row--calc{font-weight:700;border-top:2px solid var(--md-default-fg-color--light)}"
    ".dr-tally__row--check{font-size:1.15em}"
    ".dr-tally input,.dr-tally select,.dr-tally textarea{font:inherit;width:100%;box-sizing:border-box;"
    "padding:.25rem .4rem;border:1px solid var(--dr-border,var(--md-default-fg-color--lighter));"
    "border-radius:.25rem;background:var(--md-default-bg-color);color:var(--md-default-fg-color)}"
    ".dr-tally input[type=number] {text-align:right}"
    ".dr-tally textarea{min-height:4.5rem;resize:vertical}"
    ".dr-tally output{display:block;text-align:right}"
    ".dr-tally .is-good{color:var(--dr-good,#2e9e5b)}.dr-tally .is-bad{color:var(--dr-bad,#d64545)}"
    ".dr-tally__bar{display:flex;flex-wrap:wrap;gap:.6rem;align-items:center;justify-content:center;margin:1.2rem 0 .3rem}"
    ".dr-tally__bar button{font:inherit;font-weight:700;cursor:pointer;padding:.55rem 1.2rem;border-radius:2rem;"
    "border:0;background:var(--dr-accent,var(--md-accent-fg-color));color:var(--md-accent-bg-color,#fff)}"
    ".dr-tally__bar .dr-tally__clear{background:transparent;color:inherit;"
    "border:1px solid var(--dr-border,var(--md-default-fg-color--lighter))}"
    ".dr-tally__status{text-align:center;font-size:.8em;opacity:.75;margin:0}"
    "@media print{.dr-tally__bar,.dr-tally__status{display:none !important}"
    ".dr-tally__grid{display:block !important}.dr-tally__sec{break-inside:avoid;margin:0 0 .6rem}}"
    "</style>"
)

JS = (
    "<script>(function(){"
    "function num(v){var x=parseFloat(v);return isFinite(x)?x:0;}"
    "function money(x){return(x<0?'-':'')+'$'+Math.abs(x).toFixed(2).replace(/\\B(?=(\\d{3})+(?!\\d))/g,',');}"
    "function run(expr,val){var s=[];expr.split(' ').forEach(function(t){"
    "if(t.charAt(0)==='$'){s.push(val[t.slice(1)]||0);return;}"
    "if(t==='neg'){s.push(-s.pop());return;}"
    "if('+-*/'.indexOf(t)>-1&&t.length===1){var b=s.pop(),a=s.pop();"
    "s.push(t==='+'?a+b:t==='-'?a-b:t==='*'?a*b:a/b);return;}"
    "s.push(parseFloat(t));});return s.pop();}"
    "function fmt(x,f){if(f==='money')return money(x);if(f==='percent')return Math.round(x*100)+'%';"
    "return String(Math.round(x*100)/100);}"
    "function sheet(root){"
    "var key='dr-tally:'+location.pathname+':'+root.getAttribute('data-tally');"
    "var ins=root.querySelectorAll('input[data-k],select[data-k],textarea[data-k]');"
    "var outs=root.querySelectorAll('output[data-expr]');"
    "var form=root.getAttribute('data-form')||'';"
    "function url(){var q=[];ins.forEach(function(el){var raw=el.value;if(raw==='')return;"
    "var kd=el.getAttribute('data-kind');if(kd){var t=new Date(kd==='date'?raw+'T12:00':raw).getTime();"
    "if(!isFinite(t))return;raw=String(t);}"
    "if(el.tagName==='TEXTAREA')raw=raw.replace(/\\r?\\n/g,'\\r\\n');"
    "q.push(encodeURIComponent(el.getAttribute('data-send'))+'='+encodeURIComponent(raw));});"
    "return form+(q.length?(form.indexOf('?')>-1?'&':'?')+q.join('&'):'');}"
    "function calc(){var val={},on={},n=0;"
    "ins.forEach(function(el){var k=el.getAttribute('data-k');if(el.value!==''){on[k]=1;n++;}"
    "val[k]=num(el.value);});"
    "outs.forEach(function(o){var need=o.getAttribute('data-need');"
    "var live=need?need.split(' ').every(function(d){return on[d];})"
    ":(o.getAttribute('data-deps')||'').split(' ').some(function(d){return on[d];});"
    "var x=run(o.getAttribute('data-expr'),val);"
    "var k=o.getAttribute('data-k');if(k){val[k]=isFinite(x)?x:0;if(live)on[k]=1;}"
    "o.className='';if(!live||!isFinite(x)){o.textContent='';return;}"
    "var f=o.getAttribute('data-fmt'),t=fmt(x,f);"
    "if(o.getAttribute('data-check')){var z=Math.abs(x)<0.005;"
    "t=z?'✓':(x>0?'+':'')+t+(x>0?'  over':'  short');o.className=z?'is-good':'is-bad';}"
    "o.textContent=t;});"
    "var st=root.querySelector('.dr-tally__status');"
    "if(st)st.textContent=n+' of '+ins.length+' filled. Saved on this device until you clear it.';"
    "var a=root.querySelector('.dr-tally__open');if(a)a.href=url();"
    "try{var d={};ins.forEach(function(el){d[el.getAttribute('data-k')]=el.value;});"
    "localStorage.setItem(key,JSON.stringify(d));}catch(e){}}"
    "try{var saved=JSON.parse(localStorage.getItem(key)||'null');"
    "if(saved)ins.forEach(function(el){var k=el.getAttribute('data-k');if(saved[k]!=null)el.value=saved[k];});}catch(e){}"
    "root.addEventListener('input',calc);root.addEventListener('change',calc);"
    "root.addEventListener('click',function(e){var b=e.target&&e.target.closest?e.target.closest('button'):null;"
    "if(!b||!root.contains(b))return;"
    "if(b.classList.contains('dr-tally__clear')){if(!confirm('Clear everything on this sheet?'))return;"
    "ins.forEach(function(el){el.value='';});try{localStorage.removeItem(key);}catch(e){}calc();return;}"
    "if(!b.classList.contains('dr-tally__send'))return;calc();var u=url(),base=form.split('?')[0],hit=null;"
    "document.querySelectorAll('.dr-form iframe').forEach(function(f){"
    "if(!hit&&(f.getAttribute('src')||'').split('?')[0]===base)hit=f;});"
    "if(!hit){window.open(u,'_blank','noopener');return;}"
    "var g=hit.cloneNode(false);g.setAttribute('src',u);hit.replaceWith(g);"
    "var det=g.closest('details');if(det)det.open=true;g.scrollIntoView({behavior:'smooth',block:'start'});});"
    "calc();}"
    "document.querySelectorAll('.dr-tally').forEach(sheet);"
    "})();</script>"
)
