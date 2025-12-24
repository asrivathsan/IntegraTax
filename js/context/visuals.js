function isfrozenorinfrozenancestor(node){let p = node;
    while (p){if(p.data&&p.data.frozen) return true;
    p = p.parent;}
    return false;
}

function subtreehasfrozen(node){return listdescendants(node).some(n=>n&&n.data&&n.data.frozen);
}


function updatecontextmenuterminals(d){d3.selectAll('.d3-context-menu li')
        .each(function(option){if(d.frozen&&option.title!=="Freeze/Unfreeze"){d3.select(this)
        .classed("disabled", true)
        .style("color", "#A0A0A0")
        .style("pointer-events", "none");}else{d3.select(this)
        .classed("disabled", false)
        .style("color", "#000000")
        .style('stroke-width', 1)
        .style("pointer-events", "auto");}});
}


function updatecontextmenu(d){d3.selectAll('.d3-context-menu li').each(function(option){if(d.frozen&&option.title!=="Freeze/Unfreeze"){
    d3.select(this).classed("disabled",true)
        .style("color","#A0A0A0")
        .style("pointer-events", "none");}else{d3.select(this)
        .classed("disabled",false)
        .style("color","#000000")
        .style('stroke-width',1)
        .style("pointer-events","auto");}});
}

function updatesubtreecolor(d, data, localsvg) {
  console.log("updatesubtreeinsidecontext (subtree-only)");

  const desc = getdescendants(d);
  desc.push(d);

  const parentstat = d.data.nodestat;

  if (parentstat !== undefined) {
    const col = getcolorbynodestat(parentstat);

    desc.forEach(n => {
      const hasManual =
        n.data.textstat && ["v", "va", "c", "cnv", "h", "s"].includes(n.data.textstat);
      if (n.data.terminal && hasManual) return; 

      const id = n.data.name || n.data.terminal;
      d3.select("#circleid" + id + "id").style("fill", col);
      if (n.data.terminal)
        d3.select("#terminaltext" + id + "id").style("fill", col);
    });
  } else {
    desc.forEach(n => {
      const id = n.data.name || n.data.terminal;
      d3.select("#circleid" + id + "id").style("fill", "#FFFFFF");
    });

    desc.forEach(n => {
      if (n.data.nodestat !== undefined) {
        const nc = getcolorbynodestat(n.data.nodestat);
        const sub = getdescendants(n);
        sub.push(n);
        sub.forEach(c => {
          const cid = c.data.name || c.data.terminal;
          d3.select("#circleid" + cid + "id").style("fill", nc);
          if (c.data.terminal)
            d3.select("#terminaltext" + cid + "id").style("fill", nc);
        });
      }
    });
  }

  const subtree = new Set();
  (function collect(node) {
    subtree.add(node);
    if (node.children) node.children.forEach(collect);
  })(d);

  localsvg
    .selectAll("path.link")
    .filter(l => subtree.has(l.source))
    .style("stroke", "#009933")
    .style("stroke-width", 5);
}

function colorlinks_for_verified_subtree(d, localsvg) {
  const subtree = new Set();
  (function collect(n) {
    subtree.add(n);
    if (n.children) n.children.forEach(collect);
  })(d);
  localsvg.selectAll("path.link")
    .filter(function(l) { return subtree.has(l.source); })
    .style("stroke", "#009933")
    .style("stroke-width", 5);
}

function togglefreezestate(d,elm){if(!elm||!elm.id){
    return;}
    d.frozen=!d.frozen;
    var isNowFrozen=d.frozen;
    var frozenColor="#808080";
    var unfrozenColor="#FFFFFF";
    d3.select("#"+elm.id)
        .transition()
        .duration(300)
        .style("fill",isNowFrozen?frozenColor:unfrozenColor);
    updatecontextmenu(d);
}

function freezeunfreezenodes(d,i,links,menu){
    d.data.frozen=!d.data.frozen;
    var isnowfrozen=d.data.frozen; 
    frozennodes=getdescendants(d);
    frozennodes.push(d); 
    var frozenColor="#808080"; 
    var textColor=isnowfrozen?"#A0A0A0":"#000000";

    frozennodes.forEach(function(k){k.data.frozen = isnowfrozen;if (isnowfrozen){if (k.data.originalTextstat === undefined) { k.data.originalTextstat = k.data.textstat; }} else {
        if (k.data.originalTextstat !== undefined) {k.data.textstat = k.data.originalTextstat;delete k.data.originalTextstat;}}
        d3.select("#circleid"+k.data.name+"id").each(function(){if(isnowfrozen){if(!k.data.originalColor){k.data.originalColor=d3.select(this).style("fill");}
        d3.select(this)
            .transition()
            .duration(300)
            .style("fill",frozenColor);}else{d3.select(this)
            .transition()
            .duration(300)
            .style("fill", k.data.originalColor || getcolorbynodestat(k.data.nodestat) || "#FFFFFF");;}});

        if (k.data.terminal){d3.select("#circleid"+k.data.terminal+"id").each(function(){if(isnowfrozen){if(!k.data.originalColorTerminal){k.data.originalColorTerminal=d3.select(this).style("fill");}
	        d3.select(this)
	            .transition()
	            .duration(300)
	            .style("fill",frozenColor);}else{d3.select(this)
                .transition()
                .duration(300)
                .style("fill", k.data.originalColorTerminal || getcolorbynodestat(k.data.nodestat) || "#FFFFFF");;}});}
        d3.select("#fobject"+k.data.terminal+"id")
            .transition()
            .duration(300)
            .style("color",textColor)
            .style("pointer-events",isnowfrozen?"none":"auto");});
    i.selectAll("path.link")
        .data(links)
        .filter(function(link) {
            return frozennodes.includes(link.source)&&frozennodes.includes(link.target);})
        .each(function(link){let linkSelection=d3.select(this);
            if(isnowfrozen){console.log("freeze snapshot stroke",
            linkSelection.style("stroke"),
            "time", performance.now());if(!link.source.data.originalStroke){link.source.data.originalStroke=linkSelection.style("stroke");
            link.source.data.originalStrokeWidth=linkSelection.style("stroke-width");}
            linkSelection
                .transition()
                .duration(300)
                .style("stroke","#808080") 
                .style("stroke-width","5");}else{linkSelection.transition()
                    .duration(300)
                    .style("stroke",link.source.data.originalStroke||"#000000")
                    .style("stroke-width",link.source.data.originalStrokeWidth||"1");}});
    d3.select("#circleid"+root.data.name+"id")
        .style("fill","#ffffff");
    d.data.frozen=isnowfrozen;
    menu.forEach(function(option){if(d.data.frozen&&option.title!=="Freeze/Unfreeze"){option.disabled=true;}else{option.disabled=false;}});
}
