import os, sys, re, argparse,functools
from collections import namedtuple
from scipy.stats import gaussian_kde
from scipy.signal import find_peaks
import numpy as np
import scipy
import edlib,logging
logger=logging.getLogger("edlib")

IUPAC={"A":{"A"}, "C":{"C"}, "G":{"G"}, "T":{"T"},"R":{"A","G"}, "Y":{"C","T"}, "S":{"G","C"}, "W":{"A","T"},"K":{"G","T"}, "M":{"A","C"},"B":{"C","G","T"}, "D":{"A","G","T"}, "H":{"A","C","T"}, "V":{"A","C","G"},"N":{"A","C","G","T"}}
def makeambpairs():
    pairs=set()
    def addpair(a,b):
        for x in a:
            for y in b:
                pairs.add((x,y))
                pairs.add((y,x))
    for amb,bases in IUPAC.items():
        for b in bases:
            addpair(amb,b)
    return sorted(pairs)

ambpairs = makeambpairs()

def plotdnormhist(dvals, thr, outprefix, suffix):
    if not dvals:
        return
    counts, edges=np.histogram(dvals, bins=60)
    outfile=outprefix+"."+suffix+"_hist.tsv"
    with open(outfile, "w") as out:
        out.write("bin_start\tbin_end\tcount\n")
        for i in range(len(counts)):
            out.write(str(edges[i])+"\t"+str(edges[i+1])+"\t"+str(counts[i])+"\n")
        out.write("# threshold\t"+str(round(thr, 6))+"\n")

def readfasta(infile):
    seqdict={}
    seqidlist=[]
    seqid=None
    seqs=[]
    with open(infile) as infile:
        for line in infile.readlines():
            line=line.strip()
            if not line: continue
            if ">" in line:
                if seqid is not None:
                    seqdict[seqid]="".join(seqs)
                    seqidlist.append(seqid)
                seqid=line[1:]
                seqs=[]
            else:
                seqs.append(line.upper())
    if seqid is not None:
        seqdict[seqid]="".join(seqs)
        seqidlist.append(seqid)
    return seqdict,seqidlist

def write_fasta(indict,outfile):
    with open(outfile,"w") as out:
        for seqid in indict:
            out.write(">"+seqid+"\n"+indict[seqid]+'\n')

def revcomp(seq):
    comp=str.maketrans("ACGTRYMKSWBDHVN","TGCAYRKMSWVHDBN")
    return seq.translate(comp)[::-1]
def count_N(s):
    return s.count("N")

def parse_cigar_counts(cigar):
    eq=0
    mm=0
    ins=0
    dele=0
    for each in re.findall(r"(\d+)([=XID])",cigar or ""):
        n=int(each[0]); op=each[1]
        if op=="=":
            eq+=n
        elif op=="X":
            mm+=n
        elif op=="I":
            ins+=n
        elif op=="D":
            dele+=n
    return {"=":eq,"X":mm,"I":ins,"D":dele}

def identity_gapmode5(dist,cigar,targetlen):
    counts=parse_cigar_counts(cigar)
    denom=targetlen+counts["I"]
    if denom<=0:
        return 0.0
    return max(0.0,1.0-(dist/float(denom)))

def edlib_hw_align(query,target):
    return edlib.align(query,target,mode="HW",task="path",additionalEqualities=ambpairs)

def map_revcomp_coords(origlen,startrc,endrc):
    startorig=(origlen-1)-endrc
    endorig=(origlen-1)-startrc
    return startorig,endorig

def min_distance_both_orients(query,subject):
    df=edlib.align(query,subject,mode="HW",task="distance",additionalEqualities=ambpairs)["editDistance"]
    subrc=revcomp(subject)
    dr=edlib.align(query,subrc,mode="HW",task="distance",additionalEqualities=ambpairs)["editDistance"]
    if dr<df:
        return ("-",df)
    else:
        return ("+",dr)

