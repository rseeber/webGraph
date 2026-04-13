import glob
from string import Template
import os
import json

import scrape

md_baseDir = "_markdown"
output_baseDir = "headstones"

def buildHtml(links, title, output_baseDir, link):
    with open("template.md", "r") as f:
        template = Template(f.read())
    content = ""
    for l in links:
        domain, page = scrape.splitURL(l)
        content += f"- [{l}](/{output_baseDir}/{domain}/{page})\n"
    return template.substitute(content=content, title=title, link=link)

def writeToMdFile(filename, data):
    with open(f"{md_baseDir}/{filename}/index.md", "w") as f:
        f.write(data)

def getTitleFromConfig():
    # load config.json
    with open("config.json", "r") as f:
        config = json.load(f)

    nameDefault = config["nameDefault"]
    nameOpt = input(f"What is the dataset called?\n(0)=\033[1;4m{nameDefault}\033[m, (1)=Spider, (2)=Crawl\n> ")
    # handle default value
    if nameOpt == "":
        nameOpt = 0
    try:
        nameOpt = int(nameOpt)
        title = [nameDefault, "Spider", "Crawl"][nameOpt]
    # if the user puts in a custom name, just use that
    except Exception:
        title = nameOpt
    return title

def main(): 
    scrape.title = getTitleFromConfig()
            
    domains = glob.glob(f"data/{scrape.title}/*.json")


    linkableDomains = []

    # create a domain page for each domain
    for domain in domains:
        domain = domain[len(f"data/{scrape.title}/"):-len(".json")]
        print(domain)
        linkableDomains.append(domain)
        pages = scrape.getJson_disk(domain)["pages"]
        links = []
        # create a stump page for each actual page
        for pageName in pages.keys():
            links.append(domain+pageName)
            edges = pages[pageName]["edges"]
            stumpHtml = buildHtml(edges, domain+pageName, "headstones", f"http://{domain}{pageName}")
            # save the html at f"{domain}/{page}"
            # create the folder
            dir = f"{md_baseDir}/headstones/{domain}{pageName}"
            if not os.path.exists(dir):
                os.makedirs(dir)
            # create the file
            writeToMdFile(f"headstones/{domain}{pageName}", stumpHtml)
        domainHtml = buildHtml(links, domain, "headstones", f"http://{domain}/")
        dir = f"{md_baseDir}/browse/{domain}"
        if not os.path.exists(dir):
            os.makedirs(dir)
        writeToMdFile(f"browse/{domain}", domainHtml)

    # index of all domains
    browseHtml = buildHtml(linkableDomains, "Browse Domains", "browse", "N/A")
    writeToMdFile(f"browse", browseHtml)

# MAIN()
if __name__ == "__main__":
    main()