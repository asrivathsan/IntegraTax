function handleexclusivecolorselection(type, value) {const subtreeSelect  = document.getElementById("nodessubtreeColorButton");
  const nodeSelect=document.getElementById("nodeColorButton");
  const terminalSelect=document.getElementById("nodesterminalColorButton");
  svg.selectAll("g.node").each(function (d) {if (!d.data) return;
    const protectedNode=d.data.frozen ||d.data.nodestat==="v"||d.data.textstat==="v"||d.data.textstat==="va";
    if (!protectedNode) {d3.select(this).select("circle").style("fill", "#ffffff");}});
  d3.selectAll("path.link")
    .style("stroke", "#000000")
    .style("stroke-width", 1);
  if (type==="subtree") {nodeSelect.value = "None";
    terminalSelect.value = "None";
    updatenodeColour("None");
    updateterminalnodeColour("None");
    if (value==="None") {
      updatesubtreeColour("None");
      treeData.descendants().forEach(d => (d.data.linkcolor = false));}
    else {updatesubtreeColour(value);}}
  else if (type==="node") {subtreeSelect.value = "None";
    terminalSelect.value = "None";
    updatesubtreeColour("None");
    updateterminalnodeColour("None");
    if (value !== "None") updatenodeColour(value);}

  else if (type==="terminal") {subtreeSelect.value = "None";
    nodeSelect.value="None";
    updatesubtreeColour("None");
    updatenodeColour("None");
    if (value !== "None") updateterminalnodeColour(value);}
  waitForAllTransitionsToEnd(()=>{repaintverifiedsubtrees();  
    paintnodespecificcolors();  
    waitForAllTransitionsToEnd(() => {
      restorefreezestates();});});
}


function clustcolors (clustmembers) {var namelist=[];
  var nodes = treeData.descendants();
  var node = svg.selectAll("g.node").data(nodes, function(d) {try{if(!d.data.terminal){return 0;}
      else{var termname=d.data.terminal;
      namelist.push(clustmembers[termname]);}}
    catch (error) {null}} )
  namelist = namelist.filter(function( element ) {return element !== undefined;});
  var namesunique = namelist.filter(onlyUnique);
  var namescolors={};
  var i=0;
  namesunique.map(function(d){if (i<colorArray.length){namescolors[d]=colorArray[i];i=i+1;}else{i=0;}});
  return namescolors;
}

function hapcolors(){var namelist=[];
  var nodes=treeData.descendants();
  var node=svg.selectAll("g.node").data(nodes, function(d) {
      try{if(!d.data.terminal){return 0;}
        else{var termname=d.data.terminal;
      namelist.push(hap[termname]);}}
      catch (error) {null}} )
  namelist=namelist.filter(function( element ) {return element!==undefined;});
  var namesunique=namelist.filter(onlyUnique);
  var namescolors={};
  var i=0;
  namesunique.map(function(d){if (i<colorArray.length){namescolors[d]=colorArray[i];i=i+1;}else{i=0;}});
  return namescolors;
}


