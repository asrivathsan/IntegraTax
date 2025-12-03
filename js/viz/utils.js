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
function sethiddendescendants(internal, hidden) {
  internal.descendants().forEach(n => {
    if (n !== internal) {
      if (n.data && n.data.frozen) return;
      n._hiddenV = hidden;
    }
  });
}

function reservepixelforlabels() {
  const labelNodes = document.querySelectorAll('text[id^="terminaltext"]');
  let maxWidth = 0;

  labelNodes.forEach(el => {
    const bbox = el.getBBox ? el.getBBox() : null;
    if (bbox && bbox.width > maxWidth) maxWidth = bbox.width;
  });
  if (maxWidth === 0) {
    const probe = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    const avg = getTextWidth(probe, "14px sans-serif") / probe.length;
    maxWidth = keepchars() * avg;
  }
  const fixedBuffer = 100;
  return Math.ceil(maxWidth + fixedBuffer);
}


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

function getclustermembership(treeData, clustperc){var clustermembership = {};
  treeData.descendants().forEach(function(d){if(d.data.terminal){let currentNode = d;
    let bestParent = null;
    let bestFusepoint = -Infinity; 
    let clustpercnum = parseFloat(clustperc); 
    while (currentNode.parent) {let parentFusepoint = parseFloat(currentNode.parent.data.fusepoint); 
      if (!isNaN(parentFusepoint) && parentFusepoint <= clustpercnum) {
          if (parentFusepoint >= bestFusepoint) {
              bestParent = currentNode.parent;
              bestFusepoint = parentFusepoint;}}
      currentNode = currentNode.parent;}
    clustermembership[d.data.terminal] = bestParent ? bestParent.data.name : d.data.terminal;}});
  const uniqueClusters = [...new Set(Object.values(clustermembership))];
  const clusterRemap = {};
  uniqueClusters.forEach((cluster, idx) => {
  clusterRemap[cluster] = idx + 1;});
  const remappedMembership = {};
  for (const [key, originalCluster] of Object.entries(clustermembership)) {
    remappedMembership[key] = clusterRemap[originalCluster];}
  return remappedMembership;
}



function getLITclassifications(treeData, LITmin, LITmax,maxPthresh){var LITnodeclassification = {};
  var LITterminalselections = {};
  LITmin = parseFloat(LITmin);
  LITmax = parseFloat(LITmax);
  var nodes = treeData.descendants();
  var donenodes = [];
  nodes.forEach(d => {if (d.data.terminal) {LITterminalselections[d.data.terminal] = 0;}});
  nodes.forEach(d => {let filteredlist = [];
    if (parseFloat(d.data.fusepoint) > LITmin && parseFloat(d.data.fusepoint)<=LITmax) {templist=maxpairs[d.data.name].split(":");
      filteredlist = [safeID[hap[templist[0]]], safeID[hap[templist[1]]]];
      filteredlist.push(safeID[rephaps[d.data.name]]);
      LITnodeclassification[d.data.name] = 1;
      for (var i = 0; i < filteredlist.length; i++) {LITterminalselections[filteredlist[i]] = 1;}
      let childnodes = getDescendants(d);
      childnodes.forEach(k => {if (k != d) {donenodes.push(k);}});}
      else if (maxP[d.data.name] > maxPthresh && parseFloat(d.data.fusepoint) <= LITmax) {templist=maxpairs[d.data.name].split(":");
        filteredlist = [safeID[hap[templist[0]]], safeID[hap[templist[1]]]];
        filteredlist.push(safeID[rephaps[d.data.name]]);
        LITnodeclassification[d.data.name] = 1;
        for (var i = 0; i < filteredlist.length; i++) {LITterminalselections[filteredlist[i]] = 1;}
        let childnodes = getDescendants(d);
        childnodes.forEach(k => {if (k!=d) { donenodes.push(k);}});}});
  nodes.forEach(d => {if (parseFloat(d.data.fusepoint)<=LITmin&&maxP[d.data.name] < maxPthresh) {
    if (!donenodes.includes(d)) {if(maxpairs[d.data.name]!=""){templist=maxpairs[d.data.name].split(":");
      filteredlist = [safeID[hap[templist[0]]], safeID[hap[templist[1]]]];}
    else{filteredlist=[];filteredlist.push(safeID[rephaps[d.data.name]]);}               
    LITnodeclassification[d.data.name] = 0;
  for (var i = 0; i < filteredlist.length; i++) {LITterminalselections[filteredlist[i]] = 1;}
  let childnodes = getDescendants(d);
  childnodes.forEach(k => {if (k != d) {donenodes.push(k);}});}}});
  nodes.forEach(d => {if (!donenodes.includes(d) && d.data.terminal) {LITnodeclassification[d.data.terminal] = 0;
  LITterminalselections[d.data.terminal]=1;}});
  return [LITnodeclassification, LITterminalselections];
}

function shortenspecimen(id, keep) {if (!id) return "";
  return id.length > keep ? id.slice(0, keep - 1) + "…" : id;
}


function rgbToHex(rgb) {let rgbValues = rgb.match(/\d+/g); 
  return "#" + rgbValues.map(x => Number(x).toString(16).padStart(2, "0")).join("");
}

function selectelement(id, valueToSelect) {let element = document.getElementById(id);
    element.value = valueToSelect;
}

