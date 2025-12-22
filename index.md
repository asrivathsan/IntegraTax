---
layout: default
title: Home
permalink: /
nav_order: 0
---

# **Welcome to IntegraTax**

**IntegraTax** is a user-friendly software for clustering DNA sequences and an interactive workspace with dendrograms to support species delimitation and taxonomic research.

IntegraTax separates hierarchical cluster generation from interactive interpretation. Clustering hierarchies and distance information are generated once and preserved, while taxonomic decisions are made, revised, and recorded in an interactive workspace. This design supports iterative integrative taxonomy without fixing outcomes prematurely. Revisions that occur interactively are stored with the project itself.

## Get Started

- [Install IntegraTax]({{ "/installation/" | relative_url }})  
- [How to use IntegraTax]({{ "/using/" | relative_url }}) 
- [Large-scale Integrative Taxonomy (LIT) Workflow]({{ "/lit/" | relative_url }})
- [Frequently Asked Questions]({{ "/FAQ/" | relative_url }})
- [About]({{ "/about/" | relative_url }})

## Main Functions

IntegraTax provides two core functions:

**1.** **Clustering** - Generates complete single-linkage hierarchies with information required for later taxonomic decisions. This information is preserved rather than collapsed into fixed clusters.
An overview of clustering module implemented as IntegraTax executable
<br>

<img src="{{ '/assets/img/Overview.png' | relative_url }}" alt="Species Name File" width="700"><br>

**2.** **Taxonomy** - An interactive workspace that displays the clusters and specimens as an dendrogram (Cluster Fusion Diagram) that can be annotated by taxonomists.
<br><br>
IntegraTax places taxon-relevant classification and summary calculations directly within the interactive workspace. Unstable clusters, LIT-based specimen groupings, congruence-based dendrogram colouring, alternative species hypotheses, and measures such as match ratios, specimen congruence, and SPART summaries are handled on the hierarchy itself, enabling progressive taxonomic decisions without reliance on external, stage-specific summaries.
<br> A snapshot of IntegraTaxViz.html
<br>

<img src="{{ '/assets/img/visualisationoverview.png' | relative_url }}" alt="Overview of Visualisation" width="700"> **NEEDS REPLACEMENT WITH SPART BUTTON**