def getbreakpoint(values,bw="silverman",q_range=(0.001,0.999),minprom=0.05):
    v=np.asarray(values,float)
    v=v[np.isfinite(v)]
    if v.size<2:
        logger.info("Warning: Too few values for thresholding")
        return None
    lo,hi=np.quantile(v,q_range[0]),np.quantile(v,q_range[1])
    if not np.isfinite(lo) or not np.isfinite(hi) or lo==hi:
        lo,hi=float(v.min()),float(v.max())
    if lo==hi:
        logger.info("Warning: Zero variance in values, no breakpoint")
        return None
    try:
        kde=gaussian_kde(v,bw_method=bw)
        g=np.linspace(lo,hi,1024)
        d=kde(g)
    except Exception as e:
        logger.info("Warning: KDE failed",e)
        return None
    mode_idx=int(np.argmax(d))
    peak=float(d[mode_idx])
    valleys,_=find_peaks(-d,prominence=minprom*peak)
    rights=valleys[valleys>mode_idx]
    if rights.size:
        return float(g[rights[0]])
    if mode_idx+1<g.size:
        i=mode_idx+1+int(np.argmin(d[mode_idx+1:]))
        return float(g[i])
    logger.info("Warning: No antimode found in KDE")
    return None

def select_representatives(pass1kept,k=10):
    if not pass1kept:
        return []
    arr=sorted(pass1kept,key=lambda d:d["distprop"])
    if len(arr)<=k:
        return arr
    reps=[arr[0],arr[-1]]
    slots=k-2
    for i in range(1,slots+1):
        q=i/(slots+1.0)
        idx=int(round(q*(len(arr)-1)))
        reps.append(arr[idx])
    uniq=[]
    seen=set()
    for each in reps:
        sid=each["seqid"]
        if sid in seen:
            continue
        seen.add(sid)
        uniq.append(each)
    return uniq[:k]


def write_tsv(rows,header,outfile):
    with open(outfile,"w") as out:
        out.write("\t".join(header)+"\n")
        for each in rows:
            line=[]
            for h in header:
                line.append(str(each.get(h,"")))
            out.write("\t".join(line)+"\n")

def logprogress(prefix,i,total,logevery):
    if i==0 or (i%logevery!=0 and i!=total):
        return
    logger.info(f"[{prefix}] {i}/{total}")



