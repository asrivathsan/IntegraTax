
function displaysummary(result,clustperc,results,showall){const{matchratio,specimencongruence,ncongruent,nclusters,nterminals,
    nterminalswithspecies,nclusterswithspecies,nspecies,ncongruentspecimens}=result
  const popup=document.getElementById("SummaryPopup")
  const content=document.getElementById("SummaryContent")
  popup.style.display="block"
  let chartarea=showall
    ? `<div style="display:flex;justify-content:space-around;align-items:flex-start;
        gap:20px;margin:20px auto;max-width:1200px;">
         <div id="clusterChart" style="flex:1;height:320px;"></div>
         <div id="matchChart" style="flex:1;height:320px;"></div>
         <div id="specChart" style="flex:1;height:320px;"></div>
       </div>`
    : `<div id="clusterChart" style="width:90%;height:320px;margin:20px auto;"></div>`
  content.innerHTML=`
  <div style="max-width:1000px;margin:0 auto;text-align:center;">
    <h3>Dataset summary</h3>
    <p><strong>Number of specimens:</strong> ${nterminals}</p>
    <p><strong>Number of species:</strong> ${nspecies}</p>
    ${chartarea}
    <h3>Threshold specific summary</h3>
    <p><strong>Clustering threshold:</strong> ${clustperc}</p>
    <p><strong>Clusters with species names:</strong> ${nclusterswithspecies}</p>
    <p><strong>Specimens with species names:</strong> ${nterminalswithspecies}</p>
    <p><strong>Specimens in congruent clusters:</strong> ${ncongruentspecimens}</p>
    <p><strong>Congruent clusters:</strong> ${ncongruent}</p>
    <p><strong>Match ratio:</strong> ${matchratio.toFixed(3)}</p>
    <p><strong>Specimen congruence:</strong> ${specimencongruence.toFixed(3)}</p>
  </div>`
  if(showall) drawallgraphs(results)
  else drawclustergraph()}
function drawclustergraph(){const chartdiv=document.getElementById("clusterChart")
  const data=Object.entries(clusterbythreshold).map(([thr,val])=>({thr:+thr,clusters:+val}))
  if(data.length===0)return
  const w=chartdiv.clientWidth||350,h=320,m={l:45,r:10,t:10,b:35}
  const svg=d3.select(chartdiv).append("svg").attr("width",w).attr("height",h)
  const x=d3.scaleLinear().domain(d3.extent(data,d=>d.thr)).range([m.l,w-m.r])
  const y=d3.scaleLinear().domain([0,d3.max(data,d=>d.clusters)]).nice().range([h-m.b,m.t])
  const line=d3.line().x(d=>x(d.thr)).y(d=>y(d.clusters))
  svg.append("path").datum(data).attr("fill","none").attr("stroke","#093b1a").attr("stroke-width",2).attr("d",line)
  svg.append("g").attr("transform",`translate(0,${h-m.b})`).call(d3.axisBottom(x).ticks(5))
  svg.append("g").attr("transform",`translate(${m.l},0)`).call(d3.axisLeft(y).ticks(5))
  svg.append("text").attr("x",w/2).attr("y",h-8).attr("text-anchor","middle").attr("font-size","10px").text("Threshold")
  svg.append("text").attr("x",-h/2).attr("y",15).attr("transform","rotate(-90)").attr("text-anchor","middle").attr("font-size","10px").text("Clusters")}
