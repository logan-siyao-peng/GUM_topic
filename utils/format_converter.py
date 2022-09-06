import io
import os
import re
import math
from glob import glob
import json
import argparse
from statistics import mean
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter


def validate_topic_line(topicpath, rsdpath):
	with io.open(topicpath, 'r', encoding='utf8') as f:
		topic_lines = f.read().strip().split('\n')
	
	with io.open(rsdpath, 'r', encoding='utf8') as f:
		rsd_lines = f.read().strip().split('\n')
	
	topic_lines = [x.split('\t') for x in topic_lines]
	topic_edus = [x for x in topic_lines if len(x) == 2]
	rsd_edus = [x.split('\t')[:2] for x in rsd_lines if '\t' in x]
	
	# Make sure no_space strings are the same
	assert len(topic_edus) == len(rsd_edus)
	for line_id in range(len(topic_edus)):
		topic_edu_line_nospace = re.sub(r'\s+', '', topic_edus[line_id][1])
		rsd_edu_line_nospace = re.sub(r'\s+', '', rsd_edus[line_id][1])
		assert topic_edu_line_nospace == rsd_edu_line_nospace
	
	# seperate indexes to differentiate {<2} topic lines
	rsd_edu_id = 0
	for topic_line_id in range(len(topic_lines)):
		if len(topic_lines[topic_line_id]) == 2:
			topic_lines[topic_line_id][0] = rsd_edus[rsd_edu_id][0]
			topic_lines[topic_line_id][1] = rsd_edus[rsd_edu_id][1]
			rsd_edu_id += 1
	assert rsd_edu_id == len(rsd_edus)
	
	topic_lines = ["\t".join(x) for x in topic_lines]
	return topic_lines

def write_split_files(topic_lines, basename_no_ext, topic_split_dir, deepest_split_level):
	split_level_dict = {}
	for curr_split_level in range(1, deepest_split_level+1):
		kept_lines = []
		for line in topic_lines:
			if re.match(r"^\d+\t", line):
				kept_lines.append(line)
			else:
				for tmp_split_level in range(1, curr_split_level+1):
					if "{>%d}" % tmp_split_level in line \
							or "{=%d}" % tmp_split_level in line \
							or "{<%d}" % tmp_split_level in line:
						kept_lines.append(line)
		
		# Assure the right number of topic splits
		kept_break_lines = [x for x in kept_lines if "\t" not in x]
		assert len(kept_break_lines) <= 2**curr_split_level - 1
		if len(kept_break_lines) != 2**curr_split_level - 1:
			print("o Missing sublevel in file at depth: ", basename_no_ext, curr_split_level, kept_break_lines)
		
		curr_split_dir = topic_split_dir + str(curr_split_level) + os.sep
		if not os.path.exists(curr_split_dir):
			os.makedirs(curr_split_dir)
		with io.open(curr_split_dir + basename_no_ext + ".txt", "w", encoding="utf8") as f:
			f.write("\n".join(kept_lines))
			
		split_level_dict[curr_split_level] = len(kept_break_lines)
		
	return split_level_dict
		
		
			

def convert_line_to_json(topic_lines):
	lines = topic_lines
	
	# Check Title lines "~"
	title_line_numbers = [idx for idx, x in enumerate(lines) if x.strip() == "~"]
	assert len(title_line_numbers) <= 1
	if len(title_line_numbers) == 1:
		seg_anno_dict = {
			"TitleText": lines[:title_line_numbers[0]]
		}
		main_text_start_line = title_line_numbers[0] + 1
	else:
		seg_anno_dict = {}
		main_text_start_line = 0
	
	# Initially call seg anno dict, and it will then run recursively
	seg_anno_dict.update(recurse_topic_splits(lines[main_text_start_line:], 1, "", ""))
	
	return seg_anno_dict
	

def recurse_topic_splits(topic_lines, current_level, path_from_root, nuclearity_from_root):
	# find split annotations at that depth
	split_line_regex_results = [(idx, x) for idx, x in enumerate(topic_lines)
	                            if re.findall('{[<>=]' + str(current_level) + '}', x) != []]
	
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



def write_json_file(seg_anno_dict, jsonpath):
	with io.open(jsonpath, 'w', encoding='utf8') as f:
		f.write(json.dumps(seg_anno_dict, indent=4, ensure_ascii=False))


def save_number_splits_plot(deepest_split_level, num_splits, plot_file_name):
	labels, values = zip(*Counter(num_splits).items())
	indexes = np.arange(len(labels))
	
	# Creating a figure with some fig size
	fig, ax = plt.subplots(figsize=(10, 5))
	ax.bar(labels, values, width=1.0)
	# Now the trick is here.
	# plt.text() , you need to give (x,y) location , where you want to put the numbers,
	# So here index will give you x pos and data+1 will provide a little gap in y axis.
	for index, data in enumerate(values):
		plt.text(x=labels[index], y=data + 0.2, s=f"{data}", fontdict=dict(fontsize=20))
	
	xticks_range = range(math.floor(min(labels)), math.ceil(max(labels)) + 1)
	plt.xticks(xticks_range)
	plt.title("Frequency of different number of splits when max split depth is %d" % deepest_split_level,
	          y=-0.12)
	plt.tight_layout()
	plt.savefig(plot_file_name)

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--topic_line_dir", default="../data/line/")
	parser.add_argument("--rsd_dir", default="../../gum/_build/target/rst/dependencies/")
	parser.add_argument("--topic_json_dir", default="../data/json/")
	parser.add_argument("--topic_split_dir", default="../data/split/")
	parser.add_argument("--deepest_split_level", default=5)
	args = parser.parse_args()
	
	topic_docs = sorted(glob(args.topic_line_dir + "*.txt"))
	
	if not os.path.isdir(args.topic_line_dir):
		os.makedirs(args.topic_line_dir)
	
	total_split_dict = {x:[] for x in range(1,args.deepest_split_level+1)}
	for topic_doc in topic_docs:
		basename_no_ext = os.path.splitext(os.path.basename(topic_doc))[0]
		topic_lines = validate_topic_line(topic_doc,
		              args.rsd_dir + basename_no_ext + ".rsd",
		              )
		individual_split_dict = write_split_files(topic_lines, basename_no_ext, args.topic_split_dir, args.deepest_split_level)
		
		# add number of splits to dict
		for k in individual_split_dict.keys():
			total_split_dict[k].append(individual_split_dict[k])
		
		seg_anno_dict = convert_line_to_json(topic_lines)
		write_json_file(seg_anno_dict, args.topic_json_dir + basename_no_ext + ".json")
		print('o Done converting line to json: ', topic_doc)

	# Save split frequency bar plots
	for k in total_split_dict.keys():
		save_number_splits_plot(k, total_split_dict[k], args.topic_split_dir + "split_level_%d.png" % k)
