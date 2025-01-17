.. highlight:: none

.. _bkd-graphs-hypergraphs:

Background - Graphs and Hypergraphs
===================================

To understand the power of Synapse, it helps to have some additional background. Without delving into mathematical definitions, this section introduces key concepts related to a **hypergraph,** and contrasts them with those of a **graph** or a **directed graph.** Most people should be familiar with the concept of a graph – even if not in the strict mathematical sense – or with data that can be visually represented in graph form.

- `Graphs`_
- `Directed Graphs`_
- `Analysis with Graphs`_
- `Hypergraphs`_
- `Analysis with a Synapse Hypergraph`_
- `Conclusions`_

Graphs
------

A **graph** is a mathematical structure used to model pairwise relations between objects. Graphs consist of:

- **vertices** (or **nodes**) that represent objects, and
- **edges** that connect two vertices in some type of relationship.

|graph|

Edges are specifically pairwise or two-dimensional: an edge connects exactly two nodes. Both nodes and edges may have properties that describe their relevant features. In this sense both nodes and edges can be thought of as representational objects within the graph: nodes typically represent things ("nouns") and edges typically represent relationships ("verbs").

**Examples**

**Cities and Roads.** A simple example of data that can be represented by a graph are cities connected by roads. If abstracted into graph format, each city would be a vertex or node and a road connecting two cities would be an edge. Since you can travel from City A to City B or from City B to City A on the same road, the graph is **directionless** or **undirected.**

**Social Networks.** Another example is social networks based on "connections", such as Facebook or LinkedIn. In this case, each person would be a node and the connection between two people would be an edge. Because basic connections in these networks are mutual (you can’t "friend" someone on Facebook without them agreeing to "friend" you in return), it can be considered a directionless graph. (This is a simplification, but serves our purpose as an example.)

Directed Graphs
---------------

A **directed graph** is a graph where the edges have a direction associated with them. In other words, the relationship represented by the edge is one-way. Where an edge in an undirected graph is often represented by a straight line, an edge in a directed graph is represented by an arrow.

|directedgraph|

**Examples**

**Cities and Roads.** In our cities-and-roads example, the graph would be a directed graph if the roads were all one-way streets: in this case you can use a particular road to go from City A to City B, but not from City B to City A.

**Social Networks.** Social networks that support a "follows" relationship (such as Twitter) can be represented as directed graphs. Each person is still a node, but the "follows" relationship is one way – I can "follow" you, but you don’t have to follow me. If you choose to follow me, that would be a second, independent one-way edge in the opposite direction. (Again, this is a simplification but works for a basic illustration.)

**Other Examples.** Many other types of data can be represented with nodes and directed edges.  For example, in information security you can represent data and relationships such as:

``<malware_file> -- <performed DNS lookup for> --> <domain>``

or

``<domain> -- <has DNS A record for> --> <ip_address>``

In these examples, files, domains and IP addresses are nodes and "performed DNS lookup" or "has DNS A record" (i.e., "resolved to") are edges (relationships). The edges are directed because a malware binary can contain programming to resolve a domain name, but a domain can’t "perform a lookup" for a malware binary; the relationship (edge) is one-way.

In addition to nodes and edges, some directed graph implementations may allow labeling or tagging of nodes and edges with additional information. These tags can act as metadata for various purposes, such as to create analytically relevant groupings.

Many tools exist to visually represent various types of data in a directed graph format; Maltego (which bills itself as a "...tool that renders directed graphs for link analysis") is a well-known example.

Analysis with Graphs
--------------------

Directed graphs have become increasingly popular for representing and conducting analysis across large data sets. Analysis using a directed graph can be highly generalized into three methods for interacting with the data:

- **Lifting** or retrieving data. Lifting simply asks about and returns specific nodes or edges from the graph. For example, you can ask about the node representing your Twitter account or the node representing IP address 1.2.3.4. You can also ask about sets of nodes that share some common feature – for example, all of the Twitter users who signed up for the service in January 2014, or all the PE executables whose compile date is 6/19/1992.

- **Filtering** the results. Once you lift an initial data set (a node or set of nodes), filtering allows you to refine your results by including or excluding data based on some criteria. For example, once you have the set of Twitter users who signed up in January 2014, you may decide to exclude users who list their location as the United States. Similarly, once you have the set of files compiled on 6/19/1992, you can filter those results to only include files whose size is greater than 26576 bytes.

