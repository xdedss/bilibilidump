

import codecs, sys, os, logging, multiprocessing
import argparse

 
from gensim.models import Word2Vec
from gensim.models.word2vec import LineSentence


def train_vec(fname, dim):
    print('word to vec')
    
    program = os.path.basename(sys.argv[0])
    logger = logging.getLogger(program)
    logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s')
    logging.root.setLevel(level=logging.INFO)

    model = Word2Vec(LineSentence(fname), size=dim, window=5, min_count=5, workers=multiprocessing.cpu_count())
    model.save('%s.model' % fname)
    model.wv.save_word2vec_format('%s.vector' % fname, binary=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', metavar='input', help='输入文件名')
    parser.add_argument('-d', '--dim', dest='dim', default=200, type=int, help='词向量维数，默认200')
    args = parser.parse_args()
    
    train_vec(args.input, args.dim)