function drawallgraphs(results){if(!results||results.length===0)return
  const w=380,h=320,m={l:45,r:20,t:10,b:35}
  const tooltip=d3.select("body").append("div")
    .style("position","absolute").style("visibility","hidden")
    .style("background","rgba(0,0,0,0.75)").style("color","#fff")
    .style("padding","4px 8px").style("border-radius","4px")
    .style("font-size","12px").style("pointer-events","none")
function drawchart(divid,valuefield,color,label,ylab,domain=[0,1]){const div=document.getElementById(divid)
  const w=380,h=340,m={l:50,r:25,t:40,b:40} 
  const svg=d3.select(div).append("svg").attr("width",w).attr("height",h)
  const x=d3.scaleLinear().domain(d3.extent(results,d=>d.thr)).range([m.l,w-m.r])
  const y=d3.scaleLinear().domain(domain).range([h-m.b,m.t])
  const line=d3.line().x(d=>x(d.thr)).y(d=>y(d[valuefield]))
  svg.append("path").datum(results)
    .attr("fill","none").attr("stroke",color).attr("stroke-width",2).attr("d",line)
  svg.selectAll("circle.pt").data(results).enter().append("circle")
    .attr("cx",d=>x(d.thr)).attr("cy",d=>y(d[valuefield]))
    .attr("r",3).attr("fill",color).style("opacity",0)
    .on("mouseover",(e,d)=>{tooltip.style("visibility","visible")
      .text(`Threshold: ${d.thr.toFixed(2)}, ${label}: ${d[valuefield].toFixed(3)}`)})
    .on("mousemove",e=>{tooltip.style("top",(e.pageY-25)+"px").style("left",(e.pageX+10)+"px")})
    .on("mouseout",()=>tooltip.style("visibility","hidden"))
  const maxd=results.reduce((a,b)=>b[valuefield]>a[valuefield]?b:a)
  svg.append("circle")
    .attr("cx",x(maxd.thr)).attr("cy",y(maxd[valuefield]))
    .attr("r",5).attr("fill",color).attr("stroke","#000").attr("stroke-width",1.2)
  svg.append("text")
    .attr("x",x(maxd.thr)+6).attr("y",y(maxd[valuefield])-8)
    .attr("font-size","10px").attr("fill",color)
    .text(`distance=${maxd.thr.toFixed(2)}, y=${maxd[valuefield].toFixed(2)}`)
  svg.append("g")
    .attr("transform",`translate(0,${h-m.b})`)
    .call(d3.axisBottom(x).ticks(5))
  svg.append("g")
    .attr("transform",`translate(${m.l},0)`)
    .call(d3.axisLeft(y).ticks(5))
  svg.append("text")
    .attr("x",w/2).attr("y",h-8)
    .attr("text-anchor","middle").attr("font-size","10px").text("Threshold")
  svg.append("text")
    .attr("x",-h/2).attr("y",15)
    .attr("transform","rotate(-90)")
    .attr("text-anchor","middle").attr("font-size","10px").text(ylab)
}

  drawchart("clusterChart","nclusters","#093b1a","Clusters","Clusters",[0,d3.max(results,d=>d.nclusters)])
  drawchart("matchChart","matchratio","#d62828","Match ratio","Match ratio",[0,1])
  drawchart("specChart","specimencongruence","#1d7ed1","Specimen congruence","Specimen congruence",[0,1])
}


function updateexportoption(invar){if(invar=="SVG"){ToSVG(svg);
	selectelement('exportButton',"Select");}
	if(invar=="CSV"){ToCSV(parsed)
		selectelement('exportButton','Select')}
	if(invar=="FASTA"){ToFASTA(parsed)
		selectelement('exportButton','Select')}
	if(invar=="Excel LIT only"){ExcelLIT(parsed)
		selectelement('exportButton','Select')}
 	if (invar=="SPART"){ToSPART();
 		selectelement('exportButton',"Select");}
 }


function ToSVG(svgselection){const svgnode = svgselection.node().parentNode.cloneNode(true); 
  const svgwrapper = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  const originalSVG = document.getElementById("graphSvg");
  [...originalSVG.attributes].forEach(attr => {svgwrapper.setAttribute(attr.name, attr.value);});
  svgwrapper.appendChild(svgnode);
  const serializer = new XMLSerializer();
  const svgstr = serializer.serializeToString(svgwrapper);
  const svgblob = new Blob([svgstr], {type:"image/svg+xml;charset=utf-8" });
  const svgURL = URL.createObjectURL(svgblob);
  const downloadlink = document.createElement("a");
  downloadlink.href = svgURL;
  downloadlink.download = "dendrogram.svg";
  document.body.appendChild(downloadlink);
  downloadlink.click();
  document.body.removeChild(downloadlink);
}



