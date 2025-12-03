let uselog = false;
let showruler = true;   
     
let showLITband = true;

function hasFrozenDescendant(node) {
  return node.descendants().some(d => d.data && d.data.frozen);
}function restoreXvYvFromBackup() {
  if (!window.treeData) return;
  const nodes = treeData.descendants();
  nodes.forEach(n => {
    if (n.data._xv0 !== undefined) n.data.xv = n.data._xv0;
    if (n.data._yv0 !== undefined) n.data.yv = n.data._yv0;
  });
  refreshlayout();
  reflowx_log();
}
function precollapseabovethreshold(treeData, threshold) {
  if (!treeData) return;

  collapsedbands.length = 0;
  treeData.descendants().forEach(n => {
    n._collapsedV = false;
    n._hiddenV = false;
  });

  const nodes = treeData.descendants();
  const numeric = nodes.filter(n => Number.isFinite(+n.data.fusepoint));
  if (!numeric.length) return;

  const t = +threshold;
  if (!Number.isFinite(t)) return;

  // 🔹 identical to precollapseatthreshold, but flip the direction
  numeric.forEach(n => {
    const f = +n.data.fusepoint;
    if (f > t) n.data.xv = t;        // flatten nodes ABOVE threshold
  });

  // --- everything below here is literally copied from your working collapse-at-threshold ---
  const fuseVals = numeric.map(n => +n.data.fusepoint).filter(Number.isFinite);
  const minFuse = d3.min(fuseVals);
  const maxFuse = d3.max(fuseVals);
  if (!Number.isFinite(minFuse) || !Number.isFinite(maxFuse) || minFuse === maxFuse) return;

  const scale = d3.scaleLinear()
    .domain([minFuse, maxFuse])
    .range([0, height - margin.top - margin.bottom]);

  numeric.forEach(n => {
    const f = +n.data.xv;
    n.data.xv = scale(f);
  });

  nodes.forEach(n => {
    if (!Number.isFinite(+n.data.xv)) n.data.xv = 0;
    if (!Number.isFinite(+n.data.yv)) n.data.yv = +n.data.yv || 0;
  });

  refreshlayout();
  reflowx_log();
}

function refreshlayout(){collapsedbands.length=0;
  	treeData.descendants().forEach(n=>{n._hiddenV=false;});
  	treeData.descendants().forEach(n=>{if (n._collapsedV&&!hascollapsedancestor(n)){const {min,max}=subtreeYVrange(n);
     	collapsedbands.push({min,max,squash:0});
     	sethiddendescendants(n,true);}});
 	ymap=makeYMap(1.9);
	treeData.descendants().forEach(n=>{n.x=ymap(+n.data.yv||0);});

	svg.selectAll("g.node")
	    .transition().duration(350)
	    .attr("transform",n=>`translate(${n.y},${n.x})`)
	    .style("display",n=>n._hiddenV?"none":null);

	svg.selectAll("path.link")
	    .transition().duration(350)
	    .attr("d",elbow)
	    .style("display",l=>ishiddenlink(l)?"none":null);

	const visiblenodes=treeData.descendants().filter(n=>!n._hiddenV);
	const visiblemaxx=d3.max(visiblenodes,d=>d.x)||0;
	const newHeight=Math.ceil(visiblemaxx+100+margin.top+margin.bottom);
	d3.select("#graphSvg").attr("height",newHeight);
	svg.attr("height",newHeight-margin.top-margin.bottom);
	svg.selectAll("g.node").select("text.collapse-label").remove();

	svg.selectAll("g.node")
		.filter(d=>d._collapsedV&&!d.data.terminal)
		.append("text")
		.attr("class","collapse-label")
		.attr("dy",4)
		.attr("x",8)
		.style("font-size","11px")
		.style("fill","#555")
		.text(d=>{const nTips=d.descendants().filter(x=>x.data.terminal).length;
	  		return `${nTips} terminals collapsed`;});
}

