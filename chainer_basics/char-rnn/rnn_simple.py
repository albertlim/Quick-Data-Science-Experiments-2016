'''
http://docs.chainer.org/en/stable/tutorial/recurrentnet.html
https://github.com/pfnet/chainer/blob/master/examples/ptb/net.py
https://github.com/karpathy/char-rnn
https://github.com/yusuketomoto/chainer-char-rnn/blob/master/train.py
http://karpathy.github.io/2015/05/21/rnn-effectiveness/
'''

###### preprocessing data ######
f = open('shakespeare.txt')
raw = f.read().lower()
vocab = list(set(list(raw)))
content = raw.split('\n')
lines = []
for line in content:
	if line != '' and len(line.split()) > 4:
		lines += [line]

def char2Index(char):
	return vocab.index(char)
def index2Char(index):
	return vocab[index]
def listIndex2Sentence(list_of_index):
	return ''.join([index2Char(index) for index in list_of_index])

import numpy as np
import chainer
from chainer import cuda, Function, gradient_check, Variable, optimizers, serializers, utils, FunctionSet
from chainer import Link, Chain, ChainList
import chainer.functions as F
import chainer.links as L

class RNN(Chain):
	def __init__(self):
		super(RNN, self).__init__(
			embed=L.EmbedID(len(vocab), 100),
			mid=L.LSTM(100, 50),
			out=L.Linear(50, len(vocab)),
		)

	def reset_state(self):
		self.mid.reset_state()

	def __call__(self, cur_char):
		x = self.embed(cur_char)
		h = self.mid(x)
		y = self.out(h)
		return y

	def predict_char(self, cur_char):
		predicted = self.__call__(cur_char)
		softmax_predicted = F.softmax(predicted)
		selected = np.argmax(softmax_predicted.data)
		selected_var = Variable(np.array([selected], dtype=np.int32))
		return selected_var

	def generateSentence(self, start_index=14, length=40):
		self.reset_state()
		# note index 14 is 'c'
		starter = Variable(np.array([start_index], dtype=np.int32))
		my_list_var = [starter]
		curr = starter
		for i in range(length):
			predicted = self.predict_char(curr)
			my_list_var += [predicted]
			curr = predicted
		my_list = [elem.data.item() for elem in my_list_var]
		return my_list


class Classifier(Chain):
	def __init__(self, predictor):
		super(Classifier, self).__init__(predictor=predictor)

	def __call__(self, x, t):
		y = self.predictor(x)
		self.loss = F.softmax_cross_entropy(y, t)
		self.accuracy = F.accuracy(y, t)
		return self.loss

rnn = RNN()
model = Classifier(rnn)
optimizer = optimizers.SGD()
optimizer.setup(model)

totalSize = len(lines) / 100 * 100
batchSize = 100 

def compute_loss(x_list):
	loss = 0
	for cur_word, next_word in zip(x_list, x_list[1:]):
		# print cur_word, next_word
		x = Variable(np.array([char2Index(cur_word)], dtype=np.int32))
		y = Variable(np.array([char2Index(next_word)], dtype=np.int32))
		loss += model(x, y)
	return loss

# dummy = Variable(np.array([1], dtype=np.int32))
# print listIndex2Sentence(rnn.generateSentence())

for epoch in range(20):
	print('epoch: %d' % (epoch))
	indexes = np.random.permutation(totalSize)
	for i in range(0, totalSize, batchSize):
		if i % 1000 == 0:
			print 'at %d, generated: %s' % (i, listIndex2Sentence(rnn.generateSentence()))
		for sentenceId in range(i, i + batchSize):
			sentence = lines[sentenceId]
			# print sentence
			rnn.reset_state()
			optimizer.update(compute_loss, sentence)
