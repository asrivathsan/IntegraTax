

function contextmenu_internal(){d3.contextmenu=function(menu,open){d3.selectAll('.d3-context-menu').data([1])
    .enter()
    .append('div')
    .attr('class','d3-context-menu');
    d3.select('body').on('click.d3-context-menu',function(){d3.select('.d3-context-menu').style('display','none');});
    return function(event,index,elm) {event.preventDefault();
    event.stopImmediatePropagation();   
	menu.forEach(function(option){if(index.data.frozen&&option.title!=="Freeze/Unfreeze") {
     	option.disabled=true;}else{option.disabled=false;}});
        d3.selectAll('.d3-context-menu').html('');
        var list=d3.selectAll('.d3-context-menu').append('ul');
	list.selectAll('li')
	  .data(menu)
	  .enter()
	  .append('li')
	  .attr('class',d => d.disabled?'disabled':'')
	  .style('color',d => d.disabled?'#A0A0A0':'#000000')
	  .style('pointer-events',d => d.disabled?'none':'auto')
	  .html(d => d.children?`${d.title} &#9656;`:d.title)
	.on('mouseover',function(event,d){d3.selectAll('.d3-submenu').remove();
	if (d.children){const listelement=this;
	    const submenu=d3.select('.d3-context-menu')
	      .append('ul')
	      .attr('class','d3-submenu')
	      .style('position','absolute')
	      .style('left',listelement.offsetLeft+listelement.offsetWidth+5+'px')
	      .style('top',listelement.offsetTop+'px')
	      .style('background','#fff')
	      .style('border','1px solid #ccc')
	      .style('padding','4px 0')
	      .style('list-style','none')
	      .style('z-index','1000');
    submenu.selectAll('li')
      .data(d.children)
      .enter()
      .append('li')
      .style('cursor','pointer')
      .style('padding','4px 12px')
      .text(child => child.title)
	.on('click',function(event,i){event.stopPropagation();
	  d3.select('.d3-context-menu').style('display','none');
	 const nodes=i.data.descendants();
	 const clickednode=nodes.find(d => "circleid"+d.data.name+"id"===elm.id);
	 if(!clickednode)return;
  const descendants=getdescendants(clickednode).filter(x => x.data.terminal);
  let fastalines=[];
  descendants.forEach(term=>{
    const id=term.data.terminal;
    const name=terminallabel[id]||id;
    const seq=i.sequence[id];
    if (!seq||seq.length<3) return;
    const isBoldView=i.title.includes("BOLD-View");
    const formatted=isBoldView?seq:`>${name}\n${seq}`;
    fastalines.push(formatted);});
  const output=fastalines.join("\n");
  navigator.clipboard.writeText(output).then(()=>{let url=null;
    let message="Terminal sequences copied to clipboard.";
    if (i.title.includes("BOLD")&&!i.title.includes("View")){url="https://id.boldsystems.org/";
      message += "\nPaste into BOLD Identification Engine.";}
    else if (i.title.includes("NCBI")){url="https://blast.ncbi.nlm.nih.gov/Blast.cgi?PROGRAM=blastn&PAGE_TYPE=BlastSearch&LINK_LOC=blasthome";
      message += "\nPaste into NCBI BLAST.";} 
    else if(i.title.includes("GBIF")){url="https://www.gbif.org/tools/sequence-id";
      message += "\nPaste into GBIF Sequence ID.";}
    alert(message);
    if (url) window.open(url,'_blank');});});}})
   .on('click',function(d2,i){if(!i.disabled){if(i.title=="Enter species name"){const speciesnew=pop();
		if (!speciesnew || !speciesnew.trim()) return;
 		const matchednode=i.data.descendants()
	    .find(d => "circleid"+d.data.name+"id" === elm.id);
	  	if (!matchednode) return;
	  	assignspeciessubtree(matchednode,speciesnew.trim(),i.data,i.localsvg);}
	if(i.title==="Export Fasta"){const nodes=i.data.descendants();
	    const clickednode=nodes.find(d => "circleid"+d.data.name+"id" === elm.id);
	    if(!clickednode) return;
	    const descendants=getdescendants(clickednode).filter(x => x.data.terminal);
	    const fastalines=[];
	    descendants.forEach(term=>{const id=term.data.terminal;
	        const name=terminallabel[id]||id;
	        const seq=i.sequence[id];
	        if (seq && seq.length>2){fastalines.push(`>${name}`);
	            fastalines.push(seq);}});

	    const blob=new Blob([fastalines.join("\n")],{ type: 'text/plain;charset=utf-8' });
	    const url=URL.createObjectURL(blob);
	    const a=document.createElement('a');
	    a.href=url;
	    a.download=(clickednode.data.name || "subtree")+"_sequences.fasta";
	    document.body.appendChild(a);
	    a.click();
	    document.body.removeChild(a);}

    if(i.title=="Undo"){undosubtree(i,elm.id);}
                        
	if(i.title=="Accept lowest code as species name"){const nodes=i.data.descendants();
	  const matchednode=nodes.find(d=>"circleid"+(d.data.terminal||d.data.name)+"id"===elm.id);
	  if(!matchednode) return;
	  const termlisttemp=matchednode.descendants()
	    .map(k=>terminallabel[k.data.terminal])
	    .filter(Boolean)
	    .map(name=>(name.match(/[A-Z]+[0-9]+/i)||[])[0])
	    .filter(Boolean)
	    .sort();
	  if(!termlisttemp.length) return;
	  const speciesnew=termlisttemp[0];
	  assignspeciessubtree(matchednode,speciesnew,i.data,i.localsvg);}
	  if(i.title=="Add notes"){const nodes=i.data.descendants();
		  const matchednode=nodes.find(d=>"circleid"+(d.data.terminal||d.data.name)+"id"===elm.id);
		  if(!matchednode)return;
		  const note=prompt("Enter note:");
		  if(!note||!note.trim())return;
		  matchednode.data.note=note.trim();
		  rendernotes(matchednode,i.localsvg);}
	if (typeof i.action === "function") {
  try {
    i.action(elm, i);
  } catch (err) {
    console.error("Menu action failed:", err);
  }
}	  
	if (i.title === "Freeze/Unfreeze") {
 const clicked = findClickedNode(i, elm);
   if (!clicked) return;
   const links = i.data.links();
   freezeunfreezenodes(clicked, i.localsvg, links, menu);
 }}
    d3.select('.d3-context-menu').style('display','none');});

    if(open) open(index.data,index);
        d3.select('.d3-context-menu')
            .style('left',(event.pageX - 2)+'px')
            .style('top',(event.pageY - 2)+'px')
            .style('display','block');
        event.preventDefault();
    event.stopPropagation();};}
}