function reflowx_log() {if (!treeData) return; 
	const containerelement=document.querySelector(".dendrogram-container");
	const newW=containerelement?containerelement.clientWidth:window.innerWidth;
	d3.select("#graphSvg").attr("width",newW);
	const nodesarray=treeData.descendants();
	const maxXV=d3.max(nodesarray,d=>+d.data.xv||0)||1;
	const LEFT_PAD = margin.left + 30;
	const reservenow = reservepixelforlabels(); 
	const textZone = reservepixelforlabels();  
const containerWidth = containerelement ? containerelement.clientWidth : window.innerWidth;
const RIGHT_EDGE = containerWidth - margin.right - textZone;

const usablewidth = Math.max(200, RIGHT_EDGE - LEFT_PAD);

const xlinear = v => LEFT_PAD + (v / maxXV) * usablewidth;

	const xlogR2L=v=>{const t=Math.max(0,maxXV - v); 
	const s=Math.log1p(t)/Math.log1p(maxXV);
	return RIGHT_EDGE-s*usablewidth;};
	xmap=uselog?xlogR2L:xlinear;
	nodesarray.forEach(d=>{ d.y=xmap(+d.data.xv||0); });
	svg.selectAll("g.node").transition().duration(350)
		.attr("transform",d=>`translate(${d.y},${d.x})`);
	svg.selectAll("path.link").transition().duration(350)
		.attr("d",elbow);
	drawrulergrid(maxXV,LEFT_PAD,usablewidth);
}


function drawrulergrid() {if (!xmap||!rulerhost||!rulerSVG||!rulerg|| !gridg) return;
	const innerheight =((+d3.select("#graphSvg").attr("height"))||height) - margin.top - margin.bottom;
	rulerhost.style.display=showruler?"":"none";
	gridg.style("display",showruler?null:"none");
	if (!showruler) { gridg.selectAll("rect.lit-zone").remove(); return; }
	const nodes=treeData.descendants();
	const fvals=nodes.map(d=>+d.data.fusepoint).filter(Number.isFinite);
	if (!fvals.length) return;
	const fusemin=d3.min(fvals);
	const fusemax=d3.max(fvals);
	const pairs=[];
	const byf=d3.group(nodes,d=>+d.data.fusepoint);
	for (const [fraw,group] of byf) {if (!Number.isFinite(fraw)) continue;
		const meanXV=d3.mean(group,d=>+d.data.xv||0);
		if (!Number.isFinite(meanXV)) continue;
			pairs.push({ f: +fraw,px: xmap(meanXV) });}
	pairs.sort((a,b)=>a.f-b.f); 
	if (pairs.length<2) return;
	const scalefusepoint=d3.scaleLinear()
		.domain(pairs.map(p=>p.f))
		.range(pairs.map(p=>p.px))
		.clamp(true);
	const fusetopixel=f=>scalefusepoint(+f);
	const cw =document.getElementById("graphSvg")?.ownerSVGElement?.clientWidth ||document.querySelector(".dendrogram-container")?.clientWidth||window.innerWidth||1200;
	rulerSVG.attr("width",cw);
	rulerg.attr("transform","translate("+margin.left+",0)");
	const ticks=d3.range(Math.floor(fusemin),Math.ceil(fusemax)+1,1);
	const fmt=d3.format(".2f");
	const xL=fusetopixel(fusemin),xR=fusetopixel(fusemax);
	const baseline=rulerg.selectAll("line.ruler-base").data([0]);
	baseline.join(enter=>enter.append("line").attr("class","ruler-base")).attr("x1",xL).attr("x2",xR).attr("y1",0).attr("y2",0).attr("stroke","#666");
	const tSel=rulerg.selectAll("g.ruler-tick").data(ticks,d=>d);
	const tEnter=tSel.enter().append("g").attr("class","ruler-tick");
	tEnter.append("line").attr("y1",0).attr("y2",6).attr("stroke","#666");
	tEnter.append("text").attr("y",18).attr("text-anchor","middle");
	tSel.merge(tEnter)
		.attr("transform",d=>`translate(${fusetopixel(d)},0)`)
		.select("text").text(d=>fmt(d));
	tSel.exit().remove();
	const gridselection=gridg.selectAll("line.vgrid").data(ticks,d=>d);
	gridselection.enter().append("line").attr("class","vgrid").merge(gridselection)
		.attr("x1",d=>fusetopixel(d))
		.attr("x2",d=>fusetopixel(d))
		.attr("y1",0)
		.attr("y2",innerheight);
	gridselection.exit().remove();
	gridg.selectAll("rect.lit-zone").remove();
	if (typeof showLITband==="undefined"||showLITband) {const LITminVal=parseFloat(document.getElementById("LITmin").value);
	const LITmaxVal=parseFloat(document.getElementById("LITmax").value);
	const x1=fusetopixel(LITmaxVal);
	const x2=fusetopixel(LITminVal);
	gridg.insert("rect",":first-child")
	  .attr("class","lit-zone")
	  .attr("x",Math.min(x1,x2))
	  .attr("y",0)
	  .attr("width",Math.abs(x2-x1))
	  .attr("height",innerheight)
	  .attr("fill","#d3d3d3")
	  .attr("fill-opacity",0.25);}
	gridg.lower(); 
}

