const SPART_BAR_WIDTH=26;
const SPART_BAR_GAP=4;
const SPART_LANE_PAD=10;
function getTerminals(node){descs=[]
  function getChildschildren2(node){
    if(!node.children){descs=descs.concat(node);
    return descs;}
    node.children.forEach(function(d) {getChildschildren2(d);});
    return descs;}
  return getChildschildren2(node);
}

function getDescendants(node) {descs=[node]
  function getChildschildren(node){
    if(!node.children){return [];}
      node.children.forEach(function(d){descs=descs.concat(d); descs.concat(getChildschildren(d));});
      return descs;}
    return getChildschildren(node);
}
function sethiddendescendants(internal, hidden) {internal.descendants().forEach(n => {if (n!==internal) {
      if (n.data && n.data.frozen) return;
      n._hiddenV=hidden;
    }});}

function reservepixelforlabels() {const labelNodes=document.querySelectorAll('text[id^="terminaltext"]');
  let maxWidth=0;
  labelNodes.forEach(el => { const bbox=el.getBBox ? el.getBBox() : null;
    if (bbox && bbox.width > maxWidth) maxWidth=bbox.width;});
  if (maxWidth === 0) {const probe="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    const avg=getTextWidth(probe, "14px sans-serif") / probe.length;
    maxWidth=keepchars() * avg;}
  const fixedBuffer=100;
let spartLane = 0;
if (window.spartActive && window.universalRuns?.length) {
  spartLane = window.spartLanePx || 0;
}
console.log("reserved", spartLane, "spartLanePx", window.spartLanePx);


return maxWidth + fixedBuffer + spartLane;}


function getTextWidth(text,font){var canvas=getTextWidth.canvas||(getTextWidth.canvas=document.createElement("canvas"));
  var context=canvas.getContext("2d");
  context.font=font;
  var metrics=context.measureText(text);
  return metrics.width;
}
function onlyUnique(value, index, array) {return array.indexOf(value) === index;
}

function keepchars(){return Math.max(1, Math.min(100, maxnameLength));
}

function getclustermembership(treeData, clustperc){var clustermembership={};
  treeData.descendants().forEach(function(d){if(d.data.terminal){let currentNode=d;
    let bestParent=null;
    let bestFusepoint=-Infinity; 
    let clustpercnum=parseFloat(clustperc); 
    while (currentNode.parent) {let parentFusepoint=parseFloat(currentNode.parent.data.fusepoint); 
      if (!isNaN(parentFusepoint) && parentFusepoint <= clustpercnum) {
          if (parentFusepoint >= bestFusepoint) {
              bestParent=currentNode.parent;
              bestFusepoint=parentFusepoint;}}
      currentNode=currentNode.parent;}
    clustermembership[d.data.terminal]=bestParent ? bestParent.data.name : d.data.terminal;}});
  const uniqueClusters=[...new Set(Object.values(clustermembership))];
  const clusterRemap={};
  uniqueClusters.forEach((cluster, idx) => {
  clusterRemap[cluster]=idx+1;});
  const remappedMembership={};
  for (const [key, originalCluster] of Object.entries(clustermembership)) {
    remappedMembership[key]=clusterRemap[originalCluster];}
  return remappedMembership;
}

function computeSPARTLaneWidth() {
  if (!window.universalRuns?.length) return 0;

  const maxCol =
    Math.max(...window.universalRuns.map(r => r.col ?? 0));

  const stride = SPART_BAR_WIDTH + SPART_BAR_GAP;

  return Math.ceil(
    SPART_LANE_PAD +
    (maxCol + 1) * stride
  );
}


