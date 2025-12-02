import sys,fileinput,math,itertools,os,re
import basic_seq_handling as bsm
from PyQt5 import QtCore
import gc

def merge_two_dicts(x, y):
    z=x.copy()  
    z.update(y)   
    return z
def loadseqs(infilename):
    seqdict={}
    flag=0
    for line in fileinput.input([infilename]):
        if ">" in line:
            try:
                seqdict[seqID]=bsm.change_ext_gaps(sequence.upper())
            except UnboundLocalError:
                pass
            seqID=line.strip().replace(">", "")
            sequence=''
        else:
            try:
                sequence += line.strip()
            except:
                print("odd")
                flag=1
                break
    try:
        seqdict[seqID]=bsm.change_ext_gaps(sequence.upper())
    except:
        if flag == 0:
            print("odd")
    fileinput.close()
    return seqdict


class rungene(QtCore.QThread):
    notifyProgress=QtCore.pyqtSignal(int)
    notifyRange=QtCore.pyqtSignal(int)
    notifySwitch=QtCore.pyqtSignal(str)
    taskFinished=QtCore.pyqtSignal(str)
    def __init__(self, seqids, seqdict,indir,counts,seqiddict,infilename,minthresh,maxthresh,spassocs):
        super(rungene, self).__init__()
        self.seqids=seqids
        self.seqdict=seqdict
        self.indir=indir
        self.counts=counts
        self.seqiddict=seqiddict
        self.infilename=infilename
        self.minthresh=minthresh
        self.maxthresh=maxthresh
        self.spassocs=spassocs
        self._should_cancel=False
    def run(self):
        seqids=self.seqids
        indir=self.indir 
        counts=self.counts
        seqiddict=self.seqiddict
        infilename=self.infilename
        minthresh=self.minthresh
        maxthresh=self.maxthresh
        spassocs=self.spassocs
        safeids={}

        def countchildren(k,n,listn,masteriddict,terminals):
        #    print k
            if [k]!=masteriddict[k].keys():
                for item in masteriddict[k].keys():
                    if item not in terminals:
                        n,listn=countchildren(item,n,listn,masteriddict,terminals)
                    else:
                        n=n+1
                        listn.append(item)
            else:
                n+=1
            return n,listn

        def deletechildren(k,listn,masteriddict,terminals):
        #    print k
            if [k]!=masteriddict[k].keys():
                for item in masteriddict[k].keys():
                    if item not in terminals:
                        listn.append(item)
                        listn=deletechildren(item,listn,masteriddict,terminals)
                    else:
                        pass
            else:
                pass
            return listn
        def buildtree(tree):

            treeitems=tree.items()
            new={}
            for k,v in treeitems:
                newlist=[]
                newlistappend=newlist.append
                if len(v)>1:
                    v_sorted=sorted(v, key=lambda x: masterdictcount[x])
                    for item in v_sorted:
                        newlistappend(buildtree({item:masteriddict[item].keys()}))
                new[k]=newlist
            return new


        def keychange(tree,n,terminals,maxfp):

            newlist=[]
            newlistappend=newlist.append
            for c in tree:
                citems=c.items()
                new={}
                if isinstance(c, dict):
                    for k,v in citems:
                        if k in terminals:
                                new={"terminallabel": str(namesdict[k]), "terminal": safeids[k], "node_size":str(5), "children": keychange(v,n,terminals,maxfp), "yv": str(n+masterdictcount[k]//2*10), "xv":str(int(((maxfp-fusepoints[k])*10))) }
                        else:
                                new={"name": str(k),  "node_size":str(5), "fusepoint":str(fusepoints[k]), "children": keychange(v,n,terminals,maxfp), "yv": str(n+masterdictcount[k]//2*10), "xv":str(int(((maxfp-fusepoints[k])*10))) }
                        n+=masterdictcount[k]*10
                else:
                    new={"name": str(c)}
                    n+=10
                newlistappend (new)
            return newlist
        namesdict={int(k):seqiddict[k] for k in seqiddict.keys() }
        safeids={int(k):"terminal"+str(k) for k in seqiddict.keys()}
        print(seqids)
        specimeniddict={}
        internal_ids={i for i, name in namesdict.items() if not name.startswith("ext_")}
        external_ids={i for i, name in namesdict.items() if name.startswith("ext_")}

        for each in namesdict.keys():
            specimeniddict[each]=namesdict[each]
        #print "seqids",seqiddict
        dirlist=os.listdir(indir)
        cutoffs=[float(fname) for fname in dirlist if not fname.startswith(".") and fname.replace('.', '', 1).isdigit()]
        cutoffs.sort()
        masteriddict={}
        last_index={}
        uncollapsed={}
        maxindex=counts+1
        fusepoints={}
        terminals=[]
        masterdictcount={}
        maxps={}
        maxppairs={}
        for idn in seqids:
            terminals+=[int(i) for i in idn]
            iddict={int(id):'' for id in idn}
            iddict3={int(id): 0.00 for id in idn}
            iddict2={int(id): {int(id): ''} for id in idn}
            if len(iddict)==1:
                fusepoints.update(iddict3)
                masteriddict.update(iddict2)
                last_index[int(idn[0])]=int(idn[0])
                uncollapsed[int(idn[0])]=iddict
                masterdictcount[int(idn[0])]=1
                maxps[int(idn[0])]=0
            else:
                fusepoints[maxindex]=float(0)
                masteriddict[maxindex]=iddict
                fusepoints.update(iddict3)
                masteriddict.update(iddict2)
                last_index[int(idn[0])]=maxindex
                maxps[maxindex]=0
                uncollapsed[maxindex]=iddict
                masterdictcount[maxindex]=len(iddict.keys())
                for each in iddict.keys():
                    masterdictcount[each]=1
                maxindex+=1
    #    print "laster",last_index
        donelist=[]
        print(last_index)

            
        self.notifyRange.emit(len(cutoffs))

        for i,cutoff in enumerate(cutoffs):
            print(cutoff)
            if self._should_cancel:
                return
            newindex={}
            reindexed={}
            tdone={}
            path = os.path.join(indir, f"{cutoff:.2f}")
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                for line in fh:
                    
                    status=''
                    m=line.strip().split('\t')
                    if last_index[int(m[0])]!=last_index[int(m[1])]:
                        temp=[last_index[int(m[0])], last_index[int(m[1])]]
                        temp.sort()
                        if temp not in donelist:
                            o1,o2=last_index[int(m[0])],last_index[int(m[1])]
                            donelist.append(temp)
                            try:
                                if reindexed[int(m[0])]<reindexed[int(m[1])]:
                                    newindex[reindexed[int(m[0])]].update(newindex[reindexed[int(m[1])]])
                                    uncollapsed[reindexed[int(m[0])]].update(uncollapsed[reindexed[int(m[1])]])
                                    masterdictcount[reindexed[int(m[0])]]+=masterdictcount[reindexed[int(m[1])]]
                                    k=reindexed[int(m[1])]
                                    for each in newindex[reindexed[int(m[1])]].keys():
                                        reindexed[each],last_index[each]=reindexed[int(m[0])],reindexed[int(m[0])]
                                    newindex.pop(k)
                                    for each in uncollapsed[reindexed[int(m[1])]]:
                                        reindexed[each]=reindexed[int(m[0])]
                                        last_index[each]=reindexed[int(m[0])]
                                        maxps[reindexed[int(m[0])]]=cutoff
                                        id0=int(m[0]); id1=int(m[1])
                                        if id0 in internal_ids and id1 in internal_ids:
                                            maxppairs[reindexed[int(m[0])]]=[m[0],m[1]]
                                else:
                                    newindex[reindexed[int(m[1])]].update(newindex[reindexed[int(m[0])]])
                                    uncollapsed[reindexed[int(m[1])]].update(uncollapsed[reindexed[int(m[0])]])
                                    masterdictcount[reindexed[int(m[1])]]+=masterdictcount[reindexed[int(m[0])]]
                                    k=reindexed[int(m[0])]
                                    for each in newindex[reindexed[int(m[0])]].keys():
                                        reindexed[each], last_index[each]=reindexed[int(m[1])], reindexed[int(m[1])]
                                    newindex.pop(k)
                                    for each in uncollapsed[reindexed[int(m[0])]]:
                                        reindexed[each]=reindexed[int(m[1])]
                                        last_index[each]=reindexed[int(m[1])]
                                        maxps[reindexed[int(m[1])]]=cutoff
                                        id0=int(m[0]); id1=int(m[1])
                                        if id0 in internal_ids and id1 in internal_ids:
                                            maxppairs[reindexed[int(m[1])]]=[m[0],m[1]]
                                status="T1"
                            #        print line.strip(),"T1",newindex,last_index
                            except KeyError:
                                try:
                                    newindex[reindexed[int(m[0])]][last_index[int(m[1])]]=''
                                    uncollapsed[reindexed[int(m[0])]].update(uncollapsed[last_index[int(m[1])]])
                                    masterdictcount[reindexed[int(m[0])]]+=masterdictcount[last_index[int(m[1])]]
                                    for each in uncollapsed[last_index[int(m[1])]]:
                                        reindexed[each]=reindexed[int(m[0])]
                                        last_index[each]=reindexed[int(m[0])]
                                        maxps[reindexed[int(m[0])]]=cutoff
                                        id0=int(m[0]); id1=int(m[1])
                                        if id0 in internal_ids and id1 in internal_ids:
                                            maxppairs[reindexed[int(m[0])]]=[m[0],m[1]]
                                    status="T2"
                            #        print line.strip(),"T2", newindex,last_index
                                except KeyError:
                                    try:
                                        newindex[reindexed[int(m[1])]][last_index[int(m[0])]]=''
                                        uncollapsed[reindexed[int(m[1])]].update(uncollapsed[last_index[int(m[0])]])
                                        masterdictcount[reindexed[int(m[1])]]+=masterdictcount[last_index[int(m[0])]]
                                        for each in uncollapsed[last_index[int(m[0])]]:
                                            reindexed[each]=reindexed[int(m[1])]
                                            last_index[each]=reindexed[int(m[1])]
                                            maxps[reindexed[int(m[1])]]=cutoff
                                            id0=int(m[0]); id1=int(m[1])
                                            if id0 in internal_ids and id1 in internal_ids:
                                                maxppairs[reindexed[int(m[1])]]=[m[0],m[1]]
                                        status="T3"
                            #            print line.strip(),"T3",newindex,last_index
                                    except KeyError:

                                        newindex[maxindex]={last_index[int(m[0])]:'',last_index[int(m[1])]:''}
                                        uncollapsed[maxindex]=merge_two_dicts(uncollapsed[last_index[int(m[1])]],uncollapsed[last_index[int(m[0])]])
                                        masterdictcount[maxindex]=masterdictcount[last_index[int(m[1])]]+masterdictcount[last_index[int(m[0])]]
                                        uncollapsed.pop(last_index[int(m[1])])
                                        uncollapsed.pop(last_index[int(m[0])])

                                        for each in uncollapsed[maxindex]:
                                            reindexed[each]=maxindex
                                            last_index[each]=maxindex
                                            maxps[maxindex]=cutoff
                                            id0=int(m[0]); id1=int(m[1])
                                            if id0 in internal_ids and id1 in internal_ids:
                                                maxppairs[maxindex]=[m[0],m[1]]
                                        maxindex+=1
                                        status="T4"


                            fusepoints[reindexed[int(m[0])]]=cutoff
                    else:
                        maxps[last_index[int(m[0])]]=cutoff
                        id0=int(m[0]); id1=int(m[1])
                        if id0 in internal_ids and id1 in internal_ids:
                            maxppairs[last_index[int(m[0])]]=[m[0],m[1]]
            masteriddict.update(newindex)
            self.notifyProgress.emit(i+1)
        print("clustered")
        self.notifySwitch.emit("Clustering completed; building cluster fusion diagram")
        self.notifyRange.emit(0)
        QtCore.QCoreApplication.processEvents(QtCore.QEventLoop.AllEvents, 50)
        QtCore.QThread.msleep(100) 

        fusepoints_percs={}
        for each in fusepoints.keys():
            fusepoints_percs[fusepoints[each]]=''
        cutoffs=list(fusepoints_percs.keys())
        cutoffs.sort()

        masterdicttree={max(masteriddict.keys()):masteriddict[max(masteriddict.keys())].keys()}

        masterdictterminals={}
        for each in masteriddict.keys():
            masterdictterminals[each]=0

        masterdicttree1=buildtree(masterdicttree)
        max_fp=max(fusepoints.values()) if fusepoints else 0.0
        n=0
        masterdicttree2=keychange([masterdicttree1],n,terminals,max_fp)
        self.notifySwitch.emit("Writing outputs")

        clustersizes={}
        allclusts_children={}
        allclusts_mincode={}
        parent={}
        valid_nodes={}

        def process_node(node, parent_id=None):
            if parent_id is not None:
                parent[node]=parent_id
            if node in terminals:
                clustersizes[node]=1
                allclusts_children[node]=[node]
                allclusts_mincode[node]=specimeniddict[node]
                return [node]
            members=[]
            for c in masteriddict[node].keys():
                if c==node:  
                    continue
                members.extend(process_node(c, node))
            clustersizes[node]=len(members)
            allclusts_children[node]=members
            allclusts_mincode[node]=min(specimeniddict[x] for x in members) if members else ""
            return members
        root=max(masteriddict.keys())
        process_node(root, None)
        specimens_by_clusts={name: {} for name in namesdict.keys()}
        clusts_by_thresh_all={}
        if 0 not in cutoffs:
            cutoffs=[0] + cutoffs
        INF=float('inf')
        parent_fp={node: (fusepoints[parent[node]] if node in parent else INF)
                     for node in masteriddict.keys()}

        outfile=open(os.path.join("cluster",infilename + "_clusterlist"), 'w')
        for n in cutoffs:
            if self._should_cancel:
                return

            active_nodes=[node for node in allclusts_children.keys()
                            if fusepoints.get(node, 0.0) <= n < parent_fp.get(node, INF)]

            active_nodes.sort(reverse=True)

            clusts_by_thresh2={}
            for node in active_nodes:
                members=allclusts_children[node]
                clusts_by_thresh2[node]=[namesdict[m] for m in members]
                valid_nodes[node]=''
                for m in members:
                    specimens_by_clusts[m][n]=node

            outfile.write(str(n) + " : " + str(len(clusts_by_thresh2)) + " : " + str(clusts_by_thresh2) + '\n')
            clusts_by_thresh_all[n]=clusts_by_thresh2

        outfile.close()

        rephaps={}
        for clust, children in allclusts_children.items():
            if clust not in terminals:
                haplist={}
                for each in children:
                    if each not in internal_ids:
                        continue 
                    hapcode=specimens_by_clusts[each][0]
                    haplist[hapcode]=haplist.get(hapcode, 0) + 1
                if haplist:
                    maxhap=max(haplist.values())
                    for each in children:
                        if each not in internal_ids:
                            continue
                        hapcode=specimens_by_clusts[each][0]
                        if haplist[hapcode] == maxhap:
                            rephaps[clust]=allclusts_mincode[hapcode]



        LITthresh=3
        for thresh in cutoffs:
            if float(thresh)<=LITthresh:
                LITthresh2=thresh
                if float(thresh)<=1: 
                    LITminthresh=thresh
            else:
                pass


        with open(infilename.split(".")[0]+".itv",'w') as outfile:
            outfile.write("--csv--\n")
            outfile.write(",".join(["Name","TerminalLabel","Type","SpName","Fusepoint","xv","yv","NodeStat","TextStat","Disabled","NodeText","Sex","Hap","MaxP","MaxPairs","Hapreps","Sequence","Notes"]))

            outfile.write('\n')
            for each in terminals:
                outfile.write(','.join([safeids[each],'"'+namesdict[each]+'"',"Terminal",spassocs[str(each)],"0",str(int(((max(fusepoints.values())-fusepoints[each])*10))),str(n+masterdictcount[each]/2*10),"#ffffff","","0","","",'"'+allclusts_mincode[specimens_by_clusts[each][0]]+'"',"","","",self.seqdict[namesdict[each]],""]))
                outfile.write('\n')

            for each in valid_nodes.keys():
                if each not in terminals:
                    try:

                        outfile.write(','.join(['"'+str(each)+'"',"","Internal","",str(fusepoints[each]),str(int(((max(fusepoints.values())-fusepoints[each])*10))),str(n+masterdictcount[each]/2*10),"#ffffff","","0","","","",str(maxps[each]),safeids[int(maxppairs[each][0])]+":"+safeids[int(maxppairs[each][1])],'"'+rephaps.get(each,"")+'"',"",""]))
                    except KeyError:
                        outfile.write(','.join(['"'+str(each)+'"',"","Internal","",str(fusepoints[each]),str(int(((max(fusepoints.values())-fusepoints[each])*10))),str(n+masterdictcount[each]/2*10),"#ffffff","","0","","","",str(maxps[each]),"",'"'+rephaps.get(each,"")+'"',"",""]))

                                            
                    outfile.write('\n')
            outfile.write('\n--jsontree--\n')
            treestring=str(masterdicttree2)
            treestring=treestring.replace('\'','\"')
            treestring=treestring.replace('\\\\','/')

            treestring=str(masterdicttree2)
            treestring=treestring.replace('\'','\"')
            treestring=treestring.replace('\\\\','/')
            outfile.write(treestring[1:-1])
            outfile.write('\n\n--othermetadata--\n')

            outfile.write("threshrange1")

            for thresh in cutoffs:
                if thresh in clusts_by_thresh_all.keys():
                    outfile.write(","+str(thresh))
            outfile.write("\n")

            maxname=""
            for name in namesdict.values():
                if len(name)>len(maxname):
                    maxname=name
            outfile.write("maxname,"+maxname+'\n')
            treedimensions=[len(terminals)*10,max(fusepoints.values())*10,maxname]
            outfile.write("treedimensions,"+treedimensions[2]+'\n')
            outfile.write("savemode,default\n")
            outfile.write("LITmax,"+str(LITthresh2)+'\n')
            outfile.write("LITmin,"+str(LITminthresh)+'\n')
            outfile.write("clustperc,"+str(LITthresh2)+'\n')

        self.taskFinished.emit("done")
