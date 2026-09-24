/* PiTheory site interactions. No dependencies (KaTeX loaded separately). */
(function(){
  "use strict";
  var PT = window.PT || {};
  var $ = function(s,r){return (r||document).querySelector(s)};
  var $$ = function(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s))};
  var store = {
    get:function(k,d){try{var v=localStorage.getItem(k);return v===null?d:JSON.parse(v)}catch(e){return d}},
    set:function(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}
  };
  var progress = store.get("pt_progress",{});   // {questionId: "c" | "w"}
  var saved = store.get("pt_saved",[]);         // [questionId]

  function typeset(el){
    if(window.renderMathInElement){
      window.renderMathInElement(el,{delimiters:[{left:"$$",right:"$$",display:true},{left:"$",right:"$",display:false}],throwOnError:false});
    }
  }
  function toast(msg){
    var t=$(".toast"); if(!t){t=document.createElement("div");t.className="toast";t.setAttribute("role","status");document.body.appendChild(t)}
    t.textContent=msg; t.classList.add("show"); clearTimeout(t._h); t._h=setTimeout(function(){t.classList.remove("show")},2200);
  }
  function track(name,params){ if(typeof window.gtag==="function") window.gtag("event",name,params||{}); }

  /* ---------- Question cards ---------- */
  function setStatus(card){
    var s=$(".q-status",card), r=progress[card.dataset.id];
    if(!s) return;
    s.className="q-status"+(r?" "+r:"");
    s.textContent=r==="c"?"Solved correctly":r==="w"?"Attempted":"";
  }
  function record(card,ok){
    var id=card.dataset.id;
    if(progress[id]!=="c") progress[id]=ok?"c":"w";
    store.set("pt_progress",progress); setStatus(card); updateProgress();
    track("answer",{question_id:id,correct:ok});
  }
  function checkMCQ(card,btn){
    var ans=card.dataset.answer, fb=$(".feedback",card);
    $$(".opt",card).forEach(function(b){
      b.disabled=true;
      if(b.dataset.k===ans) b.classList.add("right");
      else if(b===btn) b.classList.add("wrong");
    });
    var ok=btn.dataset.k===ans;
    fb.className="feedback "+(ok?"ok":"no");
    fb.textContent=ok?"Correct! Check the solution to confirm your method.":"Not quite. The correct option is "+ans+".";
    record(card,ok);
  }
  function checkNum(card){
    var inp=$(".num input",card), fb=$(".feedback",card);
    var v=parseFloat(inp.value), a=parseFloat(card.dataset.answer), tol=parseFloat(card.dataset.tol)||0;
    if(isNaN(v)){fb.className="feedback no";fb.textContent="Enter a number to check.";return}
    var ok=Math.abs(v-a)<=tol+1e-9;
    fb.className="feedback "+(ok?"ok":"no");
    fb.textContent=ok?"Correct! Check the solution to confirm your method.":"Not quite. Try again or open the solution.";
    record(card,ok);
  }
  function toggleSolution(card,btn){
    var box=$(".solution",card);
    box.hidden=!box.hidden;
    btn.querySelector("span").textContent=box.hidden?"Show solution":"Hide solution";
    btn.setAttribute("aria-expanded",String(!box.hidden));
    if(!box.hidden) track("view_solution",{question_id:card.dataset.id});
  }
  function toggleSave(card,btn){
    var id=card.dataset.id, i=saved.indexOf(id);
    if(i>-1){saved.splice(i,1);toast("Removed from saved")}else{saved.push(id);toast("Saved. Find it with the Saved filter.")}
    store.set("pt_saved",saved); paintSave(card);
  }
  function paintSave(card){
    var b=$('[data-act="save"]',card); if(!b) return;
    var on=saved.indexOf(card.dataset.id)>-1;
    b.setAttribute("aria-pressed",String(on)); b.querySelector("span").textContent=on?"Saved":"Save";
  }
  function share(card){
    var text="Try this physics question from PiTheory ("+card.dataset.chapter+"):\n"+card.dataset.plain+"\n\nFull solution: "+card.dataset.url;
    if(navigator.share){navigator.share({title:"PiTheory physics question",text:text}).catch(function(){})}
    else window.open("https://wa.me/?text="+encodeURIComponent(text),"_blank","noopener");
    track("share",{question_id:card.dataset.id});
  }
  function report(card){
    var msg="Hi Sir, I think there may be an error in question "+card.dataset.id+" ("+card.dataset.chapter+").\n"+card.dataset.url+"\n\nWhat I noticed: ";
    window.open("https://wa.me/"+(PT.whatsapp||"")+"?text="+encodeURIComponent(msg),"_blank","noopener");
    track("report_error",{question_id:card.dataset.id});
  }

  document.addEventListener("click",function(e){
    var card=e.target.closest(".q");
    if(card){
      var opt=e.target.closest(".opt");
      if(opt&&!opt.disabled) return checkMCQ(card,opt);
      var act=e.target.closest("[data-act]");
      if(act){
        var a=act.dataset.act;
        if(a==="sol") toggleSolution(card,act);
        else if(a==="check") checkNum(card);
        else if(a==="save") toggleSave(card,act);
        else if(a==="share") share(card);
        else if(a==="report") report(card);
      }
    }
    var yt=e.target.closest(".yt");
    if(yt&&!yt.querySelector("iframe")){
      var f=document.createElement("iframe");
      f.src="https://www.youtube-nocookie.com/embed/"+yt.dataset.id+"?autoplay=1&rel=0";
      f.allow="autoplay; encrypted-media; picture-in-picture"; f.allowFullscreen=true; f.title="PiTheory video";
      yt.appendChild(f);
    }
    var tab=e.target.closest("[data-tab]");
    if(tab){
      $$("[data-tab]").forEach(function(t){t.setAttribute("aria-selected",String(t===tab))});
      $$("[data-panel]").forEach(function(p){p.hidden=p.dataset.panel!==tab.dataset.tab});
    }
  });
  document.addEventListener("keydown",function(e){
    if(e.key==="Enter"&&e.target.matches(".num input")) checkNum(e.target.closest(".q"));
  });

  /* ---------- Progress bars (home chapter grid + chapter header) ---------- */
  function updateProgress(){
    $$("[data-progress]").forEach(function(el){
      var code=el.dataset.progress, total=+el.dataset.total||0, done=0, right=0;
      Object.keys(progress).forEach(function(id){ if(id.indexOf(code+"-")===0){done++; if(progress[id]==="c") right++;} });
      done=Math.min(done,total);
      var bar=$(".bar i",el); if(bar) bar.style.width=(total?Math.round(done*100/total):0)+"%";
      var lbl=$(".plabel",el);
      if(lbl) lbl.textContent=done?(done+" of "+total+" attempted, "+right+" correct"):"Not started yet";
    });
  }

  /* ---------- Chapter page: filters + paging ---------- */
  function initChapter(){
    var list=$("#qlist"); if(!list) return;
    var cards=$$(".q",list), PAGE=15, limit=PAGE, mode="all";
    var diff=$("#fDiff"), more=$("#moreBtn"), count=$("#qcount");
    function match(c){
      var d=c.dataset;
      if(diff&&diff.value&&d.diff!==diff.value) return false;
      if(mode==="all") return true;
      if(mode==="mcq"||mode==="numerical") return d.type===mode;
      if(mode==="top") return d.top==="1";
      if(mode==="pyq") return d.pyq==="1";
      if(mode==="saved") return saved.indexOf(d.id)>-1;
      if(mode==="todo") return !progress[d.id];
      if(mode==="wrong") return progress[d.id]==="w";
      return (d.exams||"").split("|").indexOf(mode)>-1;
    }
    function run(){
      var shown=0, n=0;
      cards.forEach(function(c){
        var ok=match(c); if(ok) n++;
        c.hidden=!(ok&&shown<limit); if(ok&&shown<limit) shown++;
      });
      count.textContent=n+(n===1?" question":" questions");
      more.hidden=shown>=n;
      $("#qempty").hidden=n>0;
    }
    $$("[data-filter]").forEach(function(b){
      b.addEventListener("click",function(){
        mode=b.dataset.filter; limit=PAGE;
        $$("[data-filter]").forEach(function(x){x.setAttribute("aria-pressed",String(x===b))});
        run();
      });
    });
    if(diff) diff.addEventListener("change",function(){limit=PAGE;run()});
    more.addEventListener("click",function(){limit+=PAGE;run()});
    var h=location.hash.slice(1), target=h&&document.getElementById(h);
    if(target&&target.classList.contains("q")){ limit=Math.max(PAGE,cards.indexOf(target)+1); }
    run();
    if(target) target.scrollIntoView();
  }

  /* ---------- All-questions search page ---------- */
  function initBank(){
    var list=$("#rows"); if(!list) return;
    var items=$$("li",list), els={cls:$("#fClass"),chapter:$("#fChapter"),type:$("#fType"),exam:$("#fExam"),diff:$("#fDiff2"),text:$("#fText")};
    var params=new URLSearchParams(location.search);
    if(params.get("s")) els.text.value=params.get("s");
    function run(){
      var t=els.text.value.trim().toLowerCase(), n=0;
      items.forEach(function(li){
        var d=li.dataset;
        var show=(!els.cls.value||d.cls===els.cls.value)&&(!els.chapter.value||d.chapter===els.chapter.value)&&
          (!els.type.value||d.type===els.type.value)&&(!els.exam.value||(d.exams||"").split("|").indexOf(els.exam.value)>-1)&&
          (!els.diff.value||d.diff===els.diff.value)&&(!t||d.text.indexOf(t)>-1);
        li.hidden=!show; if(show) n++;
      });
      $("#count").textContent=n+(n===1?" question":" questions");
      $("#empty").hidden=n>0;
    }
    Object.keys(els).forEach(function(k){els[k].addEventListener(k==="text"?"input":"change",run)});
    run();
  }

  /* ---------- Free demo class form ---------- */
  function initDemo(){
    var form=$("#demoForm"); if(!form) return;
    form.addEventListener("submit",function(e){
      e.preventDefault();
      var name=form.name.value.trim(), phone=form.phone.value.replace(/[^\d+]/g,"");
      var err=$(".err",form), done=$(".done",form);
      if(!name||phone.replace(/\D/g,"").length<8){err.hidden=false;return}
      err.hidden=true;
      var lead={name:name,phone:phone,exam:form.exam.value,cls:form.cls.value,country:form.country.value,page:location.pathname};
      var F=PT.leadForm||{};
      if(F.action){
        var body=new URLSearchParams();
        Object.keys(F.fields||{}).forEach(function(k){ if(F.fields[k]) body.append(F.fields[k],lead[k]||""); });
        fetch(F.action,{method:"POST",mode:"no-cors",body:body}).catch(function(){});
      }
      track("generate_lead",{exam:lead.exam,class:lead.cls});
      var msg="Hi Sir, I'd like to book a free demo class.\nName: "+lead.name+"\nPhone: "+lead.phone+"\nPreparing for: "+lead.exam+"\nClass: "+lead.cls+"\nLocation: "+lead.country;
      done.hidden=false;
      if(PT.whatsapp) window.open("https://wa.me/"+PT.whatsapp+"?text="+encodeURIComponent(msg),"_blank","noopener");
    });
  }

  document.addEventListener("DOMContentLoaded",function(){
    $$(".q").forEach(function(c){setStatus(c);paintSave(c)});
    initChapter();
    typeset(document.body);
    initBank();
    initDemo();
    updateProgress();
  });
})();
