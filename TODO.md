Yeah so actually, I don't know that I actually need to refactor to threaded. We can just stick with single-threaded for now. The wait times aren't thaaatt bad. And since it's basically an I/O thing, and we're not actually removing wait times, we're just waiting at 5 to 10 of them at once, we aren't even changing our O(n) timing. We reduce by a factor of 5 or 10. That's nothing.

Instead, we need to handle storing the data and only caching the recent stuff. That way we can handle an arbitrarily large graph, as long as it fits on the disk of the computer. It doesn't all have to fit into RAM.

So plan:

- Do a rewrite so that the graph can be serialized on the go into a file.
- Make it easy to grab just one node (or a significantly small set of nodes, maybe) from these files.
- Build it to grab the nodes it needs, temporarily cache them, do some work, then submit those changes back to the files.

Eventually, we will be able to have a really massive graph of the web. We can then submit this data to other tools for visualization or analysis or what have you.
