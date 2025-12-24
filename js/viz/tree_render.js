var treeData=null;
function resetrulerstate() {if (window.rulerhost && window.rulerhost.parentNode) {
    window.rulerhost.parentNode.removeChild(window.rulerhost);}
	window.rulerhost = null;
	window.rulerSVG = null;
	window.rulerg = null;
	window.gridg = null;
	window.xmap = null;
	window.collapsedbands = [];}
function openfile(event){resetrulerstate();
	window.input=event.target||document.getElementById("myFile");

	document.getElementById("loadingOverlay").style.visibility="visible";
	window.spartLanePx = 0; 
 	var reader=new FileReader();
 	reader.onload=function(){var text=reader.result;	
    window.sections=text.split(/--csv--|--jsontree--|--othermetadata--/g).map(section=>section.trim())
    window.csvContent =sections[1];
    window.data= JSON.parse(sections[2]); 
	window.parsed=d3.csvParse(csvContent);
	window.nodeinstabilitystat=false;
	window.savemode=null;
	window.threshrange1=[];
	window.LITmaxvalue=null;
	window.LITminvalue=null;
	window.clustperc=null;
	window.nodetype={},
	window.safeID=[],
	window.nodeStat=[],
	window.textStat=[],
	window.sex=[],
	window.nodeTexts=[],
	window.subtreeNodeColors=[],
	window.fusepoint=[],
	window.disabledstat=[],
	window.xv=[],
	window.yv=[],
	window.hap=[],
	window.pi=[],
	window.maxP=[],
	window.instability=[],
	window.nbefore=[],
	window.nterms=[],
	window.clust=[],
	window.nhaps=[]
	window.lit=[]
	window.clusters=[]
	window.haploclusts=[]
	window.termnames=[]
	window.terminaltextcolor=[]
	window.nodenames=[]
	window.binomnameclass=[]
	window.sequence=[]
	window.spname=[]
	window.maxpairs=[]
	window.rephaps=[]
	window.terminallabel=[]
	window.terminallabelshort=[]
	window.notes=[]
	window.spartActive=false;
	parsed.map(function(d){
	safeID[d.TerminalLabel]=d.Name
	nodetype[d.Name]=d.Type;
	terminallabel[d.Name]=d.TerminalLabel
	terminallabelshort[d.Name]=shortenspecimen(d.TerminalLabel, maxKeep);  
	nodenames[d.Name]=d.Name;
	sex[d.Name]=d.Sex;
	fusepoint[d.Name]=d.Fusepoint;
	nodeStat[d.Name]=d.NodeStat;
	textStat[d.Name]=d.TextStat;
	disabledstat[d.Name]=d.Disabled;
	nodeTexts[d.Name]=d.NodeText;
	xv[d.Name]= +d.xv;
	yv[d.Name]= +d.yv;
	hap[d.Name]=d.Hap;
	pi[d.Name]=d.PI;
	maxP[d.Name]=d.MaxP;
	instability[d.Name]=d.Instability;
	nbefore[d.Name]=d.Nbefore;
	nterms[d.Name]=d.Nterms;
	clust[d.Name]=d.Clust;
	nhaps[d.Name]=d.Nhaps;
	spname[d.Name]=d.SpName;
	lit[d.Name]=d.LIT;
	clusters.push(d.Clust);
	haploclusts[d.Hap]=d.Clust;
	sequence[d.Name]=d.Sequence;
	maxpairs[d.Name]=d.MaxPairs;
	rephaps[d.Name]=d.Hapreps
	notes[d.Name]=d.Notes})




	var haptonames={}; 

	function hasFrozenNodes(treeData) {if (!treeData) return false;
  		return treeData.descendants().some(n => n.data && n.data.frozen);
	}

	Object.entries(hap).forEach(([name, hapvalue]) => {if (hapvalue!=""){ if (!haptonames[hapvalue]) {haptonames[hapvalue]=[];}
	  haptonames[hapvalue].push(name);}});

	d3.select("#dendrogram-svg").selectAll("svg").remove();


	root=d3.hierarchy(data, function(d) { return d.children; });

	const visiblenodes0=root.descendants().filter(n => !n._hiddenV);
	const maxX0=d3.max(visiblenodes0, d => +d.data.yv || 0) || 0;
	const svgHeight=maxX0 * 1.9+100;
	window.height=svgHeight+80;     

    window.metadata=sections[3];

	window.metadataparsedlines=metadata.split('\n');
	for (let line of metadataparsedlines){if(line.includes("threshrange1")){window.threshrange1=line.trim().split(",").slice(1);}
		if(line.includes("savemode")){savemode=line.trim().split(",").slice(1);}
		if(line.includes("LITmax")){LITmaxvalue=line.trim().split(",").slice(1);}
	    if(line.includes("LITmin")){LITminvalue=line.trim().split(",").slice(1);} 
	    if(line.includes("clustperc")){clustperc=line.trim().split(",").slice(1);}
		if(line.toLowerCase().startsWith("maxname")){const raw=(line.split(",").slice(1).join(",")||"").trim();
		  const n=parseInt(raw,10);
		  maxnameLength=(!Number.isNaN(n)&&n>0)?n:raw.length;
		  maxnameLength=maxnameLength+30;}}
	const exportOpts=d3.select('#exportButton');
	exportOpts.selectAll('option').data(['Select','SVG',"FASTA","Excel LIT only","SPART"]).join('option').attr('value',d=>d).text(d=>d);
	exportOpts.on('change',function(event){updateexportoption(event.target.value);});

	const LITmax=d3.select('#LITmax');
	LITmax.selectAll('option').data(threshrange1).join('option').attr('value',d=>d).text(d=>d);
	LITmax.property('value',LITmaxvalue);
	LITmax.on("change", function () {syncclusteringtoLITmax();});

	const LITmin=d3.select('#LITmin');
	LITmin.selectAll('option').data(threshrange1).join('option').attr('value',d=>d).text(d=>d);
	LITmin.property('value',LITminvalue);

	const Clustperc=d3.select('#Clustperc');
	Clustperc.selectAll('option').data(threshrange1).join('option').attr('value',d=>d).text(d=>d);
	Clustperc.property('value',clustperc);
	Clustperc.on('change',function(event){updateclustoption(event.target.value);});

	const collapseatthreshold=d3.select('#collapseatthreshold');
	const collapseoptions=["None"].concat(threshrange1);

	collapseatthreshold.selectAll('option').data(collapseoptions).join('option').attr('value',d=>d).text(d=>d);
	collapseatthreshold.property('value',"None");
	collapseatthreshold.on('change', function(event){const val=event.target.value;
	  if (val === "None") {
	    expandall();
	  } else {
	    if (hasFrozenNodes(treeData)) {
	      alert("There are frozen nodes, this feature does not work with that. Please unfreeze your nodes.");
	      collapseatthreshold.property("value", "None");
	      return;
	    }
	    precollapseatthreshold(treeData, cleanthreshold(val));
	    refreshlayout();
	  }
	});

const collapseabovethreshold=d3.select('#collapseabovethreshold');
collapseabovethreshold.selectAll('option')
  .data(collapseoptions)
  .join('option')
  .attr('value', d => d)
  .text(d => d);

collapseabovethreshold.property('value', "None");

collapseabovethreshold.on('change', function(event) {
  const val=event.target.value;
  if (val === "None") {
    expandall();
    refreshlayout();
  } else {
    precollapseabovethreshold(treeData, cleanthreshold(val));
  }
});

const nodesubtreeColour=d3.select('#nodessubtreeColorButton');
nodesubtreeColour
  .selectAll('option')
  .data(['None','PI/nonPI',"Binomial name"])
  .join('option')
  .attr('value', d => d)
  .text(d => d);

nodesubtreeColour.on('change', function(event) {
  handleexclusivecolorselection("subtree", event.target.value);
});

nodesubtreeColour.property('value', 'PI/nonPI');



const nodeColour=d3.select('#nodeColorButton');
nodeColour.selectAll('option')
  .data(['None','PI/nonPI',"Binomial name"])
  .join('option')
  .attr('value', d => d)
  .text(d => d);
nodeColour.on('change', function(event) {
  handleexclusivecolorselection("node", event.target.value);
});

const terminalnodeColour=d3.select('#nodesterminalColorButton');
terminalnodeColour.selectAll('option')
  .data(['None',"Binomial name","Cluster","Haplotype","LIT selections"])
  .join('option')
  .attr('value', d => d)
  .text(d => d);
terminalnodeColour.on('change', function(event) {
  handleexclusivecolorselection("terminal", event.target.value);
});



	const terminalTextColour=d3.select('#terminalTextColorButton');
	var toptions=['None',"Binomial name","Cluster","Haplotype","LIT selections"];
	var defaultValue='LIT selections';
	terminalTextColour.selectAll('option').data(toptions).join('option').attr('value',d=>d).text(d=>d);
	terminalTextColour.property('value',defaultValue);
	terminalTextColour.on('change',function(event){updateterminaltextColour(event.target.value);});


	const nodeText=d3.select('#nodeTextButton');
	nodeText.selectAll('option').data(['Fusepoints','MaxP','Node ID']).join('option').attr('value',d=>d).text(d=>d);
	nodeText.on('change',function(event){displaynodetext(event.target.value);});
	const termTextLenInput=document.getElementById("terminalTextLength");
	termTextLenInput.addEventListener("change", (event) => {
	  let newLen=parseInt(event.target.value, 10);
	  if (isNaN(newLen) || newLen < 10) newLen=10;
	  if (newLen > 300) newLen=300;
	  event.target.value=newLen;
	  updateterminallabellength(newLen);
	});
	function updateterminallabellength(maxLen) {maxnameLength=maxLen;
	  window.maxKeep=maxLen;
	  Object.keys(terminallabel).forEach(key => {terminallabelshort[key]=shortenspecimen(terminallabel[key], maxLen);});
		for (const term of Object.keys(terminallabel)) {const el=document.getElementById("terminaltext"+term+"id");
		  if (!el) continue;
		  const shortLabel=terminallabelshort[term];
		  const species=spname[term] || "";
		  const visible=(shortLabel+" "+species).trim();
		  el.textContent=visible;
		  const full=(terminallabel[term]+" "+species).trim();
		  el.dataset.fullLabel=full;
		  const bound=d3.select(el).datum();
		  if (bound && bound.data) bound.data.fullLabel=full;}
	  const reserve=reservepixelforlabels();
	  const container=document.querySelector(".dendrogram-container");
	  const newWidth=container ? container.clientWidth : window.innerWidth;
	  d3.select("#graphSvg").attr("width", newWidth);
	  reflowx_log();}


	function cleanthreshold(val) {if (typeof val === "number") return val;
	if (typeof val === "string") return parseFloat(val.split(" ")[0]);return NaN;}

	function syncclusteringtoLITmax() {const LITmaxSel=document.getElementById("LITmax");
  	 const clustSel =document.getElementById("Clustperc");
  	 if (!LITmaxSel || !clustSel) return;
  	 const newThresh=cleanthreshold(LITmaxSel.value);
  	 if (cleanthreshold(clustSel.value) === newThresh) return;
	 clustSel.value=newThresh;
 	 updateclustoption(newThresh);}

	function updateclustoption(val) {clustperc=cleanthreshold(val);
	  clustermembers=getclustermembership(treeData,clustperc);
	  if (document.getElementById("nodesterminalColorButton").value==="Cluster"){updateterminalnodeColour("Cluster");}
	  if (document.getElementById("terminalTextColorButton").value==="Cluster"){updateterminaltextColour("Cluster");}
	   const nodeMode=document.getElementById("nodeColorButton").value;
  		const subtreeMode=document.getElementById("nodessubtreeColorButton").value;
  		const terminalMode=document.getElementById("nodesterminalColorButton").value;
  		if (nodeMode==="Binomial name") {updatenodeColour("Binomial name");}
		if (subtreeMode==="Binomial name") {updatesubtreeColour("Binomial name");}
  		if (terminalMode==="Binomial name") {updateterminalnodeColour("Binomial name");}
	}


	function estimatevisibleclusters(treeData,threshold){let collapsed=new Set();
	 	treeData.descendants().forEach(n=>{if (!n.data.terminal&&parseFloat(n.data.fusepoint)<=threshold){
	    let p=n.parent,ancestorCollapsed=false;
	    while (p){if (collapsed.has(p)) { ancestorCollapsed=true; break;}
			p=p.parent;}
	    if(!ancestorCollapsed) collapsed.add(n);}});
	  	return treeData.descendants().length-[...collapsed].reduce((acc,n)=>acc+n.descendants().length-1,0);
	}

	window.svg=d3.select("#dendrogram-svg").append("svg")
	    .attr("id", "graphSvg")
	    .attr("width", containerWidth)   
	    .attr("height", height)
	    .style("display", "block")
	    .append("g")
	    .attr("transform", "translate("+margin.left+","+margin.top+")");
	const dendrocontainerelement=document.querySelector(".dendrogram-container");
	window.rulerhost=document.createElement("div");
	rulerhost.className="ruler-bar";
	dendrocontainerelement.insertBefore(rulerhost, document.getElementById("dendrogram-svg"));
	window.rulerSVG=d3.select(rulerhost).append("svg")
	  .attr("id","x-ruler")
	  .attr("width", containerWidth)
	  .attr("height", 28);

	window.rulerg=rulerSVG.append("g")
	  .attr("class","ruler-g")
	  .attr("transform","translate("+margin.left+",0)");
	window.gridg=svg.append("g").attr("class","x-grid").style("pointer-events","none");

	window.treemap=d3.tree().size([height, containerWidth]);
	const tooltip=d3.select("body").append("div")
	    .attr("class", "tooltip")
	    .style("position", "absolute")
	    .style("visibility", "hidden")
	    .style("background", "rgba(0, 0, 0, 0.8)")
	    .style("color", "#fff")
	    .style("padding", "5px 10px")
	    .style("border-radius", "5px")
	    .style("font-size", "12px")
	    .style("pointer-events", "none");

	window.treeData=treemap(root);

	document.getElementById("dendrogram-svg").treeData=treeData;
	(function initCollapseMenu() {if (!treeData || !threshrange1 || threshrange1.length === 0) return;  // 
		const collapseatthreshold=d3.select('#collapseatthreshold');
	  const collapseoptions=["None"].concat(threshrange1);
	  collapseatthreshold.selectAll('option')
	    .data(collapseoptions)
	    .join('option')
	    .attr('value', d => d)
	    .text(d => d);
	  collapseatthreshold.property('value', "None");

	autocollapsethreshold=null;
	if (treeData.descendants().length > 5000) {let bestthresh=null, bestdiff=Infinity;
	  threshrange1.forEach(thresh => {const countVisible=estimatevisibleclusters(treeData, thresh);
	    const diff=Math.abs(countVisible - 5000);
	    if (diff < bestdiff) {bestdiff=diff;
	      bestthresh=thresh;}});
	 if (bestthresh !== null) {collapseatthreshold.property('value', bestthresh);
	   autocollapsethreshold=parseFloat(bestthresh);}}})();

	(function updateclusterlabels(){ window.clusterbythreshold={}
	  const sel=d3.select('#Clustperc').selectAll('option')
	  sel.text(d=>{const clusters=getclustermembership(treeData,d)
	    const nclusters=new Set(Object.values(clusters)).size
	    clusterbythreshold[d]=nclusters
	    return`${d} (${nclusters} clusters)`})})()


	const sublistddata={
	  data: treeData,
	  termnames: nodenames,
	  spnames: spname,
	  sequence: sequence,
	  disabledstat: disabledstat,
	  localsvg: svg
	};

	 window.contextMenuOptions=[
	    {title: 'Export Fasta',...sublistddata },
	    {title: 'Accept lowest code as species name',...sublistddata},
	    {title: 'Enter species name',...sublistddata},
{
  title: "Collapse / Expand subtree",
  ...sublistddata,
  action: function(elm, d) {
    const node=elm && elm.__data__;
    if (!node || node.data.terminal) return;

    node._collapsedV=!node._collapsedV;

    if (node._collapsedV) {
      sethiddendescendants(node, true);
      addband(node);
    } else {
      sethiddendescendants(node, false);
      removeband(node);
    }

    refreshlayout();
  }
},
	    {title: 'Copy Sequence / Search Online',
	    children: [{ title: 'Copy and go to BOLD', ...sublistddata },
	      { title: 'Copy and go to NCBI NT', ...sublistddata },
	      { title: 'Copy and go to GBIF', ...sublistddata },
	      { title: 'Only Copy', ...sublistddata }]},
	    {title: 'Add notes',...sublistddata},
	    {title: 'Freeze/Unfreeze',...sublistddata,action: function(elm, d){togglefreezestate(d);updatecontextmenu(d);}},
	    {title: 'Undo',...sublistddata,action: function(elm, d){togglefreezestate(d);updatecontextmenu(d);}}];


	 window.contextMenuOptionsTerminals=[

	    {title: 'Set as Verified',...sublistddata},
	    {title: 'Cannot be verified',...sublistddata},
	    {title: 'Set as Contamination',...sublistddata, hapdict: haptonames,hapdict2: hap,action: function(elm, d) {togglefreezestate(d); updatecontextmenu(d);}},
	    {title: 'Set as Male',...sublistddata,action: function(elm, d) {togglefreezestate(d);updatecontextmenu(d);}},
	    {title: 'Set as Female',...sublistddata,action: function(elm, d) {togglefreezestate(d);updatecontextmenu(d); }},
	    {title: 'Set as Holotype',...sublistddata,action: function(elm, d) {togglefreezestate(d);updatecontextmenu(d);}},
	    {title: 'Set as Slide Mounted Specimen',...sublistddata,action: function(elm, d){togglefreezestate(d); updatecontextmenu(d);}},
	    {title: 'Accept code as species name',...sublistddata},
	    {title: 'Edit/Enter species name',...sublistddata,action: function(elm, d) {togglefreezestate(d);updatecontextmenu(d);}},
	    {title: 'Copy Fasta Sequence',...sublistddata},
	    {title: 'Copy Sequence / Search Online',
	    children: [{title: 'Copy and go to BOLD', ...sublistddata },
	      { title: 'Copy and go to NCBI NT', ...sublistddata },
	      { title: 'Copy and go to BOLD-View', ...sublistddata },
	      { title: 'Copy and go to GBIF', ...sublistddata },
	      { title: 'Only Copy', ...sublistddata }]},
	    {title: 'Add notes',...sublistddata},
	    {title: 'Freeze/Unfreeze',...sublistddata,action: function(elm, d) {togglefreezestate(d); updatecontextmenu(d); }},
	    {title: 'Undo',...sublistddata,action: function(elm, d) {togglefreezestate(d); updatecontextmenu(d); }}];

	if (autocollapsethreshold !== null) {precollapseatthreshold(treeData, autocollapsethreshold);}

	window.nodes=treeData.descendants(),
	    window.links=treeData.links();
	    const reserve=reservepixelforlabels();

	const maxXV=d3.max(nodes, d => +d.data.xv || 0);
	const usablewidth=Math.max(200, window.innerWidth - margin.right - margin.left - reserve);
	const xScale=(maxXV && maxXV > 0) ? (usablewidth / maxXV) : 1;
	let ymap=makeYMap(1.9);
	nodes.forEach(function(d){d.y=30+(+d.data.xv || 0) * xScale;
	  d.x=ymap(+d.data.yv || 0);});

	var node=svg.selectAll("g.node").data(nodes, function(d) { return d.id || (d.id=++i); });
	var nodeEnter=node.enter().append("g").attr("class", "node")
	  .attr("id", function(d){if(!d.data.terminal){return "nodeid"+d.data.name+"id";}else{return "termid"+d.data.terminal+"id";}})
	  .attr("nodetype", function(d){if(!d.data.terminal){return "internalnode";}else{return "terminalnode";}})
	  .attr("transform", function(d) { return "translate("+d.y+","+d.x+")"; });



	nodeEnter.append("text").attr("id", function(d){if (d.data.terminal) {return "terminaltext"+d.data.terminal+"id"; } })
		.attr("width", 200)
		.attr("height", 25)
		.attr("x", function(d){ return d.children || d._children ? -13 : 13; })
		.attr("y", 4)
		.attr("text-anchor", function(d){ return d.children || d._children ? "end" : "start"; })
		.each(function(d){
		  if (d.data.terminal) {
		    d.data.spname=spname[d.data.terminal];
		    const full=(terminallabel[d.data.terminal]+" "+(spname[d.data.terminal] || "")).trim();
		    d.data.fullLabel=full;
		    d3.select(this).attr("data-full-label", full);
		  }
		})
		.text(function(d){
		  if (!d.data.terminal) return;
		  const short=terminallabelshort?.[d.data.terminal] || terminallabel[d.data.terminal];
		  return (short+" "+(spname[d.data.terminal] || "")).trim();
		})

	  .style("fill-opacity", 1)
	  .style("stroke-width", 0)
	  .style("stroke", "#000000")
	  .attr("font-family", "Segoe UI, Roboto, sans-serif")
	  .on("mouseover", function(event, d){if (!d || !d.data || !d.data.terminal) return;
	    const full=d.data.fullLabel || (terminallabelshort[d.data.terminal]+" "+(spname[d.data.terminal] || "")).trim();
	    tooltip.style("visibility", "visible").text(full);})
	  .on("mousemove", function(event){tooltip.style("top", (event.pageY - 10)+"px")
	      .style("left", (event.pageX+10)+"px");})
	  .on("mouseout", function(){
	    tooltip.style("visibility", "hidden");});

	nodeEnter.append("text").attr("id",function(d){if(d.data.name){return "internaltext"+d.data.name+"id";}})
	  .attr("x", function(d) { return d.children || d._children ? -13 : 13; })
	  .attr("text-anchor", function(d) { return d.children || d._children ? "end" : "start"; })
	  .attr("dy","-0.4em")
	  .attr("dx","0.6em")
	  .text(function(d) {return fusepoint[d.data.name]; })
	  .style("fill-opacity", 1)
	  .style("stroke-width", 0)
	  .style("stroke","#000000")
	  .attr("font-family", "Segoe UI, Roboto, sans-serif");

	nodeEnter.append("text")
	  .attr("id",d => "nodetext-"+d.data.name)
	  .attr("x", function(d) {return d.children || d._children ? -13 : 13; })
	  .attr("text-anchor", function(x) {return x.children || x._children ? "end" : "start"; })
	  .attr("dy","1em")
	  .attr("dx","0.6em")
	  .text(function(x){if (!x.data.terminal){nodeTexts[x.data.name]=nodeTexts[x.data.name] || spname[x.data.name] || "";return nodeTexts[x.data.name];}})
	  .style("fill-opacity", 1)
	  .style("stroke-width", 0)
	  .style("stroke","#383838")
	  .attr("font-family", "Segoe UI, Roboto, sans-serif");


	nodeEnter.append("circle").attr("r", function(d){return d.data.node_size*1.2;})
	  .style("fill", "#ffffff")
	  .attr("id", function(d){if(!d.data.terminal){return "circleid"+d.data.name+"id";}else{return "circleid"+d.data.terminal+"id";}})
	  .attr("nodecircletype", function(d){if(!d.data.terminal){return "internodecircle";}})
	  .on("contextmenu", function(event, d){if(!d.data.terminal){
	    contextMenuOptions.forEach(function(option) {if (d.data.frozen && option.title !== "Freeze/Unfreeze") {
	      option.disabled=true;  } else {option.disabled=false; }});
	    updatecontextmenu(d); 
	    d3.contextmenu(contextMenuOptions)(event, d,this);}
	    else if (d.data.terminal){contextMenuOptionsTerminals.forEach(function(option) {
	      if (d.data.frozen && option.title !== "Freeze/Unfreeze") {option.disabled=true; } else {option.disabled=false;}});
	    updatecontextmenuterminals(d);
	    d3.contextmenuterminal(contextMenuOptionsTerminals)(event, d,this);}})
	  .style("stroke-width", 1.5)
	  .style("stroke",'#444')
	  .attr('class', 'node');

// --- Tooltip & swap restricted to circle only ---
nodeEnter.select("circle")
  .on("mouseover", function (event, d) {
    let overlapping=false;
    let allnodes=d3.selectAll("g.node");
    allnodes.each(function (otherd) {
      if (d !== otherd) {
        const dx=d.x - otherd.x;
        const dy=d.y - otherd.y;
        const distance=Math.sqrt(dx * dx+dy * dy);
        if (distance < 10) overlapping=true;
      }
    });
    if (overlapping) {
      tooltip
        .style("visibility", "visible")
        .text("Left-click to change order between terminal\nand internal node options");
    }
  })
  .on("mousemove", function (event) {
    tooltip
      .style("top", event.pageY - 10+"px")
      .style("left", event.pageX+10+"px");
  })
  .on("mouseout", function () {
    tooltip.style("visibility", "hidden");
  })
  .on("click.swap", function (event, d) {
    if (event.button !== 0) return;

    let clickednode=d3.select(this.parentNode); // parent g.node
    let allnodes=d3.selectAll("g.node");
    let overlappingnode=null;
    let mindistance=Infinity;

    allnodes.each(function (otherd) {
      if (d !== otherd) {
        const dx=d.x - otherd.x;
        const dy=d.y - otherd.y;
        const distance=Math.sqrt(dx * dx+dy * dy);
        if (distance < 10 && distance < mindistance) {
          overlappingnode=d3.select(this);
          minddistance=distance;
        }
      }
    });

    if (overlappingnode) {
      clickednode.lower();
      overlappingnode.raise();
    }
  });


nodeEnter
  .filter(d => !d.data.terminal)
	window.div=d3.select("#shadowbox").append("div")
	  .attr("class", "tooltip")
	  .style("opacity", 0);

	if (autocollapsethreshold !== null){svg.selectAll("g.node")
	    .style("display", n => n._hiddenV ? "none" : null);

	svg.selectAll("path.link").style("display", l => ishiddenlink(l) ? "none" : null);}

	refreshlayout();


window.link=svg.selectAll("path.link")
  .data(links, d => linkKeyByNodes(d.source, d.target));

window.link
  .attr("id", d => linkKeyByNodes(d.source, d.target));

window.link.enter().insert("path", "g")
  .attr("class", "link")
  .attr("id", d => linkKeyByNodes(d.source, d.target)) 
  .style("fill", "transparent")
  .style("stroke-width", 1)
  .style("stroke", "#000000")
  .attr("d", elbow);

	svg.selectAll("path.link")
	.style("display", l => ishiddenlink(l) ? "none" : null);

	requestAnimationFrame(() => {uselog=true;
	  document.getElementById("togglelengthscale").textContent="Log length: ON";
	  svg.selectAll("path.link").interrupt();
	  reflowx_log();
	  svg.selectAll("path.link").attr("d", elbow);
	  console.log("animatecolor");colorlinksbasedonnodes();
	});

	window.initialReserve=reservepixelforlabels();

	if (savemode=="default"){colorlinksbasedonnodes();
	  updatesubtreeColour("PI/nonPI");
	  window.clustermembers=getclustermembership(treeData,clustperc);
	  window.maxp=parseFloat(document.getElementById("maxPthreshold").value);
	  [window.classfiedLIT,window.classifiedLITterminals]=getLITclassifications(treeData,LITminvalue,LITmaxvalue,maxp);
	  updateterminaltextColour("LIT selections")}

	else if (savemode=="manual"){window.metadataparsedlines=metadata.split('\n');
	  for (let line of metadataparsedlines){if (line.includes("clustperc")){document.getElementById("Clustperc").value=line.trim().split(",").slice(1);
	      window.clustermembers=getclustermembership(treeData,line.trim().split(",").slice(1));}
	    if (line.includes("LITmin")){document.getElementById("LITmin").value=line.trim().split(",").slice(1);}
	    if (line.includes("LITmax")){document.getElementById("LITmax").value=line.trim().split(",").slice(1);}
	    if (line.includes("subtreecolor")){document.getElementById("nodessubtreeColorButton").value=line.trim().split(",").slice(1);}
	    if (line.includes("terminalnodecolor")){document.getElementById("nodesterminalColorButton").value=line.trim().split(",").slice(1);}
	    if (line.includes("terminaltextcolor")){document.getElementById("terminalTextColorButton").value=line.trim().split(",").slice(1);}
	    if (line.includes("internnodetext")){document.getElementById("nodeTextButton").value=line.trim().split(",").slice(1);
	      displaynodetext(line.trim().split(",")[1]);}
	    if (line.includes("internnodecolor")){document.getElementById("nodeColorButton").value=line.trim().split(",").slice(1);}
	    if (line.includes("maxpthreshold")){document.getElementById("maxPthreshold").value=line.trim().split(",").slice(1);}}
	  window.maxp=parseFloat(document.getElementById("maxPthreshold").value)
	  const t=updatesubtreeColour(document.getElementById("nodessubtreeColorButton").value);
	  console.log("updatesubtreeColour returned", t);
	  updateterminalnodeColour(document.getElementById("nodesterminalColorButton").value)
	  updateterminaltextColour(document.getElementById("terminalTextColorButton").value)
	  updatenodeColour(document.getElementById("nodeTextButton").value);

	  [window.classfiedLIT,window.classifiedLITterminals]=getLITclassifications(treeData,LITminvalue,LITmaxvalue,maxp); 
console.log("now waiting");

waitForAllTransitionsToEnd(() => {
  console.log("all transitions done");
  readnodespecificcolors();

  waitForAllTransitionsToEnd(() => {
    console.log("decorations done, restoring freeze states");
    const links=treeData.links();
    svg.selectAll("g.node").each(d => {
      if (disabledstat[d.data.name] === "true" || disabledstat[d.data.terminal] === "true") {
        d.data.frozen=false;
        freezeunfreezenodes(d, svg, links, contextMenuOptions);
      }
    });
  });
});
		;}
	


	}
setTimeout(() => {
  const overlay=document.getElementById("loadingOverlay");
  if (overlay) overlay.style.visibility="hidden";
}, 300);
	reader.readAsText(input.files[0]);

}



function elbow(d, i){const n=(d && d.target) ? d.target : d;  
  const p=n.parent;
  if (p.x < n.x) {return "M"+p.y+","+p.x+ "V"+(n.x - 4)+"a"+4+","+4+" 1 0 0 "+4+","+4+ "H"+n.y;}
  else if (p.x > n.x) {return "M"+p.y+","+p.x+ "V"+(n.x+4)+"a"+-4+","+4+" 0 0 1 "+4+","+-4+ "H"+n.y;} 
  else {return "M"+p.y+","+p.x+"V"+n.x+"H"+n.y;}
}

