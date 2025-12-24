

function pop(){
   return prompt("Enter species name!", "Text");
}

function rgbtohex(rgb){
    let rgbValues=rgb.match(/\d+/g); 
    return "#"+rgbValues.map(x=>Number(x).toString(16).padStart(2,"0")).join("");
}

function renderterminallabel(d){
    const sexsymbol=d.data.sex==="m"?"\u2642":d.data.sex==="f"?"\u2640":"";
    const slidesymbol=d.data.slideMounted?"\u29C9":"";
    return terminallabelshort[d.data.terminal]+(d.data.spname?"_"+d.data.spname:"")+sexsymbol+slidesymbol;
}
function findClickedNode(i, elm) {
  if (!i || !i.data || !elm || !elm.id) return null;
  return i.data.descendants().find(d =>
    ("circleid" + (d.data.terminal || d.data.name) + "id") === elm.id
  ) || null;
}
function getcolorbynodestat(nodestat){
    if (nodestat==="v"){return "#009933"; // Green
    }else if(nodestat==="spi"){return "#FF0000"; // Red
    }else if(nodestat==="snpi"){return "#1F83F3"; // Blue
    }else if(nodestat==="npi"){return "#FF0000"; // Red
    }else if(nodestat==="nnpi"){return "#1F83F3"; // Blue
    }else if(nodestat==="c"){return "#008000"; // Blue
    }else if(nodestat==="s"){return "#808080"; // Red
    }else if(nodestat==="l"){return "#FFA500"; // Blue
    }else if (nodestat === "vsub") { return "#009933"; 
  }else{return "#FFFFFF";}
}

function getdescendants(node){let descs=[node]
  function getchildschildren(node){
    if(!node.children){return [];}
     node.children.forEach(function(d){
     descs=descs.concat(d); descs.concat(getchildschildren(d));
    });return descs;}
   return getchildschildren(node);
  }
  
function gettextwidth(text,font){var canvas=gettextwidth.canvas||(gettextwidth.canvas=document.createElement("canvas"));
    var context=canvas.getContext("2d");
    context.font=font;
    var metrics=context.measureText(text);
    return metrics.width;
};

function listdescendants(node){if(node&&typeof node.descendants==='function'){return node.descendants();}
  return getDescendants(node)||[];
}

function rendernotes(d,localsvg){const id=d.data.terminal||d.data.name;
  d3.select("#noteicon"+id+"id").remove();
  if(!d.data.note||!d.data.note.trim())return;
  function clickhandler(e){e.stopPropagation();
    const newnote=prompt("Edit note:",d.data.note||"");
    if(newnote!==null&&newnote.trim()!==d.data.note){d.data.note=newnote.trim();
      rendernotes(d,localsvg);}}
  if(d.data.terminal){var txt=d3.select("#terminaltext"+id+"id");
    if(!txt.empty()){txt.append("tspan")
        .attr("id","noteicon"+id+"id")
        .attr("dx",6)
        .attr("dy",0)
        .style("cursor","pointer")
        .text("\u{1F5D2}")
        .on("click",clickhandler);
      return;}}
  var g=d3.select("#termid"+id+"id");
  if(g.empty()){var c=localsvg.select("#circleid"+id+"id");
    if(c.empty())return;
    var p=c.node()?c.node().parentNode:null;
    if(!p)return;
    g=d3.select(p);}
  g.append("text")
   .attr("id","noteicon"+id+"id")
   .attr("x",12)
   .attr("y",-8)
   .attr("font-size","14px")
   .attr("cursor","pointer")
   .text("\u{1F5D2}")
   .on("click",clickhandler);
  }
function linkKeyByNodes(s,t){
  const sid=s.data.terminal||s.data.name, tid=t.data.terminal||t.data.name;
  return "linkid"+sid+"_"+tid;
}


