---
layout: default
title: FAQ
nav_order: 4
has_children: false
permalink: /FAQ/
has_toc: false
---

# **Frequently Asked Questions**

## **Table of Contents**

- [Installation](#installation)
- [Clustering](#clustering)
- [Visualisation](#visualisation)
- [LIT](#lit)

---

## **Installation**

### Why can't I open IntegraTax on macOS?

Didn't read the Installation page huh? ;) [Click here to resolve the issue.]({{ "/installation/" | relative_url }})

---

## **Clustering**

### What does the minimum overlap do and should I change it?
The minimum overlap ensures that your input sequences have at least in default 100bp of overlap. 
If there are non overlapping sequences, it will be impossible to calculate the pairwise distances. 
Hence, this measure ensures that only alignments with certain overlap will be used. The default of 100bp 
should be sufficient for *COI* barcodes and we do not recommend changing it.

### Why am I constantly getting BLAST failed messages when I do a BLAST homology search?
Check if the fasta file name or folder names that the external sequences are in have special characters or spaces. If so, remove them and rerun the BLAST homology search.

---

## **Visualisation**

### How do I clear the html and restart the dendrogram visualisation?

Just click refresh and reload the `.itv` file in the Choose File button.

### My cluster only has a single haplotype. How do I use the right click options on the cluster node instead of the specimen node?
[Left-click]({{"/using/#right-click-options" | relative_url}}) the node and it will change the right-click options. Left-clicking again on the same node will revert the options.


---

## **LIT**

### How do I know what the alternative next most distant haplotype is if the current most distant haplotype cannot be verified and the other alternative haplotypes are of the same clustering threshold?
Currently, IntegraTax does not suggest the next most distant haplotype for checking. 
However, one could copy the sequences of the cluster and build a haplotype network to check which specimen/haplotype is the next most distant one.

---

## **Still have unanswered questions?**

Please raise an issue on our [github page](https://github.com/asrivathsan/IntegraTax)!

---