function updatenodeColour(invar) {
  if (invar=="None"){return;}


  if (invar == "PI/nonPI"){var LITmax=parseFloat(document.getElementById("LITmax").value);
    const maxPthreshold=parseFloat(document.getElementById("maxPthreshold").value);
    var LITmin=parseFloat(document.getElementById("LITmin").value);
    var highlightnodesPI=[];
    var highlightnodesnonPI=[];
    var nodes=treeData.descendants();
      nodes.forEach(d=>{if (d.data.nodestat==="v") return;if (d.data.fusepoint>LITmax){d.data.linkcolor=false;
        d3.select("#circleid"+d.data.name+"id").style("fill", "#FFFFFF");
        d3.select("#circleid"+d.data.terminal+"id").style("fill", "#FFFFFF");}
        else if (d.data.fusepoint>LITmin&&d.data.fusepoint <= LITmax){d.data.linkcolor=false;
          d3.select("#circleid"+d.data.name+"id").style("fill", "#ff0000");
          d3.select("#circleid"+d.data.terminal+"id").style("fill", "#ff0000");
          if(d.data.terminal){d.data.PIstat=1;}
          d.data.nodestat="npi";
          let childnodes=getDescendants(d);
          childnodes.forEach(k=>{if (k!=d) {if(k.data.terminal){k.data.PIstat=1;}
            highlightnodesPI.push(k);}});}
          else if(maxP[d.data.name]>maxPthreshold){d.data.linkcolor=false;
            if(d.data.terminal){d.data.PIstat=1;}
              d3.select("#circleid"+d.data.name+"id").style("fill", "#ff0000");
              d3.select("#circleid"+d.data.terminal+"id").style("fill", "#ff0000");
              d.data.nodestat="npi";
              let childnodes=getDescendants(d);
              childnodes.forEach(k=>{if (k!=d){if(k.data.terminal){k.data.PIstat=1;}
                highlightnodesPI.push(k);}}); }
            else if (d.data.fusepoint<=LITmin&&maxP[d.data.name]<maxPthreshold){if(d.data.terminal){d.data.PIstat=0;}
              d3.select("#circleid"+d.data.name+"id").style("fill", "#1F83F3");
              d3.select("#circleid"+d.data.terminal+"id").style("fill", "#1F83F3");
              d.data.nodestat="nnpi";
              d.data.linkcolor=false;
              if(d.data.terminal){d.data.PIstat=0;}
              let childnodes=getDescendants(d);
              childnodes.forEach(k => {
                  if (k!=d&&!highlightnodesPI.includes(k)){highlightnodesnonPI.push(k);}});}});

      nodes.forEach(d=>{if (d.data.nodestat==="v") return;if (d.data.terminal){if(!highlightnodesnonPI.includes(d)&&!highlightnodesPI.includes(d)) {
        d.data.PIstat=0;
        d.data.nodestat="nnpi";
        d3.select("#circleid"+d.data.terminal+"id").style("fill", "#1F83F3");}}});

      nodes.forEach(d=>{if (d.data.nodestat==="v") return;if (highlightnodesPI.includes(d)){d3.select("#circleid"+d.data.name+"id").style("fill", "#ff0000");
        d3.select("#circleid"+d.data.terminal+"id").style("fill", "#ff0000");
        if(d.data.terminal){d.data.PIstat=1;}}
        if (highlightnodesnonPI.includes(d)) {d3.select("#circleid"+d.data.name+"id").style("fill", "#1F83F3");
          d3.select("#circleid"+d.data.terminal+"id").style("fill", "#1F83F3");
        if(d.data.terminal){d.data.PIstat=0;}}});
  }

  if (invar == "Binomial name") {var LITmax=parseFloat(document.getElementById("Clustperc").value);
    var highlightnodescongruent=[];
    var highlightnodeslump=[];
    var highlightnodessplit=[];
    var nodes=treeData.descendants();
    nodes.forEach(d=>{if (d.data.nodestat==="v") return;var terminals=getTerminals(d);
      var termnames=[];
      terminals.forEach(function(k){try{if(spname[k.data.terminal]){termnames.push(spname[k.data.terminal]);}}
        catch (error){null;}});
      var uniqueNames=termnames.filter(onlyUnique);
      if (d.data.fusepoint>LITmax) {d3.select("#circleid"+d.data.name+"id").style("fill", "#FFFFFF");
        d3.select("#circleid"+d.data.terminal+"id").style("fill", "#FFFFFF");} 
      else {if (uniqueNames.length==1) {let species=uniqueNames[0];
        let occurrencesOutside=Object.values(spname).filter(name => name===species).length;
        if(occurrencesOutside===termnames.length){d3.select("#circleid"+d.data.name+"id").style("fill", "#008000");
          d3.select("#circleid"+d.data.terminal+"id").style("fill", "#008000");
          let childnodes=getDescendants(d);
          childnodes.forEach(k=>{if(k!=d){highlightnodescongruent.push(k);}});}
        else {d3.select("#circleid"+d.data.name+"id").style("fill", "#808080");
          d3.select("#circleid"+d.data.terminal+"id").style("fill", "#808080");
          let childnodes=getDescendants(d);
          childnodes.forEach(k=>{if (k!=d){highlightnodessplit.push(k);}});}}
        else if (uniqueNames.length>1){d3.select("#circleid"+d.data.name+"id").style("fill", "#FFA500");
            d3.select("#circleid"+d.data.terminal+"id").style("fill", "#FFA500");
            let childnodes=getDescendants(d);
            childnodes.forEach(k=>{if(k!=d){highlightnodeslump.push(k);}});}}});
            nodes.forEach(d=>{if (highlightnodescongruent.includes(d)){d3.select("#circleid"+d.data.name+"id").style("fill", "#008000");
             d3.select("#circleid"+d.data.terminal+"id").style("fill", "#008000");}
            if(!highlightnodescongruent.includes(d)&&!highlightnodeslump.includes(d)&&highlightnodessplit.includes(d) ){d3.select("#circleid"+d.data.name+"id").style("fill", "#808080");
              d3.select("#circleid"+d.data.terminal+"id").style("fill", "#808080");}
            if (highlightnodeslump.includes(d) ) {d3.select("#circleid"+d.data.name+"id").style("fill", "#FFA500");
              d3.select("#circleid"+d.data.terminal+"id").style("fill", "#FFA500");}});}

}