- **Traversing** the graph structure. Once you’ve lifted an initial data set, you can ask about relationships between your data set and other nodes by pathing (traversing) along the edges (relationships) that connect those nodes. For example, if you retrieve the node for your Twitter account, you can identify all of the accounts you are following on Twitter by traversing all of the "follows" edges from your node to the nodes of accounts that you follow. Similarly, if you retrieve the node for IP address 1.2.3.4, you can retrieve all of the domains that resolve to that IP by pathing backwards (remember, edges are directional) along the all of the "has DNS A record for" edges that point from various domains to that IP.

Some graph implementations may include a limited form of **pivoting** across nodes with like properties. Once you’ve lifted an initial data set, pivoting allows you to retrieve additional nodes or edges that share some property in common with your original data. For example, you can retrieve the node representing a PE executable and then "pivot" to any other PE executables that share the same PE import hash or the same PE compile time. (Note that this description of a "pivot" is effectively just lifting a set of nodes that share a specific property value, such as an import hash.)

Analysis Limitations
++++++++++++++++++++

Despite their utility and increased use, directed graphs have certain limitations, most notably the "two-dimensionality" inherent in the concept of an edge. The fact that an edge can only connect exactly two nodes leads to a variety of consequences, including:

- **Performance.** Even though a directed graph edge can only join two nodes, in theory there is no limit to the **total** number of edges to or from a given node. These “edge dense” or “heavy” nodes represent a potential performance limitation when attempting to conduct analysis across a large or complex directed graph. The computational resources required to traverse large numbers of edges, hold the resulting set of nodes in memory, and then perform additional operations on the results (filtering, pivoting, additional traversals, etc.) can become prohibitive.
  
  **Example:** "edge dense" nodes may include those representing extremely common objects such as IP address 127.0.0.1 or the MD5 hash representing the "empty" (zero-byte) file. Tens of thousands of domains may have been configured to resolve to 127.0.0.1 at various times. Similarly, hundreds of thousands of individual malware samples may attempt to write a zero-byte file to disk to test write permissions before infecting a host. Attempting a query that traverses the edges pointing to or from one of those nodes can return significant amounts of irrelevant data at best, or be performance-prohibitive at worst.

- **Data Representation.** Some relationships involve more than two objects, which may require some creativity to force them into a two-dimensional directed graph model. One side effect may be a multiplication of edges (because you need to show the relationship of several ``foos`` to a single ``bar``), or the arbitrary "clustering" of data to combine what would normally be two or more nodes into a single node simply so the cluster can be associated with another node via a single edge.
  
  **Example:** "genetic parentage" is a multi-dimensional relationship. In modeling genealogy research, you need to represent two parents and a child. In a directed graph, you can do this by representing "parentage" as a directed relationship between a single parent (``n1``) and the child (``n2``). If each individual parent is a single node, you require three nodes and two edges to represent the complete relationship among two parents and the child.
  
  Alternately, you could conflate the two parent nodes into as single node (``n1``) that consisted of the combination of the two individuals, with an edge between this "pair" (``n1``) and the child (``n2``). Here you use only two nodes and a single edge, but have created a semi-artificial "cluster" node to do so; and you will need to create a unique "cluster" node for every set of two parents that have a child. In addition, there may be cases where you want to treat one of the parents as an individual person (node) for other purposes (for example, to note the person’s date of birth and date of death as properties on that person’s node). Now the same person may be represented in multiple places in the directed graph, both as an individual node and as one part of multiple "parent clusters".
  
  The issue may seem only moderately challenging for genealogy but consider a broader field like plant biology. In an attempt to create a more drought-tolerant or disease-resistant rose bush, botanists may combine genetic material from multiple “parents” to produce a hybrid offspring.

Hypergraphs
-----------

A **hypergraph** is a generalization of a graph in which an edge can join any number of nodes. Because an edge is no longer limited to joining exactly two nodes, edges in a hypergraph are often called **hyperedges.** If a directed graph where edges join exactly two nodes is two-dimensional, then a hypergraph where a hyperedge can join any number (n-number) of nodes is **n-dimensional.**

|hypergraph|

Looked at another way, they key features of a hypergraph are:

- **Everything is a node.** Objects ("nouns") are still nodes in a hypergraph, similar to a directed graph. However, relationships ("verbs", commonly represented as edges in a directed graph) are now also represented as nodes. Where an edge in a directed graph consists of three objects (two nodes and the edge connecting them), in a hypergraph the same data is represented as a single multi-dimensional node.

