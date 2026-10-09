"""WiLI-2018 from Zenodo. Only the test split is kept: it is the benchmark;
x_train/y_train are the dataset's training data and must not be evaluated on."""
from lidpipe import paths
from lidpipe.download import finish, url_zip

out = paths.benchmark_raw('wili_2018')
lock, files = url_zip('wili_2018', out, ['x_test.txt', 'y_test.txt', 'labels.csv', 'README.txt'])
finish(out, 'wili_2018', lock, files)