function updatesubtreeColour(invar) {if (invar == "None") {  return;}
  if (invar == "PI/nonPI") {
    var LITmax=parseFloat(document.getElementById("LITmax").value);
    var LITmin= parseFloat(document.getElementById("LITmin").value);
    const maxp=parseFloat(document.getElementById("maxPthreshold").value);
    console.log("maxp",maxp)

    threshrange1.forEach((value, index) => {if (LITmax == value) {var highlightnodesPI=[];
    var highlightnodesnonPI=[];
    var nodes=treeData.descendants();
    nodes.forEach(d => {if (d.data.nodestat==="v") return;if (d.data.fusepoint > LITmax) { d.data.linkcolor=true;
      d3.select("#circleid"+d.data.name+"id").style("fill", "#FFFFFF");
      d3.select("#circleid"+d.data.terminal+"id").style("fill", "#FFFFFF");} 

    else if (d.data.fusepoint > LITmin&&d.data.fusepoint <= LITmax) {d3.select("#circleid"+d.data.name+"id").style("fill", "#ff0000");
      d3.select("#circleid"+d.data.terminal+"id").style("fill", "#ff0000");
      d.data.nodestat="spi";
      d.data.linkcolor=true;
      let childnodes=getDescendants(d);
      childnodes.forEach(k => {if (k != d) {highlightnodesPI.push(k);}});}
    else if (maxP[d.data.name] > maxp) {d3.select("#circleid"+d.data.name+"id").style("fill", "#ff0000");
      d3.select("#circleid"+d.data.terminal+"id").style("fill", "#ff0000");
      d.data.nodestat="spi";
      d.data.linkcolor=true;
      let childnodes=getDescendants(d);
      childnodes.forEach(k => {if (k != d) {highlightnodesPI.push(k);}});}
    else if (d.data.fusepoint <= LITmin&&maxP[d.data.name] < maxp) {d3.select("#circleid"+d.data.name+"id").style("fill", "#1F83F3");
      d3.select("#circleid"+d.data.terminal+"id").style("fill", "#1F83F3");
      d.data.nodestat="snpi";
      d.data.linkcolor=true;
      let childnodes=getDescendants(d);
      childnodes.forEach(k => {if (k != d&&!highlightnodesPI.includes(k)) {highlightnodesnonPI.push(k);}});}});

    nodes.forEach(d => {if (d.data.nodestat==="v") return;if (d.data.terminal) {if (!highlightnodesnonPI.includes(d)&&!highlightnodesPI.includes(d)) {d.data.nodestat="snpi";
     d3.select("#circleid"+d.data.terminal+"id").style("fill", "#1F83F3");}}});

    nodes.forEach(d => {if (d.data.nodestat==="v") return;if (highlightnodesPI.includes(d)) {d3.select("#circleid"+d.data.name+"id").style("fill", "#ff0000");
      d3.select("#circleid"+d.data.terminal+"id").style("fill", "#ff0000");}
      if (highlightnodesnonPI.includes(d)) {d3.select("#circleid"+d.data.name+"id").style("fill", "#1F83F3");
      d3.select("#circleid"+d.data.terminal+"id").style("fill", "#1F83F3");}});
    }});console.log("updatesubtree");t=colorlinksbasedonnodes();return t;}


  if (invar == "Binomial name") {var LITmax=parseFloat(document.getElementById("Clustperc").value);
    var highlightnodescongruent=[];
    var highlightnodeslump=[];
    var highlightnodessplit=[];
    var nodes=treeData.descendants();
    nodes.forEach(d => {if (d.data.nodestat==="v") return;var terminals=getTerminals(d);
      var termnames=[];
      terminals.forEach(function(k) {try {if (spname[k.data.terminal]) {termnames.push(spname[k.data.terminal]); }} 
          catch (error) {null;}});
      var uniqueNames=termnames.filter(onlyUnique);
      if (d.data.fusepoint > LITmax) {d3.select("#circleid"+d.data.name+"id").style("fill", "#FFFFFF");
          d3.select("#circleid"+d.data.terminal+"id").style("fill", "#FFFFFF");} 
      else {if (uniqueNames.length == 1) {
          let species=uniqueNames[0];
          let occurrencesOutside=Object.values(spname).filter(name => name===species).length;
          if (occurrencesOutside===termnames.length) {
              d.data.linkcolor=true;
              d.data.nodestat="c";
              d3.select("#circleid"+d.data.name+"id").style("fill", "#008000");
              d3.select("#circleid"+d.data.terminal+"id").style("fill", "#008000");
              let childnodes=getDescendants(d);
              childnodes.forEach(k => {if (k != d) {highlightnodescongruent.push(k);}});}
      else {d.data.linkcolor=true;
          d.data.nodestat="s";
          d3.select("#circleid"+d.data.name+"id").style("fill", "#808080");
          d3.select("#circleid"+d.data.terminal+"id").style("fill", "#808080");
          let childnodes=getDescendants(d);
          childnodes.forEach(k => {if (k != d) {highlightnodessplit.push(k);}});}}
      else if (uniqueNames.length > 1){d.data.linkcolor=true;
          d.data.nodestat="l";
          d3.select("#circleid"+d.data.name+"id").style("fill", "#FFA500");
          d3.select("#circleid"+d.data.terminal+"id").style("fill", "#FFA500");
          let childnodes=getDescendants(d);
          childnodes.forEach(k => {if (k != d) {highlightnodeslump.push(k);}});}}}); 
      nodes.forEach(d => {if (d.data.nodestat==="v") return;if (highlightnodescongruent.includes(d)) {d.data.nodestat="c";
        d3.select("#circleid"+d.data.name+"id").style("fill", "#008000");
        d3.select("#circleid"+d.data.terminal+"id").style("fill", "#008000");}
        if(!highlightnodescongruent.includes(d)&&!highlightnodeslump.includes(d)&&highlightnodessplit.includes(d)){d.data.nodestat="s";
          d3.select("#circleid"+d.data.name+"id").style("fill", "#808080");
          d3.select("#circleid"+d.data.terminal+"id").style("fill", "#808080");}
        if (highlightnodeslump.includes(d)){d.data.nodestat="l";
          d3.select("#circleid"+d.data.name+"id").style("fill", "#FFA500");
          d3.select("#circleid"+d.data.terminal+"id").style("fill", "#FFA500");}});console.log("updatesubtree");
    t=colorlinksbasedonnodes();return t;}
}



