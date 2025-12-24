function hasTerminalStatus(d) {
  const ts = d.data && d.data.textstat;
  return ts && ["v", "va", "c", "cnv", "h", "s"].includes(ts);
}

function savepreviousstate(d){
  if(!d||!d.data)return;
  if(!d.data.stateHistory)d.data.stateHistory=[];
  const id=d.data.terminal||d.data.name;
  const csel=d3.select("#circleid"+id+"id");
  const tsel=d.data.terminal?d3.select("#terminaltext"+id+"id"):d3.select("#nodetext-"+d.data.name);
  const snap={
    labelText:!tsel.empty()?tsel.text():"",
    textColor:!tsel.empty()?tsel.style("fill"):"#000000",
    fillColor:!csel.empty()?csel.style("fill"):"#FFFFFF",
    circleStroke:!csel.empty()?csel.style("stroke"):"#ccc",
    textstat:d.data.textstat,
    nodestat:d.data.nodestat,
    spname:d.data.spname,
    sex:d.data.sex,
    isVerified:!!d.data.isVerified,
    isContaminant:!!d.data.isContaminant,
    slideMounted:!!d.data.slideMounted
  };
  if(!d.data.terminal&&typeof svg!=="undefined"){
    const desc=[];(function f(n){desc.push(n);if(n&&n.children)n.children.forEach(f);})(d);
    const linkStyles=[];svg.selectAll("path.link").filter(l=>new Set(desc).has(l.source)).each(function(){const s=d3.select(this);linkStyles.push({id:this.id,stroke:s.style("stroke"),width:s.style("stroke-width"),opacity:s.style("opacity"),dasharray:s.style("stroke-dasharray")});});
    const nodeStyles=[];desc.forEach(n=>{if(n.data&&!n.data.terminal){const nid=n.data.name, s=d3.select("#circleid"+nid+"id");nodeStyles.push({id:"circleid"+nid+"id",fill:s.style("fill"),stroke:s.style("stroke")});}});
    snap.linkStyles=linkStyles;snap.nodeStyles=nodeStyles;
  }
  d.data.stateHistory.push(snap);
}

function undosubtree(i,elm){
  let target=i.data.descendants().find(d=>"circleid"+(d.data.terminal||d.data.name)+"id"===elm);
  if(!target)return;
  if("previousState" in target.data){target.data.nodestat=target.data.previousState;delete target.data.previousState;}
  if(target.data.stateHistory&&target.data.stateHistory.length){
    const last=target.data.stateHistory.pop();
    target.data.spname=last.spname;target.data.textstat=last.textstat;target.data.nodestat=last.nodestat;target.data.sex=last.sex;target.data.isVerified=!!last.isVerified;target.data.isContaminant=!!last.isContaminant;target.data.slideMounted=!!last.slideMounted;
    const ls=d3.select("#nodetext-"+target.data.name);if(!ls.empty())ls.text(last.labelText||"").style("fill",last.textColor||"#000000");
    d3.select("#circleid"+target.data.name+"id").style("fill",last.fillColor||"#FFFFFF").style("stroke",last.circleStroke||"#ccc");
    if(last.linkStyles)last.linkStyles.forEach(s=>{if(!s||!s.id)return;d3.select("#"+s.id).style("stroke",s.stroke).style("stroke-width",s.width).style("opacity",s.opacity).style("stroke-dasharray",s.dasharray).attr("stroke",s.stroke).attr("stroke-width",s.width);});
    if(last.nodeStyles)last.nodeStyles.forEach(ns=>{if(!ns||!ns.id)return;d3.select("#"+ns.id).style("fill",ns.fill).style("stroke",ns.stroke);});
  }
  const desc=[];(function f(n){desc.push(n);if(n&&n.children)n.children.forEach(f);})(target);
  desc.forEach(k=>{
    if(!k||!k.data||!k.data.terminal||!k.data.stateHistory||!k.data.stateHistory.length)return;
    const p=k.data.stateHistory.pop();
    k.data.spname=p.spname;k.data.textstat=p.textstat;k.data.nodestat=p.nodestat;k.data.isVerified=!!p.isVerified;k.data.isContaminant=!!p.isContaminant;k.data.slideMounted=!!p.slideMounted;
    const tid=k.data.terminal, tt=d3.select("#terminaltext"+tid+"id"), cc=d3.select("#circleid"+tid+"id"), tg=d3.select("#termid"+tid+"id");
    const wasHolotype   = p.textstat === "h";
    const wasSlideMount = p.textstat === "s";
    const wasContam     = p.textstat === "c" || p.isContaminant;
    tt.text(p.labelText || tt.text())
      .style("fill", p.textColor || "#000000")
      .style("text-decoration", wasContam ? "line-through" : "none")
      .style("font-weight", (wasHolotype || wasSlideMount) ? "bold" : "normal");
    cc.style("stroke",p.circleStroke||"#ccc").style("fill",p.isContaminant?"#FFFFFF":(p.fillColor||"#FFFFFF"));
    tg.select(".verified-checkmark").remove();tg.select(".contaminant-x").remove();
    if(p.isVerified){tg.append("text").attr("class","verified-checkmark").attr("x",0).attr("y",0).attr("dy","0.35em").attr("text-anchor","middle").text("\u2713").style("fill","green").style("font-size","16px").style("font-weight","bold").style("pointer-events","none");}
    if(p.isContaminant){tg.append("text").attr("class","contaminant-x").attr("x",0).attr("dy","0.35em").attr("text-anchor","middle").text("X").style("fill","red").style("font-size","16px").style("font-weight","bold").style("pointer-events","none");}
  });
}



function undo(d){if(d.data.stateHistory&&d.data.stateHistory.length>0){const prev=d.data.stateHistory.pop();
        d.data.spname=prev.spname;
        d.data.textstat=prev.textstat;
        d.data.sex=prev.sex;
        d.data.slideMounted=prev.slideMounted;
        d.data.isVerified=prev.isVerified;
        d.data.isContaminant=prev.isContaminant;
        spname[d.data.terminal]=prev.spname;
        const label=renderterminallabel(d);
        const terminaltext=d3.select("#terminaltext"+d.data.terminal+"id");
        if (!terminaltext.empty()){terminaltext
                .text(label)
                .style("fill",prev.textColor||"#000000")
                .style("text-decoration","none")
                .style("font-weight","normal");}
        d3.select("#circleid"+d.data.terminal+"id")
            .style("fill",prev.fillColor||"#FFFFFF")
            .style("stroke",prev.circleStroke||"#ccc");
        const terminalnode=d3.select("#termid"+d.data.terminal+"id");
        terminalnode.select(".verified-checkmark").remove();
        terminalnode.select(".contaminant-x").remove();
        terminalnode.select(".slide-marker").remove();
        if (d.data.isVerified){terminalnode.append("text")
                .attr("class","verified-checkmark")
                .attr("x",0)
                .attr("y",0)
                .attr("dy","0.35em")
                .attr("text-anchor","middle")
                .text("\u2713")
                .style("fill","green")
                .style("font-size","16px")
                .style("font-weight","bold")
                .style("pointer-events","none");}
        if (d.data.isContaminant){terminalnode.append("text")
                .attr("class","contaminant-x")
                .attr("x",0)
                .attr("dy","0.35em")
                .attr("text-anchor","middle")
                .text("X")
                .style("fill","red")
                .style("font-size","16px")
                .style("font-weight","bold")
                .style("pointer-events","none");}}
}