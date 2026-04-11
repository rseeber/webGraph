import glob
from string import Template
import os

import scrape

md_baseDir = "_markdown/headstones"
output_baseDir = "headstones"

def buildHtml(links, title):
    with open("template.md", "r") as f:
        template = Template(f.read())
    content = ""
    for l in links:
        domain, page = scrape.splitURL(l)
        content += f"- [{l}](/{output_baseDir}/{domain}/{page})\n"
    return template.substitute(content=content, title=title)

def main(): 
    # for each domain in `data/`
        # for each page in domain
            
    domains = glob.glob("data/*.json")


    linkableDomains = []

    # create a domain page for each domain
    for domain in domains:
        domain = domain[5:-5]
        print(domain)
        linkableDomains.append(domain)
        pages = scrape.getJson_disk(domain)["pages"]
        links = []
        # create a stump page for each actual page
        for pageName in pages.keys():
            edges = pages[pageName]["edges"]
            stumpHtml = buildHtml(edges, domain+pageName)
            # save the html at f"{domain}/{page}"
            # create the folder
            dir = f"{md_baseDir}/{domain}{pageName}"
            if not os.path.exists(dir):
                os.makedirs(dir)
            # create the file
            with open(f"{md_baseDir}/{domain}{pageName}index.md", "w") as f:
                f.write(stumpHtml)

    # index of all domains
    with open(f"{md_baseDir}/index.md", "w") as f:
        f.write(buildHtml(linkableDomains, "Indexed Domains"))

# MAIN()
if __name__ == "__main__":
    main()