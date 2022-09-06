import io
import os
import re
import argparse
import copy
from glob import glob
from collections import defaultdict


def extract_spans_from_rs3(filename):
	
	with io.open(filename, "r", encoding="utf8") as f:
		lines = f.read().strip().split("\n")
		
	prev_span_dict = None
	span_dict = defaultdict(list)
	while_counter = 0
	
	# assert False # bug in while loop
	
	while prev_span_dict != span_dict:
		# update prev copy of span_dict
		prev_span_dict = copy.deepcopy(span_dict)
		
		for line in lines:
			if "parent=" in line:
				segment_id = re.findall(r"segment id=\"(\d+)\"", line) # EDUs
				group_id = re.findall(r"group id=\"(\d+)\"", line) # non-E DUs
				parent_id = re.findall(r"parent=\"(\d+)\"", line)
				assert len(segment_id) + len(group_id) == 1
				assert len(parent_id) == 1
				parent_id = int(parent_id[0])
	
				# debug
				if '<segment id="11" parent="10"' in line:
					print()
	
				# add span to parent
				if len(segment_id) == 1:
					span_id = int(segment_id[0])
					span_dict[span_id] += [span_id]
				elif len(group_id) == 1:
					span_id = int(group_id[0])
				
				# add to direct parent
				span_dict[parent_id] += span_dict[span_id]
				# add to non-direct super parents
				# for k2 in span_dict.keys():
				# 	if parent_id in span_dict[k2]:
				# 		span_dict[k2] += span_dict[span_id]
				
				# debug
				if parent_id == 99:
					print()
		
		for k in span_dict.keys():
			span_dict[k] = sorted(list(set(span_dict[k])))
			
		print("While loop counter: ", while_counter)
		while_counter += 1
		
	
	span_boundary_dict = {}
	for k in span_dict.keys():
		assert span_dict[k] == list(range(span_dict[k][0], span_dict[k][-1]+1))
		span_boundary_dict[k] = (span_dict[k][0], span_dict[k][-1]+1)
	
	return span_boundary_dict
			
			
		
	
	


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("--rs3_dir", default="../../gum-dev-cloned20211007/rst/rstweb/")
	parser.add_argument("--rsd_dir", default="../../gum-dev-cloned20211007/rst/dependencies/")
	parser.add_argument("--topic_split_dir", default="../data/split/")
	parser.add_argument("--deepest_split_level", default=5)
	args = parser.parse_args()
	
	rs3_files = sorted(glob(args.rs3_dir + "*.rs3"))
	
	for rs3_file in rs3_files:
		rs3_boundary_dict = extract_spans_from_rs3(rs3_file)
		print()
	
	
	