function updateterminalnodeColour(invar) {

  if (invar=="None"){return;}

  if (invar=="Binomial name"){clustercolors=clustcolors(spname);
    var nodes=treeData.descendants();
    var node=svg.selectAll("g.node").data(nodes,function(d){try{var termname=d.data.terminal;
    d3.select(this).select("circle").style("fill", function(d) { terminaltextcolor[termname]=clustercolors[spname[termname]];  
    return clustercolors[spname[termname]];});}
    catch(error){null}})}

  if (invar=="Cluster"){clustercolors=clustcolors(clustermembers);
    var nodes=treeData.descendants();
    var node=svg.selectAll("g.node").data(nodes, function(d) {try{var termname=d.data.terminal;
    d3.select(this).select("circle").style("fill", function(d) { terminaltextcolor[termname]=clustercolors[clustermembers[termname]];
    return clustercolors[clustermembers[termname]];} );}
    catch (error) {null}})}

  if (invar=="Haplotype"){haplocolors=hapcolors();
    var nodes=treeData.descendants();
    var node=svg.selectAll("g.node").data(nodes, function(d) {try{var termname=d.data.terminal;
      d3.select(this).select("circle").style("fill", function(d){return haplocolors[hap[termname]];})}
      catch (error) {null}} )}

  if (invar=="LIT selections"){var LITmaxvalue=parseFloat(document.getElementById("LITmax").value);
    var LITminvalue=parseFloat(document.getElementById("LITmin").value);
    const maxp=parseFloat(document.getElementById("maxPthreshold").value);
    var [classfiedLIT,classifiedLITterminals]=getLITclassifications(treeData,LITminvalue,LITmaxvalue,maxp);
    var nodes=treeData.descendants();
    nodes.forEach(d => {d3.select("#circleid"+d.data.terminal+"id").style("fill", function(d){if(classifiedLITterminals[d.data.terminal]==1){return "#ff0000"}
    else{return "#ffffff"}});});}
}



