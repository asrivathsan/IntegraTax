---
layout: default
title: Home
permalink: /
nav_order: 0
---

# **Welcome to IntegraTax**

**IntegraTax** is a user-friendly software for clustering DNA sequences and an interactive workspace with dendrograms to support species delimitation and taxonomic research.

IntegraTax separates deterministic structure generation from interactive interpretation. Complete clustering hierarchies and distance information are generated once and preserved, while taxonomic decisions are made, revised, and recorded in an interactive workspace. This design supports iterative integrative taxonomy without fixing outcomes prematurely. As a result, it treats taxonomy as a local analytical workspace rather than a database-driven process. Computation produces a structural foundation, while interpretation, validation, and revision occur interactively and are stored with the project itself.

## Get Started

- [Install IntegraTax]({{ "/installation/" | relative_url }})  
- [How to use IntegraTax]({{ "/using/" | relative_url }}) 
- [Large-scale Integrative Taxonomy (LIT) Workflow]({{ "/lit/" | relative_url }})
- [Frequently Asked Questions]({{ "/FAQ/" | relative_url }})
- [About]({{ "/about/" | relative_url }})

## Main Functions

IntegraTax provides two core functions:

**1.** **Clustering** - Generates complete single-linkage hierarchies with information required for later taxonomic decisions. This information is preserved rather than collapsed into fixed clusters.

<br> An overview of clustering module implemented as IntegraTax executable
<br>

<img src="{{ '/assets/img/Overview.png' | relative_url }}" alt="Species Name File" width="700"><br>

**2.** **Taxonomy** - Displays the clusters and specimens as an interactive dendrogram (Cluster Fusion Diagram) that can be annotated by taxonomists.
<br>
Taxonomic reasoning in IntegraTax occurs in the interactive workspace itself. The browser layer performs constraint checks, instability assessment, decision tracking, and revision logic, rather than acting as a passive tree viewer.

<br> A snapshot of IntegraTaxViz.html
<br>

<img src="{{ '/assets/img/visualisationoverview.png' | relative_url }}" alt="Overview of Visualisation" width="700"> **NEEDS REPLACEMENT WITH SPART BUTTON**