function getLITclassifications(treeData, LITmin, LITmax,maxPthresh){var LITnodeclassification={};
  var LITterminalselections={};
  LITmin=parseFloat(LITmin);
  LITmax=parseFloat(LITmax);
  var nodes=treeData.descendants();
  var donenodes=[];
  nodes.forEach(d => {if (d.data.terminal) {LITterminalselections[d.data.terminal]=0;}});
  nodes.forEach(d => {let filteredlist=[];
    if (parseFloat(d.data.fusepoint) > LITmin && parseFloat(d.data.fusepoint)<=LITmax) {templist=maxpairs[d.data.name].split(":");
      filteredlist=[safeID[hap[templist[0]]], safeID[hap[templist[1]]]];
      filteredlist.push(safeID[rephaps[d.data.name]]);
      LITnodeclassification[d.data.name]=1;
      for (var i=0; i < filteredlist.length; i++) {LITterminalselections[filteredlist[i]]=1;}
      let childnodes=getDescendants(d);
      childnodes.forEach(k => {if (k != d) {donenodes.push(k);}});}
      else if (maxP[d.data.name] > maxPthresh && parseFloat(d.data.fusepoint) <= LITmax) {templist=maxpairs[d.data.name].split(":");
        filteredlist=[safeID[hap[templist[0]]], safeID[hap[templist[1]]]];
        filteredlist.push(safeID[rephaps[d.data.name]]);
        LITnodeclassification[d.data.name]=1;
        for (var i=0; i < filteredlist.length; i++) {LITterminalselections[filteredlist[i]]=1;}
        let childnodes=getDescendants(d);
        childnodes.forEach(k => {if (k!=d) { donenodes.push(k);}});}});
  nodes.forEach(d => {if (parseFloat(d.data.fusepoint)<=LITmin&&maxP[d.data.name] < maxPthresh) {
    if (!donenodes.includes(d)) {if(maxpairs[d.data.name]!=""){templist=maxpairs[d.data.name].split(":");
      filteredlist=[safeID[hap[templist[0]]], safeID[hap[templist[1]]]];}
    else{filteredlist=[];filteredlist.push(safeID[rephaps[d.data.name]]);}               
    LITnodeclassification[d.data.name]=0;
  for (var i=0; i < filteredlist.length; i++) {LITterminalselections[filteredlist[i]]=1;}
  let childnodes=getDescendants(d);
  childnodes.forEach(k => {if (k != d) {donenodes.push(k);}});}}});
  nodes.forEach(d => {if (!donenodes.includes(d) && d.data.terminal) {LITnodeclassification[d.data.terminal]=0;
  LITterminalselections[d.data.terminal]=1;}});
  return [LITnodeclassification, LITterminalselections];
}

function shortenspecimen(id, keep) {if (!id) return "";
  return id.length > keep ? id.slice(0, keep - 1)+"…" : id;
}


function rgbToHex(rgb) {let rgbValues=rgb.match(/\d+/g); 
  return "#"+rgbValues.map(x => Number(x).toString(16).padStart(2, "0")).join("");
}

function selectelement(id, valueToSelect) {let element=document.getElementById(id);
    element.value=valueToSelect;
}


function loadSPART(event) {const file=event.target.files[0];
  if (!file) return;
  const reader=new FileReader();
  reader.onload=function () {const text=reader.result;
    parseSPART(text);
    window.schemeclusters =buildschemeclusters(window.spartitions);
    const { universalsets, universalsetmembers } =builduniversalsets(window.schemeclusters);
    window.universalsets=universalsets;
    window.universalsetmembers=universalsetmembers;
    window.spartitions_univ =buildspartitionsuniversal(window.spartitions,window.schemeclusters,window.universalsets);
    window.individual_univ_assignments=buildindividualuniversalassignments( window.spartitions_univ);
    const nSchemes=Object.keys(window.spartitions).length;
    window.individual_congruence={};
    for (const ind in window.individual_univ_assignments) {window.individual_congruence[ind]=`${nSchemes - (window.individual_univ_assignments[ind].size - 1)}/${nSchemes}`;}
const { support, nSchemes: nSpartSchemes } =computeuniversalsupport(window.spartitions_univ);
window.universalSupport=support;
window.nSpartSchemes=nSpartSchemes;
window.universalRuns =computeuniversalrunsbygroup(treeData, window.universalsetmembers);
assignruncolumns(window.universalRuns);
window.spartDataLoaded=true;
window.spartActive=true;
updateSPARTButton();
window.spartLanePx = computeSPARTLaneWidth();
reflowx_log(); };
reader.readAsText(file);
}