- **Hyperedges connect arbitrary sets of nodes.** An edge in a directed graph connects exactly two nodes (represented as an arrow connecting two points). A hyperedge can connect an arbitrary number of nodes; this makes hypergraphs more challenging to visualize in a "flat" form. As in the image above, hyperedges are commonly represented as a set of disconnected nodes encircled by a boundary; the boundary represents the hyperedge "joining" the nodes into a related group. Just as there is no limit to the number of edges to or from a node in a directed graph, a node in a hypergraph can be joined by any number of hyperedges (i.e., be part of any number of "groups").

In Synapse, hyperedges are represented by **tags,** which can be thought of as labels applied to nodes.

Analysis with a Synapse Hypergraph
----------------------------------

Synapse is a specific implementation of a hypergraph model. Within Synapse, an individual hypergraph is called a **Cortex.** A Cortex is a scalable hypergraph implementation which also includes key/value-based node properties and a data model which facilitates normalization.

Analysis of data using a Cortex leverages some of the same methods as a directed graph: **lifting** nodes and **filtering** results are still part of the process. However, in the absence of pairwise edges there is no traversal. Instead, all navigation is based on a **pivot.** (Technically, selecting a set of nodes from a Cortex based on a tag could be considered "navigating" along a hyperedge. But mostly everything is a pivot.)

Synapse optimizes this ability to pivot across properties through two key design features: **type safety** and **property normalization.**

- **Type safety** ensures that all node properties have an explicitly declared :ref:`data-type` and these types are enforced across the data model. For example, where a property value is an IP address, that IP address is declared and stored as an integer for consistency - as opposed to being stored as an integer in some instances and a dotted-decimal string in others. (Technically an IPv4 address is stored as an IPV4 (``inet:ipv4``) type, which can be thought of as an integer with additional constraints on things like allowable values.)

- **Property normalization** ensures that properties are represented in a consistent manner for both storage and display purposes, regardless of the format in which they are received. Synapse takes a "do what I mean" approach to input where possible, attempting to recognize common formats and normalize them on the user’s behalf. This allows users to work with data in a way that should feel natural.

  For example, a user can enter an IP address as an integer, a hex value, or a dotted decimal string; Synapse will automatically store the IP as an integer and represent it back to the user as a dotted-decimal string. Similarly, a user can enter a directory path using either Windows format (``C:\foo\bar\baz.exe``) or Linux format (``/home/user/foo/bar``) and using any combination of upper and lowercase letters; Synapse will automatically enforce normalization such as the use of forward slashes for directory separators and the use of all lower-case letters for drive, path, and file names.

These features make pivoting highly effective because they ensure that data of the same type and / or with the same value is represented consistently throughout the Cortex.

In contrast, **lack** of consistency can cause analysts to miss relevant correlations - either because the same data is represented in multiple forms, or because the burden is placed on the analyst to properly normalize their input when entering data or querying the system. It is significantly harder to identify correlations when the same data is represented or referenced in multiple ways throughout a system.

Synapse’s optimized use of pivots, combined with the ability to represent relationships (including complex “multi-dimensional” relationships) as nodes, provides some significant advantages over a directed graph.

Performance
+++++++++++

"Asking questions" of a hypergraph may be less computationally intensive than in a directed graph. As a simple example, let’s say you want to know all of the IP addresses that a domain has resolved to.

**Directed Graph**

In a directed graph, "resolves to" ("has a DNS A record for") is a relationship (edge). To answer the question of which IP addresses a domain has resolved to, you need to:

- lift the node for the domain; and
- traverse an arbitrary number of "resolves to" edges to reach the set of nodes represented by the endpoints of all those edges (i.e., the IP addresses).

For a handful of edges (a small number of IPs) this traversal is not very difficult; but if the domain has resolved to hundreds or thousands of IP addresses, traversing all of those edges becomes more computationally intensive.

Looked at another way (and depending on the specific implementation of the directed graph), an edge traversal in a directed graph may be the computational equivalent of two pivots:

Assume a generic representation of an edge as a tuple comprised of two nodes and the specific edge relationship ( ``{n1,edge,n2}`` ). In our example, a "resolves to" edge would be represented by a domain (``n1``), the relationship "resolves to" (the edge tuple), and the IP address (``n2``). In this case, traversing the "resolves to" edges is really two pivots:

- lift the node (``n1``) for the domain;
- pivot from that node to all of the "resolves to" edges where the domain is the ``n1`` of the "resolves to" tuple;
- pivot from the ``n2`` (IP address) of each "resolves to" tuple to the node representing that ``n2``.

**Synapse Hypergraph (Cortex)**

