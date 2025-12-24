function contextmenu_terminal(){d3.contextmenuterminal=function(menu,open){d3.selectAll('.d3-context-menu').data([1])
  .enter()
  .append('div')
  .attr('class','d3-context-menu');
  d3.select('body').on('click.d3-context-menu',function(){d3.select('.d3-context-menu').style('display','none');});
  return function(event,index,elm){event.preventDefault();
    event.stopPropagation();  
    menu.forEach(function(option){if(index.data.frozen&&option.title !== "Freeze/Unfreeze"){option.disabled=true;}else{option.disabled=false;}});
    d3.selectAll('.d3-context-menu').html('');
    var list=d3.selectAll('.d3-context-menu').append('ul');
  list.selectAll('li')
    .data(menu)
    .enter()
    .append('li')
    .attr('class',d=>d.disabled?'disabled':'')
    .style('color',d=>d.disabled?'#A0A0A0':'#000000')
    .style('pointer-events',d=>d.disabled?'none':'auto')
    .html(d=>d.children?`${d.title} &#9656;`:d.title)
    .on('mouseover',function(event,d){d3.selectAll('.d3-submenu').remove();
    if(d.children){const listelement=this;
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
        const clickednode=nodes.find(d => "circleid"+d.data.terminal+"id"===elm.id);
        if (!clickednode || !clickednode.data.terminal) return;
        const id=clickednode.data.terminal;
        const name=terminallabel[id] || id;
        const seq=i.sequence[id];
        const isBoldView=i.title.includes("BOLD-View");
        const fasta=isBoldView?seq:`>${name}\n${seq}`;
        navigator.clipboard.writeText(fasta).then(()=>{let url=null;
        let message="Sequence copied to clipboard.";
        if(i.title.includes("BOLD")&&!i.title.includes("View")){url="https://id.boldsystems.org/";
          message+="\nPaste it into BOLD and search.";}
        else if (i.title.includes("NCBI")){url="https://blast.ncbi.nlm.nih.gov/Blast.cgi?PROGRAM=blastn&PAGE_TYPE=BlastSearch&LINK_LOC=blasthome";
          message+="\nPaste it into NCBI BLAST and run the search.";}
        else if (i.title.includes("BOLD-View")){url="https://bold-view-bf2dfe9b0db3.herokuapp.com/blast";
          message+="\nPaste it into BOLD-View and click Search.";}
        else if(i.title.includes("GBIF")) {url="https://www.gbif.org/tools/sequence-id";
          message+="\nPaste it into GBIF Sequence ID tool.";}
          alert(message);
          if (url) window.open(url,"_blank");});});}})
      .on('click', function(d2, i) {
  if (i.disabled) return;

if (i.title === "Copy Fasta Sequence") {
  const nodes = i.data.descendants();
  const clickedNode = nodes.find(d => "circleid" + d.data.terminal + "id" === elm.id);
  if (!clickedNode || !clickedNode.data.terminal) return;
  const id = clickedNode.data.terminal;
  const name = terminallabel[id] || id;
  const seq = i.sequence[id];

  if (seq && seq.length > 2) {
    const fasta = `>${name}\n${seq}`;
    navigator.clipboard.writeText(fasta)
      .then(() => {
        alert(`FASTA sequence for "${name}" copied to clipboard.`);
      })
      .catch(err => {
        console.error("Clipboard error:", err);
        alert("Could not copy sequence to clipboard.");
      });
  } else {
    alert("No sequence data found for this terminal.");
  }
  d3.select('.d3-context-menu').style('display', 'none');
  return;
}


  const d = i.data.descendants().find(n =>
    ("circleid" + (n.data.terminal || n.data.name) + "id") === elm.id
  );
  if (!d) return;
  switch (i.title) {
    case "Set as Verified":
      setasverified(d, "o");
      break;
    case "Cannot be verified":
      d.data.textstat = "cnv";
      cannotbeverified(d, i);
      break;
    case "Set as Contamination":
      setascontamination(d, i);
      break;
    case "Set as Male":
      setasmalefemale(d, "m");
      break;
    case "Set as Female":
      setasmalefemale(d, "f");
      break;
    case "Set as Holotype":
      d.data.spname = i.spnames[d.data.terminal];
      setasverified(d, "h");
      break;
    case "Set as Slide Mounted Specimen":
      d.data.spname = i.spnames[d.data.terminal];
      setasverified(d, "s");
      break;
    case "Edit/Enter species name":
      const speciesnew = pop();
      if (speciesnew) {
        setspeciesname(d, speciesnew);
        setasverified(d, "a", false);
      }
      break;
    case "Add notes":
      const note = prompt("Enter note:");
      if (note && note.trim()) {
        d.data.note = note.trim();
        rendernotes(d, i.localsvg);
      }
      break;
    case "Freeze/Unfreeze":
      const links = i.data.links();
      freezeunfreezenodes(d, i.localsvg, links, menu);
      break;
    case "Accept code as species name":
      acceptlowestcodeterminal(i, elm.id);
      break;
    case "Undo":
      undo(d, i);
      break;
  }

  d3.select('.d3-context-menu').style('display', 'none');
});

    if(open) open(index.data,index);
        d3.select('.d3-context-menu')
          .style('left',(event.pageX - 2)+'px')
          .style('top',(event.pageY - 2)+'px')
          .style('display','block');
          event.preventDefault();
          event.stopPropagation();};} 
}