function updateSPARTButton() {const btn=document.getElementById("toggleSPART");
  if (!btn) return;
  btn.textContent=window.spartActive? "SPART: ON": "SPART: OFF";}

function parseSPART(text) {window.spartitions={};
  const lines=text.split("\n").map(l => l.trim()).filter(l => l && !l.startsWith("["));
  let schemenames=[];
  let inassignment=false;
  for (let line of lines) {const low=line.toLowerCase();
    if (low.startsWith("n_spartitions")) {
      const colon=line.indexOf(":");
      if (colon === -1) continue;
      let schemet=line.slice(colon+1).trim();
      if (schemet.endsWith(";")) {schemet=schemet.slice(0, -1);}
      schemenames=schemet.split("/").map(s => s.trim()).filter(s => s.length > 0);
      schemenames.forEach(name => {window.spartitions[name]={};});
      continue; }
    if (low.startsWith("individual_assignment") ||low.startsWith("individual_assignment")) {inassignment=true;
      continue;}
    if (low.startsWith("end")) {inassignment=false;
      continue;}
    if (inassignment) {const colon=line.indexOf(":");
      if (colon === -1) continue;
      const specimen=line.slice(0, colon).trim();
      const rhs=line.slice(colon+1).trim();
      let valuest=rhs;
      if (valuest.endsWith(";")) {valuest=valuest.slice(0, -1);}
      const values=valuest.split("/").map(v => v.trim());
      for (let i=0; i < values.length && i < schemenames.length; i++) {const v=parseInt(values[i], 10);
        if (!Number.isFinite(v)) continue;
        window.spartitions[schemenames[i]][specimen]=v;}}}}

function buildschemeclusters(spartitions) {const schemeclusters={};
  for (const scheme in spartitions) {
    schemeclusters[scheme]={};
    for (const individual in spartitions[scheme]) {
      const pid=spartitions[scheme][individual];
      if (!schemeclusters[scheme][pid]) {
        schemeclusters[scheme][pid]=new Set();}
      schemeclusters[scheme][pid].add(individual);}}
  return schemeclusters;}

function builduniversalsets(schemeclusters) {const universalsets={}; 
  const universalsetmembers={}; 
  let nextUID=1;
  for (const scheme in schemeclusters) {for (const pid in schemeclusters[scheme]) {
      const members=schemeclusters[scheme][pid];
      const signature=[...members].sort().join("|");
      if (!(signature in universalsets)) {
        const uid=nextUID++;
        universalsets[signature]=uid;
        universalsetmembers[uid]=new Set(members);}}}
  return { universalsets, universalsetmembers };
}

function buildspartitionsuniversal(spartitions, schemeclusters, universalsets) {const spartitions_univ={};
  for (const scheme in spartitions) {spartitions_univ[scheme]={};
    for (const individual in spartitions[scheme]) {
      const pid=spartitions[scheme][individual];
      const members=schemeclusters[scheme][pid];
      const signature=[...members].sort().join("|");
      spartitions_univ[scheme][individual]=universalsets[signature];}}
  return spartitions_univ;
}

function buildindividualuniversalassignments(spartitions_univ) {
  const individual_univ_assignments={};
  for (const scheme in spartitions_univ) {
    for (const individual in spartitions_univ[scheme]) {if (!individual_univ_assignments[individual]) {
        individual_univ_assignments[individual]=new Set();}
      individual_univ_assignments[individual].add(spartitions_univ[scheme][individual]);}}
  return individual_univ_assignments;}

function computeuniversalsupport(spartitions_univ) {const support={};
  const schemes=Object.keys(spartitions_univ);
  const nSchemes=schemes.length;
  schemes.forEach(scheme => {const seen=new Set();
    Object.values(spartitions_univ[scheme]).forEach(uid => {if (!seen.has(uid)) {support[uid]=(support[uid] || 0)+1;
        seen.add(uid);}});});
  return { support, nSchemes };}

