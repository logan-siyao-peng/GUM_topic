# Topic segmnetation for GUM

This repo presents the topic annotation of 55 documents from 11 genres of the GUM corpus. The main idea is to recursively split text spans in a document by topic shifts.

## Data Files
- *line*: the original annotation by an undergraduate RA
- *json*: recursive json format with topic subtrees
- *split*: topic splits when only the top *n* splits are applied

## Topic Annotation Procedure

The annotation process for topic is as follows:
1. Read through the entire document consisting of one EDU per line 
2. Exclude the title/heading at the beginning of the document
3. Divide each text span into two sub spans and mark which sub span is more prominent to the document
4. Mark each sub span with a short topic label
5. Continue Steps 3 and 4 until each sub span has no more than 5 EDUs


