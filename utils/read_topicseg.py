import io
import os
import re
from glob import glob
import json
import argparse


def read_topicseg(topicpath, updatedrsdpath, jsonpath):
	with io.open(topicpath, 'r', encoding='utf8') as f:
		topic_lines = f.read().strip().split('\n')
	
	with io.open(updatedrsdpath, 'r', encoding='utf8') as f:
		rsd_lines = f.read().strip().split('\n')
	
	topic_lines = [x.split('\t') for x in topic_lines]
	topic_edus = [x for x in topic_lines if len(x)==2]
	rsd_edus = [x.split('\t')[:2] for x in rsd_lines if '\t' in x]
	
	# Make sure no_space strings are the same
	assert len(topic_edus) == len(rsd_edus)
	for line_id in range(len(topic_edus)):
		topic_edu_line_nospace = re.sub(r'\s+', '', topic_edus[line_id][1])
		rsd_edu_line_nospace = re.sub(r'\s+', '', rsd_edus[line_id][1])
		assert topic_edu_line_nospace  == rsd_edu_line_nospace
	# assert topic_edus == rsd_edus
	
	rsd_edu_id = 0
	for topic_line_id in range(len(topic_lines)):
		if len(topic_lines[topic_line_id])==2:
			assert topic_lines[topic_line_id][0] == rsd_edus[rsd_edu_id][0]
			topic_lines[topic_line_id][1] = rsd_edus[rsd_edu_id][1]
			rsd_edu_id += 1
	assert rsd_edu_id == len(topic_edus)
	
	topic_lines = ["\t".join(x) for x in topic_lines]
	lines = topic_lines # TODO: improve
	# Check Title lines "~"
	title_line_numbers = [idx for idx, x in enumerate(lines) if x.strip()=="~"]
	assert len(title_line_numbers) <= 1
	if len(title_line_numbers) == 1:
		seg_anno_dict = {
			"TitleText": lines[:title_line_numbers[0]]
		}
		main_text_start_line = title_line_numbers[0]+1
	else:
		seg_anno_dict = {}
		main_text_start_line = 0
	
	# Initially call seg anno dict (recursively)
	seg_anno_dict.update(recurse_topic_splits(lines[main_text_start_line:], 1, "", ""))
	
	with io.open(jsonpath, 'w', encoding='utf8') as f:
		f.write(json.dumps(seg_anno_dict, indent=4, ensure_ascii=False))
	
	
	

def recurse_topic_splits(topic_lines, current_level, path_from_root, nuclearity_from_root):

	# find split annotations at that depth
	split_line_regex_results = [(idx, x) for idx, x in enumerate(topic_lines)
	                            if re.findall('{[<>=]' + str(current_level) + '}', x)!=[]]
	
	# If we reached the end node with no more splits
	if split_line_regex_results == []:
		assert all('\t' in x for x in topic_lines)
		return None

	
	elif len(split_line_regex_results) == 1:
		split_line_number, split_line_text = split_line_regex_results[0]
		split_anno = re.findall('{[<>=]' + str(current_level) + '}', split_line_text)
		assert len(split_anno) == 1
		split_anno = split_anno[0]
		
		if "<" in split_anno:
			nuclearity_dict = {
				"LeftNuclearity": "S",
				"RightNuclearity": "N",
			}
		elif ">" in split_anno:
			nuclearity_dict = {
				"LeftNuclearity": "N",
				"RightNuclearity": "S",
			}
		elif "=" in split_anno:
			nuclearity_dict = {
				"LeftNuclearity": "M",
				"RightNuclearity": "M",
			}
		else:
			print('o Error: wrong nuclearity annotation, None of >, <, =')

		recurse_dict = {
			"Depth": current_level,
			"PathFromRoot": path_from_root,
			"NuclearityFromRoot": nuclearity_from_root,
			"LeftText": [x for x in topic_lines[:split_line_number] if '\t' in x],
			"LeftTopic": split_line_text.split(split_anno)[0],
			"LeftTree": recurse_topic_splits(
				topic_lines[:split_line_number],
                 current_level + 1,
                 path_from_root + "L",
                 nuclearity_from_root + nuclearity_dict['LeftNuclearity'],
                 ),
			"RightText": [x for x in topic_lines[split_line_number + 1:] if '\t' in x],
			"RightTopic": split_line_text.split(split_anno)[1],
			"RightTree": recurse_topic_splits(
				topic_lines[split_line_number + 1:],
				current_level + 1,
				path_from_root + "R",
				nuclearity_from_root + nuclearity_dict['RightNuclearity'],
			),
		}
		
		
		recurse_dict.update(nuclearity_dict)
		
		return recurse_dict

	
	else:
		print('o Error: more splits than expected', split_line_regex_results)
		assert False
	
	
	
	



if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--topicseg_anno", default="anno_revised_byLogan_Sept2021/")
	parser.add_argument("--updated_gold_rsd", default="../gum-dev-cloned20211007/_build/target/rst/dependencies/")
	parser.add_argument("--topicseg_json", default="topicseg_json/")
	args = parser.parse_args()
	
	topic_docs = sorted(glob(args.topicseg_anno+"*.topicseg"))
	
	if not os.path.isdir(args.topicseg_json):
		os.mkdir(args.topicseg_json)
	
	for topic_doc in topic_docs:
		basename_no_ext = os.path.splitext(os.path.basename(topic_doc))[0].replace("_reannotated", "")
		read_topicseg(topic_doc,
		              args.updated_gold_rsd + basename_no_ext + ".rsd",
		              args.topicseg_json + basename_no_ext + ".json",
		              )
		print('o Done with reading doc %s to json' % topic_doc)
	
	