function computeuniversalruns(treeData, spartitions_univ) {
  const order=getterminalorder(treeData);
  const scheme=Object.keys(spartitions_univ)[0];
  const runs=[];
  let current=null;
  order.forEach((ind, i) => {const uid=spartitions_univ[scheme][ind.toLowerCase()];
    if (uid === undefined) return;
    if (!current || current.uid!==uid) { current={
        uid,
        start: i,
        end: i,
        members: [ind]};
      runs.push(current);} else {current.end=i;
      current.members.push(ind);}});
  return runs;}

function getterminalorder(treeData) {return treeData
    .leaves()
    .map(n => {const tid=n.data.terminal;
      if (window.terminallabel && window.terminallabel[tid]) {return window.terminallabel[tid];}
      return tid; })
    .filter(Boolean);}

function clearSPART() {window.spartActive=false;
  delete window.spartitions;
  delete window.schemeclusters;
  delete window.universalsets;
  delete window.universalsetmembers;
  delete window.spartitions_univ;
  delete window.individual_univ_assignments;
  delete window.individual_congruence;
  delete window.universalSupport;
  delete window.nSpartSchemes;
  delete window.universalRuns;
  svg.selectAll(".spart-bar-group").remove();
}
function normalizeID(x) {return x.toLowerCase().replace(/-/g, "_");}
function computeuniversalrunsbygroup(treeData, universalsetmembers) {const order=getterminalorder(treeData);
  const runs=[]; 
  for (const [uid, membersSet] of Object.entries(universalsetmembers)) {const members = new Set([...membersSet].map(normalizeID) );

    let current=null;
    order.forEach((label, i) => {const key=normalizeID(label);
      if (members.has(key)) {if (!current){current={uid: Number(uid),start: i,end: i, members: [label]};
          runs.push(current);} else {current.end=i;
          current.members.push(label);}} else {current=null; }}); }
return runs;}

function assignruncolumns(runs) {runs.sort((a, b) => a.start - b.start);
  const active=[];
  runs.forEach(run => {let col=0;
    while ( active.some(r =>r.col === col &&!(run.start > r.end || run.end < r.start))) { col++;}
    run.col=col;
    active.push(run);
    for (let i=active.length - 1; i >= 0; i--) {if (active[i].end < run.start) {active.splice(i, 1);}}});}

(function initsparttooltip(){if (window.showTooltip && window.hideTooltip) return;
  const tip=document.createElement("div");
  tip.id="spartTooltip";
  tip.style.position="fixed";
  tip.style.pointerEvents="none";
  tip.style.zIndex="9999";
  tip.style.padding="6px 8px";
  tip.style.borderRadius="6px";
  tip.style.background="rgba(0,0,0,0.75)";
  tip.style.color="#fff";
  tip.style.fontSize="12px";
  tip.style.display="none";
  document.body.appendChild(tip);
  window.showTooltip=function (html) {tip.innerHTML=html;
    tip.style.display="block";};
  window.hideTooltip=function () {tip.style.display="none";};
window.moveTooltip=function (evt) {
  const tip=document.getElementById("spartTooltip");
  if (!tip || tip.style.display!=="block") return;
  const padding=12;
  const tipRect=tip.getBoundingClientRect();
  const vw=window.innerWidth;
  const vh=window.innerHeight;
  let x=evt.clientX+padding;
  let y=evt.clientY+padding;
  if (x+tipRect.width > vw) {x=evt.clientX - tipRect.width - padding;}
  if (y+tipRect.height > vh) {y=evt.clientY - tipRect.height - padding;}
  x=Math.max(4, Math.min(x, vw - tipRect.width - 4));
  y=Math.max(4, Math.min(y, vh - tipRect.height - 4));
  tip.style.left=x+"px";
  tip.style.top=y+"px";};
window.addEventListener("mousemove", window.moveTooltip);})();



