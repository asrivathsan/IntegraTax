

function setasverified(d,type,savestate=true) {if (isfrozenorinfrozenancestor(d)) return;
    if(savestate)savepreviousstate(d);
	if(d.data.textstat!=="cnv"){d3.select("#termid"+d.data.terminal+"id").select(".contaminant-x").remove();
	    d3.select("#circleid"+d.data.terminal+"id")
	        .style("stroke","#ccc")
	        .style("fill","#ffffff");
	    d3.select("#terminaltext"+d.data.terminal+"id")
	        .style("fill","green");
	    let terminalnode=d3.select("#termid"+d.data.terminal+"id");
	    terminalnode.select(".verified-checkmark").remove();
	    terminalnode.append("text")
	        .attr("class","verified-checkmark")
	        .attr("x",0)
	        .attr("y",0)
	        .attr("dy","0.35em")
	        .attr("text-anchor","middle")
	        .text("\u2713")
	        .style("fill","green")
	        .style("font-size","16px")
	        .style("font-weight","bold")
	        .style("pointer-events","none");
	    d.data.isVerified=true;
	    d.data.isContaminant=false;}
    if(type==="a"){d.data.textstat="va";} 
    else if(type==="o"){d.data.textstat="v";}
    else if(type==="h"){d3.select("#terminaltext"+d.data.terminal+"id").style("font-weight","bold");
        d.data.textstat="h";}
    else if(type==="s"){d3.select("#terminaltext"+d.data.terminal+"id").style("font-weight","bold");
        d.data.textstat="s";
        d.data.slideMounted=true;}
    else{d.data.slideMounted=false;}
    const label=renderterminallabel(d);
    d3.select("#terminaltext"+d.data.terminal+"id").text(label);
}


function cannotbeverified(d,savestate=true){if (isfrozenorinfrozenancestor(d)) return;
    if(savestate)savepreviousstate(d);
    d3.select("#circleid"+d.data.terminal+"id")
        .style("stroke","#ccc")
        .style("fill","#ccc");
    d3.select("#terminaltext"+d.data.terminal+"id")
        .style("fill","#ccc");
    d3.select("#termid"+d.data.terminal+"id").select(".verified-checkmark").remove();
    d3.select("#termid"+d.data.terminal+"id").select(".contaminant-x").remove();
    d.data.isVerified=false;
    d.data.isContaminant=false;
    d.data.textstat="cnv";
}

function setasmalefemale(d,sex,savestate=true){if (isfrozenorinfrozenancestor(d)) return;
    if(savestate) savepreviousstate(d);
    d.data.sex=sex;
    d.data.spname=d.data.spname || spname[d.data.terminal];
    spname[d.data.terminal]=d.data.spname;
    const label=renderterminallabel(d);
    d3.select("#terminaltext"+d.data.terminal+"id").text(label);
}

function setascontamination(d,savestate=true){if (isfrozenorinfrozenancestor(d)) return;
    if(savestate)savepreviousstate(d);
    d3.select("#termid"+d.data.terminal+"id").select(".verified-checkmark").remove();
    const label=renderterminallabel(d);
    d3.select("#circleid"+d.data.terminal+"id")
        .style("stroke","#ccc")
        .style("fill","#ffffff");
    d3.select("#terminaltext"+d.data.terminal+"id")
        .html(`<tspan style="text-decoration: line-through;">${label}</tspan>`)
        .style("fill","#ccc");
    d3.select("#termid"+d.data.terminal+"id").select(".contaminant-x").remove();
    d3.select("#termid"+d.data.terminal+"id")
        .append("text")
        .attr("class","contaminant-x")
        .attr("x",0)
        .attr("dy","0.35em")
        .attr("text-anchor","middle")
        .text("X")
        .style("fill","red")
        .style("font-size","16px")
        .style("font-weight","bold")
        .style("pointer-events","none");
    d.data.isContaminant=true;
    d.data.isVerified=false;
    d.data.textstat="c";
}

function acceptlowestcodeterminal(i,elm){var nodes=i.data.descendants();
    var node=i.localsvg.selectAll("g.node")
        .data(nodes,function(d){if("circleid"+d.data.terminal+"id"===elm){
            const match=terminallabel[d.data.terminal].match(/[A-Z]+[0-9]+/i);
            if(!match) return;
            const speciesnew=match[0];
            setspeciesname(d,speciesnew);
            if(d.data.textstat=="cnv"){} 
            else if(d.data.isContaminant){}
            else{setasverified(d,"a",false);}}});
}

function marksubtreeasverified(d, data, localsvg) {
   savepreviousstate(d);  
  if (d.data.nodestat !== "v") {
    d.data.previousState = d.data.nodestat;
  }
  d.data.nodestat = "v";

  console.log("marksubtreeasverified → subtree-only recolor");
  updatesubtreecolor(d, data, localsvg);   
}


function assignspeciessubtree(matchednode,speciesname,data,localsvg){if(!matchednode) return;
  savepreviousstate(matchednode);
 if (subtreehasfrozen(matchednode)) {
  alert("This subtree contains frozen nodes. Unfreeze them before making changes.");
  return;}
  if (matchednode.data.nodestat!=="v") {matchednode.data.previousState=matchednode.data.nodestat;}
  matchednode.data.nodestat="v";
  matchednode.data.spname=speciesname;
  spname[matchednode.data.name]=speciesname;
  d3.select("#nodetext-"+matchednode.data.name)
    .text(speciesname)
    .style("fill","#009933");
  d3.select("#circleid"+matchednode.data.name+"id")
    .style("fill","#009933")
    .style("stroke","#ccc");
  const subtreenodes=getdescendants(matchednode);
  subtreenodes.push(matchednode); 
  subtreenodes.forEach(k => {
    if (!k.data.terminal) return;
    if (k.data.isContaminant) return;

    if (!k.data.stateHistory) k.data.stateHistory = [];
    savepreviousstate(k);
    k.data.spname = speciesname;
    spname[k.data.terminal] = speciesname;
    setspeciesname(k, speciesname, false);
    if (!hasTerminalStatus(k)) {
      d3.select("#terminaltext" + k.data.terminal + "id")
        .style("fill", "#009933")
        .style("text-decoration", "none");
    }
  });
  updatesubtreecolor(matchednode,data,localsvg);
  d3.select("#circleid"+window.root.data.name+"id").style("fill","#ffffff");
}


function setspeciesname(d,speciesnew,savestate=true){if (isfrozenorinfrozenancestor(d)) return;
    if(savestate) savepreviousstate(d);
    d.data.spname=speciesnew;
    spname[d.data.terminal]=speciesnew;
    const label=renderterminallabel(d);
    if(!d.data.isContaminant){
    d3.select("#terminaltext"+d.data.terminal+"id").text(label);}
    else{d3.select("#terminaltext"+d.data.terminal+"id").html(`<tspan style="text-decoration: line-through;">${label}</tspan>`)}
}