function updateterminaltextColour(invar) {if (invar=="None"){var nodes=treeData.descendants();
  var node=svg.selectAll("g.node").data(nodes,function(d){const term = d.data.terminal; const ts = d.data.textstat;if (ts && ["v", "va", "c", "cnv", "h", "s"].includes(ts)) return;d3.select("#termid"+d.data.terminal+"id").style("fill", function(d) { terminaltextcolor[d.data.terminal]="#000000";return "#000000"})})};

  if (invar=="Binomial name"){clustercolors=clustcolors(spname);
    var nodes=treeData.descendants();
    var node=svg.selectAll("g.node")
    .data(nodes, function(d) {const term = d.data.terminal; const ts = d.data.textstat;if (ts && ["v", "va", "c", "cnv", "h", "s"].includes(ts)) return;var termname=d.data.terminal;
    d3.select("#termid"+termname+"id").style("fill", function(d) { terminaltextcolor[termname]=clustercolors[clust[termname]];
    return clustercolors[spname[termname]];});})}
  if (invar=="Cluster"){clustercolors=clustcolors(clustermembers);
    var nodes=treeData.descendants();
    var node=svg.selectAll("g.node").data(nodes, function(d) {const term = d.data.terminal; const ts = d.data.textstat;if (ts && ["v", "va", "c", "cnv", "h", "s"].includes(ts)) return;var termname=d.data.terminal;
    d3.select("#termid"+termname+"id").style("fill", function(d) { terminaltextcolor[termname]=clustercolors[clust[termname]]; 
    return clustercolors[clustermembers[termname]];});})}
  if (invar=="Haplotype"){haplocolors=hapcolors();
    var nodes=treeData.descendants();
    var node=svg.selectAll("g.node").data(nodes, function(d) {const term = d.data.terminal; const ts = d.data.textstat;if (ts && ["v", "va", "c", "cnv", "h", "s"].includes(ts)) return;try{var termname=d.data.terminal;
          d3.select("#termid"+termname+"id").style("fill", function(d) { terminaltextcolor[d.data.terminal]=haplocolors[hap[termname]];
          return haplocolors[hap[termname]];})}
        catch (error){null}})}

  if (invar=="LIT selections"){var LITmaxvalue=parseFloat(document.getElementById("LITmax").value);
    var LITminvalue=parseFloat(document.getElementById("LITmin").value);
    const maxp=parseFloat(document.getElementById("maxPthreshold").value);
    var [classfiedLIT,classifiedLITterminals]=getLITclassifications(treeData,LITminvalue,LITmaxvalue,maxp);
    var nodes=treeData.descendants();
      nodes.forEach(d => {const term = d.data.terminal; const ts = d.data.textstat;if (ts && ["v", "va", "c", "cnv", "h", "s"].includes(ts)) return;d3.select("#termid"+d.data.terminal+"id").style("fill", function(d){if(classifiedLITterminals[d.data.terminal]==1){return "#ff0000"}
      else{return "#000000"}});});}
}

