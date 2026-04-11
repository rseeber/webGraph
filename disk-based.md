# disk-based git branch

This branch is for refactoring the code so that rather than storing the graph in memory as an object, we will be storing it on the disk as a json (or multiple json's).

The json will have the following form:

```
{
    "!metadata" : { /* data fields here */},
    
    //domain:{page:[link1, link2, ..., linkn]}
    "example.com" : {
        "/" : {
            "metadata": {}, 
            "edges": ["/", "/about", "/blog", "google.com/", "11ty.dev/about", "www.youtube.com/watch?v=dQw4w9WgXcQ"],
        "/blog" : [/* ...etc */]
    }
}
```

So that we never have to perform refactoring operations, we can simply store each domain as a seperate json file. So the above example would be stored as 

It's possible that we might store multiple json files, where we sort them based on the domain's listed. So the given example above includes two domains: `example.com` and `foo.net`. Possibly this graph.json includes all domains starting with letters 'e' and 'f'. We could also divise a structure based on the first two letters (e.g. graph for Ea-Ec -- "easter.com" and "ecclesiastical-studies.net" both included, but "education.net" would not be).

Or we could even have this be done programatically based on consumed space, so that it would be based on the first n characters. If ever a file exceeded 200MB (say), it would be split roughly in half. It would find a way to split the file in half. Either by reducing the range (e.g. Ea-Ec becomes Ea-Eb, and Ec files respectively), or if the file includes only 1 character specification (e.g., Ab), it would simply tack on a new additional letter (say, creating Aba-Abi, and Abj-Abz files).