In a Cortex, a single node represents the "resolves to" ("has DNS A record for") relationship, with the domain and IP address involved in the relationship both stored as properties on that node. To determine the IP addresses a domain has resolved to, you simply need to:

- lift the "DNS A record" nodes where the domain is a property;
- pivot from the IP address property of those nodes to the nodes representing the IP addresses themselves.

Alternately, you could simply view the IP addresses as properties on the lifted "DNS A record" nodes themselves without performing the pivot at all.

No Loss of Granularity
++++++++++++++++++++++

The pairwise nature of edges in a directed graph may result in a loss of granularity for complex relationships that realistically involve three or more elements. In order to "fit" those relationships into a directed graph model, one option is to arbitrarily combine some of those elements into a single node in order to force the relationship to be pairwise. This results in some loss of detail as elements that should rightly be treated as independent components are artificially conflated. Synapse’s ability to represent multidimensional relationships as a single node removes this limitation.

Discovery
+++++++++

"Asking questions of" or exploring a directed graph has some inherent limitations. First, since relationships are represented by edges, an analyst is limited to asking about (traversing) known relationships (that is, edges that are already defined in the model). This may limit the discovery of new or unexpected patterns or correlations.

Similarly, while directed graphs may support some navigation via pivots, analysts are often limited to pivoting via the same property and value on the same node type.  For example, I can ask about all PE file nodes that have the same PE import hash value as a given PE file node because I am asking about the same value for the same property across the same node type. In a directed graph it is harder to ask about a value that may be present in different properties on different node types. Synapse’s use of type enforcement and property normalization removes this restriction.

For example, let’s say you have a malicious domain and you determine the set of IP addresses that the domain has resolved to. You want to know if any of those IP addresses have also been used to send spear phishing email messages. Speaking generically, there is no readily apparent relationship between an IP address as the resolution of a domain, and an IP address as the source of an email message, other than the fact that they are both IP addresses. This lack of an apparent relationship (edge) implies that you can’t get your answer using a few simple traversals.

How you answer this question will vary depending on the specific implementation of the directed graph. However, if you assume an implementation with the following defined edges:

``<domain> -- <has DNS A record> --> <IP address>``

and 

``<IP address> -- <was source IP for> --> <RFC822 file>``

Then you may be able to obtain an answer through a multi-part query similar to the following:

1. Start from (lift) the domain.
2. Traverse the set of "has DNS A record" edges from the domain to obtain the set of IP addresses the domain has resolved to.
3. From those IP addresses, traverse any "was source IP for" edges to the set of RFC822 messages (if any) associated with the IPs.
4. From the RFC822 messages, traverse **back** along the "was source IP for" edges to get the subset of IP addresses that were used to send email messages.

If the above sounds messy and a bit redundant, to an extent it is. There may be slightly more "elegant" solutions given alternate directed graph implementations (for example, if the source IP of an email message was stored as a property on the email message node as opposed to being associated with the message via an edge). But it still requires some creative navigation amongst nodes, edges, and properties to find the answer.

In a Synapse hypergraph, the IP addresses can appear as properties on both the set of "domain has DNS A record" nodes (as the "resolved to" property, for example) and the set of "spear phishing email nodes" (as the "source IP" property, for example). You can simply pivot between the two node types based on the value of those properties to find your answer. Not only is the navigation itself significantly easier, but you are able to readily ask questions across disparate or arbitrary data types (DNS records and email messages), as long as they share a particular typed value in common – even if that value represents a different property in each case.

Conclusions
-----------

Though hypergraphs may be less familiar than traditional graphs, they offer distinct performance and analytical advantages over directed graph models, addressing historical shortcomings in representation, navigation, and analytical capability. Synapse, as a specific implementation of a hypergraph model, incorporates additional design features (type safety, property normalization, and a robust query language, in addition to storage and indexing optimization for performance) that further enhance its power and flexibility as an analysis tool.


.. |graph| image:: https://upload.wikimedia.org/wikipedia/commons/thumb/b/bc/Undirected_graph_no_background.svg/320px-Undirected_graph_no_background.svg.png 

.. |directedgraph| image:: https://upload.wikimedia.org/wikipedia/commons/thumb/3/39/Directed_acyclic_graph_3.svg/320px-Directed_acyclic_graph_3.svg.png

.. |hypergraph| image:: https://upload.wikimedia.org/wikipedia/commons/thumb/5/57/Hypergraph-wikipedia.svg/320px-Hypergraph-wikipedia.svg.png
