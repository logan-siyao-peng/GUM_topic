import io, re, os
from glob import glob
from statistics import mean



if __name__ == '__main__':
	# depdir = '../dependencies/*.rsd'
	# depdir = '/Users/loganpeng/Dropbox/Dissertation/data/zho-rst/rsd-zho-singlelang/*.rsd'
	rewrite = True
	educounts = {}
	for f in sorted(glob(depdir)):
		with io.open(f, 'r', encoding='utf8') as fin:
			lines = fin.read().strip().split('\n')
		basename = os.path.basename(f)
		educounts[basename] = len(lines)
		if rewrite:
			with io.open(os.path.join('raw', basename.replace('.rsd', '.raw')), 'w', encoding='utf8') as fout:
				fout.write('\n'.join(['\t'.join(x.split('\t')[:2]) for x in lines]))
	print(mean(educounts.values()), min(educounts.values()), max(educounts.values()))
	for k in educounts.keys():
		if educounts[k] <= 20:
			print(k, educounts[k])
	print('Done!')