def main():
    ap=argparse.ArgumentParser(description="edlib based homology search")
    ap.add_argument("fasta",help="Input FASTA")
    ap.add_argument("-o","--outprefix",default="out")
    ap.add_argument("--nprop",type=float,default=0.01)
    ap.add_argument("--nsecsample",type=int,default=10)
    ap.add_argument("--minlenfrac",type=float,default=0.75)
    ap.add_argument("--thresh1",type=float,default=None)
    ap.add_argument("--thresh2",type=float,default=None)
    ap.add_argument("--logevery",type=int,default=250)
    ap.add_argument("--bw", type=str, default="silverman")
    ap.add_argument("--qrange", type=str, default="0.001,0.999")
    ap.add_argument("--minprom", type=float, default=0.05)
    args=ap.parse_args()

    minprom=args.minprom
    outp=args.outprefix
    ql,qh=map(float, args.qrange.split(","))
    seqdict,seqidlist=readfasta(args.fasta)

    minlenfrac=args.minlenfrac
    nprop=args.nprop
    logevery=args.logevery
    nsecsample=args.nsecsample
    thresh1=args.thresh1
    thresh2=args.thresh2
    bw=args.bw
    if os.path.dirname(outp):
        os.makedirs(os.path.dirname(outp),exist_ok=True)
    
    logger.info("Read "+str(len(seqdict))+" sequences")

    if not seqdict:
        logger.info("No sequences"); sys.exit(1)
    cleaned={}
    for s in seqdict:
        seq=seqdict[s].replace("?","").replace("-","")
        cleaned[s]=seq
    seqdict=cleaned

    logger.info("After cleaning"+ str(len(seqdict))+" sequences")
    if not seqdict:
        logger.info("No sequences after cleaning"); sys.exit(1)
    firstid=seqidlist[0]
    firstseq=seqdict[firstid]
    firstlen=len(firstseq)
    if firstlen==0:
        logger.info("First sequence is empty after cleaning"); sys.exit(1)
    restseqs={}
    with open(outp+".nfilter.fa","w") as nout:
        nout.write(">"+firstid+"\n"+firstseq+'\n')
        total=len(seqdict)-1

        for i,id in enumerate(seqidlist[1:]):
            if len(seqdict[id])>=int(minlenfrac*firstlen) and count_N(seqdict[id])<=int(nprop*firstlen):
                restseqs[id]=seqdict[id]
                nout.write(">"+id+"\n"+seqdict[id]+'\n')
            logprogress("selected",i,total,logevery)

    logger.info(f"[filtering input] kept {len(restseqs)}/{len(seqdict)-1} in {outp}.nfilter.fa")
    if not restseqs: 
        sys.exit(0)


    orients={}
    orientfixed={}
    for seqid in restseqs:
        seq=restseqs[seqid]
        strand,dmin=min_distance_both_orients(firstseq,seq)
        if strand=="-":
            seq=revcomp(seq)
        orientfixed[seqid]=seq
        orients[seqid]=strand
    restseqs=orientfixed

    with open(outp+".orientations.tsv","w") as f:
        f.write("seqid\tstrand\n")
        for rid,strand in orients.items():
            f.write(rid+"\t"+strand+"\n")
    logger.info(f"[fixing orientations] orientations fixed for {len(restseqs)} sequences in {outp}.orientations.tsv")


    pass1stats=[]
    total=len(restseqs)
    for i,j in enumerate(list(restseqs.keys())):
        aln=edlib_hw_align(firstseq,restseqs[j])
        if aln is None or not aln.get("locations"):
            continue
        d=aln["editDistance"]
        start,end=aln["locations"][0]
        ident=identity_gapmode5(d,aln.get("cigar",""),firstlen)
        distprop=1.0-ident
        cov=(end-start+1)/float(firstlen)
        pass1stats.append({"seqid":j,"editdist":d,"identity":round(ident,6),"distprop":round(distprop,6),"start":start,"end":end,"cov":round(cov,6)})
        logprogress("pass1",i+1,total,logevery)
    logger.info(f"[pass1] aligned {len(pass1stats)} seqs")


    dvals1=[x["distprop"] for x in pass1stats]
    thr1 = thresh1 or getbreakpoint(dvals1, bw=bw, q_range=(ql,qh), minprom=minprom) or max(dvals1)
    logger.info(f"[pass1:threshold] {thr1}")
    plotdnormhist(dvals1,thr1,outp,"pass1")

    pass1filtered=[]
    pass1seqs={}
    for stats in pass1stats:
        if stats["distprop"]<=thr1 and stats["cov"]>=minlenfrac:
            pass1filtered.append(stats)
            pass1seqs[stats["seqid"]]=restseqs[stats["seqid"]]
    write_tsv(pass1filtered,["seqid","editdist","identity","distprop","start","end","cov"],outp+".pass1_hits.tsv")
    write_fasta(pass1seqs,outp+".pass1_homologs.fa")
    logger.info(f"[pass1:filter] {len(pass1filtered)}")

    if not pass1filtered: sys.exit(0)

    fulllen=[stats for stats in pass1filtered if (stats["end"]-stats["start"]+1)==firstlen]
    pass2refseqs={}
    if not fulllen:
        pass2refseqs[firstid]=firstseq
    else:
        reps=select_representatives(fulllen,k=nsecsample)
        for stats in reps:
            pass2refseqs[stats["seqid"]]=restseqs[stats['seqid']][stats["start"]:stats["end"]+1]
        pass2refseqs[firstid]=firstseq
    pass2refwins=[(seqid,pass2refseqs[seqid],len(pass2refseqs[seqid])) for seqid in pass2refseqs.keys()]
    write_fasta(pass2refseqs,outp+".pass1_reps_full.fa")
    logger.info(f"[reps] {len(pass2refseqs)} seeds for pass2")
    pass2stats=[]
    for i,seqid in enumerate(restseqs):
        best=None
        bestd=None
        bestrep=None
        bestlen=None
        for repid,repseq,replen in pass2refwins:
            aln=edlib_hw_align(repseq,restseqs[seqid])
            if aln is None or not aln.get("locations"): continue
            d=aln["editDistance"]
            if bestd is None or d<bestd:
                bestd=d
                best=aln
                bestrep=repid
                bestlen=replen
        if best is None:
            continue
        start,end=best["locations"][0]
        ident=identity_gapmode5(bestd,best.get("cigar",""),bestlen)
        distprop=1.0-ident
        cov=(end-start+1)/float(bestlen)
        pass2stats.append({"seqid":seqid,"editdist":bestd,"identity":round(ident,6),"distprop":round(distprop,6),"start":start,"end":end,"cov":round(cov,6)})
        logprogress("pass2",i+1,total,logevery)
    write_tsv(pass2stats,["seqid","editdist","identity","distprop","start","end","cov"],outp+".pass2_hits.tsv")
    logger.info(f"[pass2] scanned {len(restseqs)} seqs")

    dvals2=[stats["distprop"] for stats in pass2stats if np.isfinite(stats["distprop"])]
    thr2 = thresh2 or getbreakpoint(dvals2, bw=bw,q_range=(ql, qh), minprom=minprom) or (max(dvals2) if dvals2 else None)

    if thr2 is not None:
        logger.info(f"[pass2:threshold] {thr2}")
        plotdnormhist(dvals2,thr2,outp,"pass2")
    pass2seqs={}
    if thr2 is not None:
        for r in pass2stats:
            if r["distprop"]<=thr2 and r["cov"]>=minlenfrac:
                window=restseqs[r["seqid"]][r["start"]:r["end"]+1]
                pass2seqs[r["seqid"]]=window
        write_fasta(pass2seqs,outp+".pass2_homologs.fa")
        logger.info(f"[pass2:keep] {len(pass2seqs)}")
    else:
        logger.info("[pass2:keep] none (no threshold)")
    finalfa={}
    doneset=set()
    for stats in pass1filtered:
        if stats["seqid"] not in doneset:
            doneset.add(stats["seqid"])
            finalfa[stats["seqid"]]=restseqs[stats["seqid"]][stats["start"]:stats["end"]+1]
    for seqid in pass2seqs.keys():
        if seqid not in doneset:
            doneset.add(seqid)
            finalfa[seqid]=pass2seqs[seqid]
    finalfa[firstid]=firstseq
    write_fasta(finalfa,outp+".final.fa")

    finalids=set(list(finalfa.keys()))
    excluded={}
    for seqid in seqdict.keys():
        if seqid not in finalids:
            excluded[seqid]=seqdict[seqid]
    write_fasta(excluded,outp+".excluded.original.fa")

    logger.info(f" {outp}.nfilter.fa")
    logger.info(f" {outp}.pass1_hits.tsv")
    logger.info(f" {outp}.pass1_homologs.fa")
    logger.info(f" {outp}.pass1_reps_full.fa")
    logger.info(f" {outp}.pass2_hits.tsv")
    if pass2seqs:
        logger.info(f" {outp}.pass2_homologs.fa")
    logger.info(f" {outp}.final.fa")
    logger.info(f" {outp}.excluded.original.fa")
    logger.info(f" {outp}.orientations.tsv")


if __name__ == "__main__":
    main()