function updateLIToption(invar){var termselection=document.getElementById("terminalTextColorButton").value;
  var nodeselection=document.getElementById("nodeColorButton").value;
  var subtreeselection=document.getElementById("nodessubtreeColorButton").value;
  updateterminaltextColour(termselection);updateterminalnodeColour(nodeselection);updatesubtreeColour(subtreeselection);
}

function displaynodetext(invar){var nodes=treeData.descendants();
  nodes.forEach(function(d){let selector="#internaltext"+d.data.name+"id";
  let text="";
  if(invar==="Fusepoints") {text=fusepoint[d.data.name];}
  else if(invar==="MaxP") {text=maxP[d.data.name];}
  else if(invar==="Node ID") {text=d.data.name;}
  d3.select(selector).text(text);});
}

function applycurrentcoloring() {console.log("applytriggered");const nodeColor=document.getElementById("nodeColorButton").value;
  const subtreeColor=document.getElementById("nodessubtreeColorButton").value;
  const terminaltextcolor=document.getElementById("terminalTextColorButton").value;
  const terminalnodecolor=document.getElementById("nodesterminalColorButton").value;
  if (nodeColor&&nodeColor!=="None") {updatenodeColour(nodeColor);}
  if (subtreeColor&&subtreeColor!=="None") {updatesubtreeColour(subtreeColor);}
  if (terminaltextcolor&&terminaltextcolor!=="None") {updateterminaltextColour(terminaltextcolor);}
  if (terminalnodecolor&&terminalnodecolor!=="None") {updateterminalnodeColour(terminalnodecolor);}    
  reflowx_log();
const activeSubtree = document.getElementById("nodessubtreeColorButton").value;
if (activeSubtree && activeSubtree !== "None") {
  colorlinksbasedonnodes();
}
}

function colorlinksbasedonnodes(instant = false) {var links = treeData.links();
  svg.selectAll("path.link")
    .interrupt()              
    .style("stroke", "#000000") 
    .style("stroke-opacity", 1)
    .style("stroke-width", 1);
  function hasVerifiedAncestor(n){let p = n.parent;
    while (p) {if (p.data && p.data.nodestat==="v") return true;
      p = p.parent;}
    return false;}
  const tt = svg.transition().duration(300);
  console.log("colorlinksbasedonnodes start", performance.now());
  svg.selectAll("path.link").data(links)
    .transition(tt)
    .style("stroke", function(d){let s = d3.select("#circleid"+d.source.data.name+"id"),
          t = d3.select("#circleid"+d.target.data.name+"id");
      if (s.empty()||t.empty()) { t = d3.select("#circleid"+d.target.data.terminal+"id"); }
      let sc = s.style("fill"), tc = t.style("fill");
      const childStat = d.target.data && d.target.data.textstat;
      if (childStat && (childStat==="v"||childStat==="va"||childStat==="c"||childStat==="cnv"||childStat==="h"||childStat==="s")) {tc=sc;}
      const parentIsVerified = (d.source.data && d.source.data.nodestat==="v")||hasVerifiedAncestor(d.source);
      if (parentIsVerified) { sc = tc = "#009933"; }
      if (rgbToHex(sc) != "#ffffff") { return sc===tc ? sc : "#000000"; }
      else { return "#000000"; }})
    .style("stroke-width", function(d){let s = d3.select("#circleid"+d.source.data.name+"id"),
          t = d3.select("#circleid"+d.target.data.name+"id");
      if (s.empty()||t.empty()) { t = d3.select("#circleid"+d.target.data.terminal+"id"); }
      let sc = s.style("fill"), tc = t.style("fill");
      const childStat = d.target.data && d.target.data.textstat;
      if (childStat && (childStat==="v"||childStat==="va"||childStat==="c"||childStat==="cnv"||childStat==="h"||childStat==="s")) {tc = sc;}
      const parentIsVerified = (d.source.data && d.source.data.nodestat==="v")||hasVerifiedAncestor(d.source);
      if (parentIsVerified) { sc = tc = "#009933"; }
      if (rgbToHex(sc) != "#ffffff") { return sc===tc ? 5 : 1; }
      else { return 1; }});
  svg.selectAll("path.link").style("display", l => ishiddenlink(l) ? "none" : null);
  console.log("colorlinksbasedonnodes returning", tt);
  return tt;
}

