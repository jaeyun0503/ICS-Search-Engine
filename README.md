# ICS Search Engine
In order to run the program, please run the command:

```bash
pip install -r requirements.txt
```
After downloading the packages, at the root directory of the project, run the indexer.py file to generate the indexers for use in the search engine. In the res folders there will be files for inverted index, urls and reference index. This process takes about 7 ~ 10 minutes to complete.

When the program finishes indexing, you can choose to use Web GUI or command line.

1. Web GUI:

Run the following command:

```bash
python3 app.py
```

This will host a local server that allows you to use the Web GUI. (Default: http://127.0.0.1:5000  , check terminal output for the actual link)
You will be able to search once you enter the link.

2. Command line:

Run the search.py file, and enter the query in the command line
*Notice: If the number of links is large, some links may not be able to be displayed.


This program allows users to search keywords wihtin the UCI ICS Domains that have been properly indexed, with a fast responding time under 100ms