function ToSPART(){var clustperc = document.getElementById("Clustperc").value;
  var clusterMembership = getclustermembership(treeData, clustperc);
  const now = new Date().toISOString().slice(0, 19); 
  const allTerminals = treeData.descendants().filter(d => d.data.terminal);
  const numTerminals = allTerminals.length;
  let spartLines = [
    "begin spart;",
    `Project_name =${input};`,
    `Date = ${now};`,
    `N_spartitions = 1 : Clustering_at_${Clustperc}`,
    `N_individuals = ${numTerminals}`,
    "[Generated by Objective Clustering in LITIntegrator]",
    "Individual_asasignment"];
  for (let id in clusterMembership){spartLines.push(`${id} : ${clusterMembership[id]}`);}
  spartLines.push("end;");
  const blob = new Blob([spartLines.join('\n')], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "partition.spart";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}


function ExcelLIT(invar){var nodes = treeData.descendants();
  var node = svg.selectAll("g.node").data(nodes, function(d){if(d.data.name){nodeStat[d.data.name]=d.data.nodestat; 
  disabledstat[d.data.name]=d.data.frozen;
  nodeTexts[d.data.name]=spname[d.data.name]};
  if(d.data.terminal){nodeStat[d.data.terminal]=d.data.nodestat}
  if(d.data.textstat){textStat[d.data.terminal]=d.data.textstat}
  if(d.data.sex){sex[d.data.terminal]=d.data.sex}})
  var LITmaxvalue = parseFloat(document.getElementById("LITmax").value);
  var LITminvalue = parseFloat(document.getElementById("LITmin").value);
  const maxp = parseFloat(document.getElementById("maxPthreshold").value);
  var [classfiedLIT,classifiedLITterminals]=getLITclassifications(treeData,LITminvalue,LITmaxvalue,maxp);
  var wb = new ExcelJS.Workbook();
  var LITmax=document.getElementById("LITmax").value;
  var ws = wb.addWorksheet('Export');
  var rowvals=[]
  var nodes = treeData.descendants();
  var node = svg.selectAll("g.node").data(nodes, function(d) {
  if(d.data.terminal){rowvals[d.data.terminal] = [terminallabel[d.data.terminal],
    spname[d.data.terminal],
    hap[d.data.terminal],
    classifiedLITterminals[d.data.terminal],
    clustermembers[d.data.terminal],
    sex[d.data.terminal],
    (textStat[d.data.terminal] === "h") ? "Holotype" : "",
    (textStat[d.data.terminal] === "v") ? "Verified" :
    (textStat[d.data.terminal] === "va") ? "Verified" :
    (textStat[d.data.terminal] === "cnv") ? "Cannot be verified" :
    (textStat[d.data.terminal] === "c") ? "Contamination" :
    (textStat[d.data.terminal] === "s") ? "Slide Mounted" :"",
    d.data.note||""];}});
  ws.columns = [{ header: "ID", key: "a" },
      { header: "SpName", key: "b" },
      { header: "Haplotype", key: "c" },
      { header: "LIT selection", key: "d" },
      { header: "Cluster", key: "e" },
      { header: "Sex", key: "f" }  ,
      { header: "Holotype", key: "g" },   
      { header: "Status", key: "h" },
      { header: "Notes", key: "i" }
      ];
  for(id in rowvals){ws.addRow({ a: rowvals[id][0], b: rowvals[id][1], c: rowvals[id][2],d: rowvals[id][3],e: rowvals[id][4],f: rowvals[id][5],g: rowvals[id][6],h: rowvals[id][7], i: rowvals[id][8] });}
    lithaplist=[];
    wb.xlsx.writeBuffer({base64: true}).then( function (xls64) {var a = document.createElement("a");
      var data = new Blob([xls64], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" });
      var url = URL.createObjectURL(data);
      a.href = url;
      a.download = "export.xlsx";
      document.body.appendChild(a);
      a.click();
      setTimeout(function(){document.body.removeChild(a);
      window.URL.revokeObjectURL(url);},0);})
    .catch(function(error){null});
} 



function ToFASTA(parsed){const refinedData2 = [];
	var nodes = treeData.descendants();
  	var node = svg.selectAll("g.node").data(nodes, function(d) {
	if(d.data.name){nodeStat[d.data.name]=d.data.nodestat; 
	disabledstat[d.data.name]=d.data.frozen;
	nodeTexts[d.data.name]=spname[d.data.name]};
	if(d.data.terminal){nodeStat[d.data.terminal]=d.data.nodestat}
	if(d.data.textstat){textStat[d.data.terminal]=d.data.textstat}
	if(d.data.sex){sex[d.data.terminal]=d.data.sex}});
	parsed.forEach(item => {const Array1 = Object.values(item);
    const oldname = Array1.shift();
    if (sequence[oldname] && sequence[oldname].length > 2) {const newSpecies = spname[oldname] || "Unknown";
    const originalID = nodenames[oldname] || oldname;
    let status = 0;
    const stat = textStat[oldname];
    if (stat === "v") status ="Verified";
    else if (stat === "va") status ='Verified with species name';
    else if (stat === "h") status ="Holotype";
    else if (stat === "cnv") status ="Cannot be verified";
    else if (stat === "c") status ="Contamination"
    else if (stat === "s") status ="Slide Mounted";
    const sppart = newSpecies ? `;spname=${newSpecies}` : "";
    const statuspart = status ? `;status=${status}` : "";
    const sexinfo = sex[oldname] ? `;sex=${sex[oldname]}` : "";

    const header = `>${terminallabel[originalID] || originalID}${sppart}${statuspart}${sexinfo}`;
      refinedData2.push([header, sequence[oldname]]);}});


	let modcsvContent2 = '';
	refinedData2.forEach(row => {modcsvContent2 += row.join('\n') + '\n';});

	const blob2 = new Blob([modcsvContent2], { type: 'text/plain;charset=utf-8,' });
	const objUrl2 = URL.createObjectURL(blob2);
	const link2 = document.createElement('a');
	link2.setAttribute('href', objUrl2);
	link2.setAttribute('download', 'sequences.fasta');
	document.body.appendChild(link2);
	link2.click();
	link2.remove();
  }


function saveCSV() {const refinedData=[];
	var nodes = treeData.descendants();
	var node = svg.selectAll("g.node").data(nodes, function(d) {
	if(d.data.name){nodeStat[d.data.name]=d.data.nodestat; 
		disabledstat[d.data.name]=d.data.frozen;
    spname[d.data.name] = spname[d.data.name] || nodeTexts[d.data.name] || "";}
    nodeTexts[d.data.name]=spname[d.data.name]
    notes[d.data.name]=d.data.note||"";
	if(d.data.terminal){nodeStat[d.data.terminal]=d.data.nodestat;
    disabledstat[d.data.terminal] = d.data.frozen; 
  	if(d.data.textstat){textStat[d.data.terminal]=d.data.textstat}
  	if(d.data.sex){sex[d.data.terminal]=d.data.sex}
    notes[d.data.terminal]=d.data.note||""};
  	nodeTexts[d.data.terminal]="";
	spname[d.data.name]=d.data.spname;
  if (d.data.terminal) spname[d.data.terminal] = d.data.spname;
	termnames[d.data.terminal]=d.data.terminal;})
	const titleKeys = Object.keys(parsed[0]);
	refinedData.push(titleKeys);
	parsed.forEach(item => {const Array1=Object.values(item);
	  const oldname = Array1.shift();
	  var NewArray=[nodenames[oldname]];
    const oldlabel = Array1.shift();
    let safeLabel = oldlabel ?? '';
    if (/[",\n]/.test(safeLabel)) {safeLabel = `"${safeLabel.replace(/"/g, '""')}"`;}
    NewArray.push(safeLabel);
	  const OldClass = Array1.shift();
	  NewArray.push(OldClass);
	  NewArray.push(spname[oldname] ?? '');
	  Fusion_to_hap=Array1.slice(1, 4);
    let safenote = notes[oldname] ?? '';
    if (/[",\n]/.test(safenote)){safenote = `"${safenote.replace(/"/g, '""')}"`;}
	  NewArray=NewArray.concat(Fusion_to_hap);
	  NewArray.push(nodeStat[oldname] ?? '');
	  NewArray.push(textStat[oldname] ?? '');
	  NewArray.push(disabledstat[oldname] ?? '');
	  NewArray.push(nodeTexts[oldname] ?? '');
	  NewArray.push(sex[oldname] ?? '');
    MaxP_to_rest = Array1.slice(9);
    MaxP_to_rest[MaxP_to_rest.length - 1] = safenote ?? MaxP_to_rest.at(-1) ?? ""; 
    NewArray = NewArray.concat(MaxP_to_rest);
    refinedData.push(NewArray); })

	var modcsvContent = '--csv--\n'
	refinedData.forEach(row => {modcsvContent += row.join(',') + '\n'});
	modcsvContent+="\n--jsontree--\n"+ sections[2]+'\n'
	modcsvContent+="\n--othermetadata--\n"
	for (let line of metadataparsedlines){if(line.includes("threshrange1")){modcsvContent+=line+'\n'}
		if(line.includes("maxname")){modcsvContent+=line+'\n'}
		if(line.includes("treedimensions")){modcsvContent+=line+'\n'}}

	modcsvContent+='savemode,manual\n'
	modcsvContent+="subtreecolor,"+document.getElementById("nodessubtreeColorButton").value+'\n';
	modcsvContent+="clustperc,"+document.getElementById("Clustperc").value+'\n';
	modcsvContent+="LITmin,"+document.getElementById("LITmin").value+'\n';
	modcsvContent+="LITmax,"+document.getElementById("LITmax").value+'\n';
	modcsvContent+="terminalnodecolor,"+document.getElementById("nodesterminalColorButton").value+'\n';
	modcsvContent+="terminaltextcolor,"+document.getElementById("terminalTextColorButton").value+'\n';
	modcsvContent+="internnodetext,"+document.getElementById("nodeTextButton").value+'\n';
	modcsvContent+="internnodecolor,"+document.getElementById("nodeColorButton").value+'\n';
	modcsvContent += "maxpthreshold," + document.getElementById("maxPthreshold").value + '\n';

	const blob = new Blob([modcsvContent], { type: 'text/csv;charset=utf-8,' })
	const objUrl = URL.createObjectURL(blob)
	const link = document.createElement('a')
	link.setAttribute('href', objUrl)
	link.setAttribute('download', 'File.itv')
	link.textContent = 'Click to Download'
	document.body.appendChild(link); 
	link.click()
	link.remove();
}



function calculatematchratio(treedata,clustperc){
  const clustermembership=getclustermembership(treedata,clustperc)
  const clusterterminals={}
  Object.entries(clustermembership).forEach(([t,c])=>{if(!clusterterminals[c])clusterterminals[c]=[];clusterterminals[c].push(t)})

  const nclusters=Object.keys(clusterterminals).length
  const nterminals=Object.keys(clustermembership).length
  const terminalswithspecies=Object.keys(spname).filter(t=>spname[t])
  const nterminalswithspecies=terminalswithspecies.length
  const clusterswithspecies=Object.entries(clusterterminals).filter(([cid,ts])=>ts.some(t=>spname[t]))
  const nclusterswithspecies=clusterswithspecies.length

  let ncongruent=0
  let ncongruentspecimens=0
  const speciesused=new Set()

  clusterswithspecies.forEach(([cid,ts])=>{
    const specieslist=[...new Set(ts.map(t=>spname[t]).filter(Boolean))]
    if(specieslist.length===1){
      const species=specieslist[0]
      if(!speciesused.has(species)){
        const inothercluster=Object.entries(clusterterminals).some(([oid,ots])=>oid!==cid&&ots.some(t=>spname[t]===species))
        if(!inothercluster){
          ncongruent++
          speciesused.add(species)
          ncongruentspecimens+=ts.length
        }
      }
    }
  })
  const nspecies=new Set(Object.values(spname).filter(Boolean)).size
  const matchratio=(2*ncongruent)/(nclusterswithspecies+nspecies)
  const specimencongruence=nterminalswithspecies>0?ncongruentspecimens/nterminalswithspecies:0
  return{matchratio,specimencongruence,ncongruent,nclusters,nterminals,nterminalswithspecies,nclusterswithspecies,nspecies,ncongruentspecimens}
}

function calculatematchratio(treedata,clustperc){const clustermembership=getclustermembership(treedata,clustperc)
  const clusterterminals={}
  Object.entries(clustermembership).forEach(([t,c])=>{if(!clusterterminals[c])clusterterminals[c]=[];clusterterminals[c].push(t)})
  const terminals=treedata.leaves().map(n=>n.data.terminal||n.data.name)
  const nterminals=terminals.length
  const terminalswithspecies=terminals.filter(t=>spname[t]&&spname[t].trim()!=="")
  const nterminalswithspecies=terminalswithspecies.length
  const clusterswithspecies=Object.entries(clusterterminals)
    .filter(([cid,ts])=>ts.some(t=>spname[t]&&spname[t].trim()!==""))
  const nclusterswithspecies=clusterswithspecies.length
  const nclusters=Object.keys(clusterterminals).length
  let ncongruent=0
  let ncongruentspecimens=0
  const speciesused=new Set()
  clusterswithspecies.forEach(([cid,ts])=>{const specieslist=[...new Set(ts.map(t=>spname[t]).filter(s=>s&&s.trim()!==""))]
    if(specieslist.length===1){
      const species=specieslist[0]
      if(!speciesused.has(species)){
        const inothercluster=Object.entries(clusterterminals)
          .some(([oid,ots])=>oid!==cid&&ots.some(t=>spname[t]===species))
        if(!inothercluster){ncongruent++
          speciesused.add(species)
          ncongruentspecimens+=ts.filter(t=>spname[t]===species).length}}}})
  const nspecies=new Set(terminals.map(t=>spname[t]).filter(s=>s&&s.trim()!=="")).size
  const matchratio=(2*ncongruent)/(nclusterswithspecies+nspecies)
  const specimencongruence=nterminalswithspecies>0?ncongruentspecimens/nterminalswithspecies:0
  return{matchratio,specimencongruence,ncongruent,nclusters,nterminals,
    nterminalswithspecies,nclusterswithspecies,nspecies,ncongruentspecimens}
}