function readnodespecificcolors(){var nodes = treeData.descendants();
  console.log("applying nodespecific colors")
  var links = treeData.links();
  var node = svg.selectAll("g.node").data(nodes, function (d){
  if (nodeStat[d.data.name]=="v")
  {marksubtreeasverified(d,treeData,svg);}
  if (textStat[d.data.terminal]==="va"||textStat[d.data.terminal]==="v") {console.log(textStat[d.data.terminal]);setasverified(d, textStat[d.data.terminal]==="va"?"a":"o");}
  if (textStat[d.data.terminal]==="c") {console.log(textStat[d.data.terminal]);setascontamination(d,saveState=false);}
  if (textStat[d.data.terminal]==="cnv") {console.log(textStat[d.data.terminal]);cannotbeverified(d,saveState=false);}
  if (sex[d.data.terminal]==="m"||sex[d.data.terminal]=== "f") {console.log(sex[d.data.terminal]);d.data.sex=sex[d.data.terminal];
    setasmalefemale(d, d.data.sex, false); }
  if (textStat[d.data.terminal]==="h") {setasverified(d, "h");}
  if (textStat[d.data.terminal]==="s") {setasverified(d, "s");}
      if (disabledstat[d.data.terminal]=="true"){d.data.frozen=false;
    freezeunfreezenodes(d,svg,links,contextMenuOptions);}})
  svg.selectAll("g.node").each(function(d){
  if(!d.data.note && notes[d.data.name]) d.data.note = notes[d.data.name];
  if(!d.data.note && notes[d.data.terminal]) d.data.note = notes[d.data.terminal];
  if(d.data.note && d.data.note.trim()){
    rendernotes(d, svg);}});
}

function waitForAllTransitionsToEnd(callback) {
  function check() {
    const active = svg.selectAll("*")
      .filter(function () { return d3.active(this); })
      .size();
    if (active === 0) callback();
    else requestAnimationFrame(check);
  }
  requestAnimationFrame(check);
}

function paintnodespecificcolors() {const nodes = treeData.descendants();
  const links = treeData.links();
  svg.selectAll("g.node").each(function (d) {if (!d.data) return;
    if (!d.data.terminal){if (d.data.nodestat==="v") marksubtreeasverified(d, treeData, svg);
      if (!d.data.note && notes[d.data.name]) d.data.note = notes[d.data.name];
      if (d.data.note && d.data.note.trim()) rendernotes(d, svg);
      return;}
    const ts = d.data.textstat;
    if (ts==="va"||ts==="v") setasverified(d,ts==="va"?"a":"o");
    else if (ts==="c") setascontamination(d,false);
    else if (ts==="cnv") cannotbeverified(d,false);
    else if (ts==="h"||ts==="s") setasverified(d, ts);
    if (d.data.sex==="m"||d.data.sex==="f") {setasmalefemale(d, d.data.sex, false);}
    if (!d.data.note && notes[d.data.terminal]) d.data.note = notes[d.data.terminal];
    if (!d.data.note && notes[d.data.name]) d.data.note = notes[d.data.name];
    if (d.data.note && d.data.note.trim()) rendernotes(d, svg);});
}

function restorefreezestates() {const links = treeData.links();
  svg.selectAll("g.node").each(function (d) {const isDisabledInternal = disabledstat[d.data.name]==="true";
    const isDisabledTerminal = disabledstat[d.data.terminal]==="true";
    if (d.data.frozen||isDisabledInternal||isDisabledTerminal) {d.data.frozen = false;
      freezeunfreezenodes(d, svg, links, contextMenuOptions);}});
}

function repaintverifiedsubtrees() {const nodes = treeData.descendants();
  nodes.forEach(d => {
    if (d.data && d.data.nodestat==="v") { marksubtreeasverified(d, treeData, svg);}});
}