function settogglelabels() {const btnlog=document.getElementById("togglelengthscale");
  const btnruler=document.getElementById("toggleruler");
  const btnLIT=document.getElementById("toggleLITband");
  if (btnlog) btnlog.textContent=uselog?"Log length: ON":"Log length: OFF";
  if (btnruler) btnruler.textContent=showruler?"Ruler: ON":"Ruler: OFF";
  if (btnLIT) btnLIT.textContent=showLITband?"Instability zone: ON":"Instability zone: OFF";
}

function makeYMap(scale=1.9) {const bands=collapsedbands.slice().sort((a,b)=>a.max-b.max);
  return function ymap(rawYV) {let offset=0;
    for (const b of bands) {const height=(b.max-b.min)*scale;
    	const removed=Math.max(0,height-(b.squash??0));
      if (rawYV>b.max) {offset+=removed;
		continue;}
      if (rawYV >= b.min) {return b.min*scale-offset;}}
    return rawYV*scale-offset;};
}


function subtreeYVrange(node){const ys=node.descendants().map(n=>+n.data.yv||0);
  return {min: Math.min(...ys),max: Math.max(...ys)};}

function addband(node){const { min,max }=subtreeYVrange(node);
  collapsedbands.push({ min,max,squash: 0 }); 
 }  

function removeband(node){const {min,max}=subtreeYVrange(node);
  const i=collapsedbands.findIndex(b=>b.min===min&&b.max===max);
  if (i>=0) collapsedbands.splice(i,1);
}

function hascollapsedancestor(n){let p=n.parent;
	while (p){if (p._collapsedV) return true;
    	p=p.parent;}
	return false;
}


function precollapseatthreshold(treeData, threshold) {
  if (!treeData) return;
  collapsedbands.length = 0;
  treeData.descendants().forEach(n => {
    n._collapsedV = false;
    n._hiddenV = false;
  });
  treeData.descendants().forEach(n => {
    if (
      !n.data.terminal &&
      parseFloat(n.data.fusepoint) <= threshold &&
      !n.data.frozen &&
      !hasFrozenDescendant(n)
    ) {
      let ancestorcollapsed = false,
        p = n.parent;
      while (p) {
        if (p._collapsedV) {
          ancestorcollapsed = true;
          break;
        }
        p = p.parent;
      }
      if (!ancestorcollapsed) {
        n._collapsedV = true;
        const { min, max } = subtreeYVrange(n);
        collapsedbands.push({ min, max, squash: 0 });
        sethiddendescendants(n, true); // frozen-safe now
      }
    }
  });

  refreshlayout();
}


function ishiddenlink(l){const src=l.source||l.parent;
	const tgt=l.target||l;
	return (src&&src._hiddenV)||(tgt&&tgt._hiddenV);
}

function expandall() {collapsedbands.length=0;
  treeData.descendants().forEach(n=>{n._collapsedV=false;
  n._hiddenV=false;});
  refreshlayout();
}

function gettopcollapsedancestor(n){let top=null,p=n;
	while (p) {if (p._collapsedV) top=p;
		p=p.parent;}
	return top;
}

function expandentiresubtree(rootnode){rootnode.descendants().forEach(x=>{x._collapsedV=false;
    x._hiddenV=false;});
}

function searchaction(term){
 if(!term)return;
 term=term.trim().toLowerCase();
 let first=null;
 treeData.descendants().forEach(d=>{
  if(!d.data.terminal)return;
  const full=((d.data.fullLabel||(d.data.terminal+" "+(spname[d.data.terminal]||"")))).toLowerCase();
  const species=(spname[d.data.terminal]||"").toLowerCase();
  const hit=full.includes(term)||species.includes(term);
  if(hit){
    if(!first)first=d;
    const top=gettopcollapsedancestor(d);
    if(top)expandentiresubtree(top);
    else{let p=d.parent;while(p){p._collapsedV=false;p._hiddenV=false;p=p.parent;}}
    updateterminaltextColour("search");
  }
 });
 refreshlayout();
 if(first)setTimeout(()=>{
   const host=document.querySelector(".dendrogram-container");
   if(!host)return;
   const x=first.y-host.clientWidth/2,y=first.x-host.clientHeight/2;
   host.scrollTo({left:Math.max(0,x),top:Math.max(0,y),behavior:"smooth"});
 },350);
 else alert("No match found for: "+term);
}



