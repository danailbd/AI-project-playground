from os import path, walk
import json
import plotsparce
from sklearn import metrics

from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer

from sklearn.naive_bayes import BernoulliNB, MultinomialNB
from sklearn.svm import LinearSVC
# from sklearn.cross_validataion import KFold

SPLIT_INDEX = 3
###  prepare data sets
CATEGORIES = []

x_data_train = []
x_data_test  = []
y_train      = []
y_test       = []

# Take data for all categories
for (dir, dirs, files) in walk('processed_data'):
    for category_data in files:
        test_data = None
        with open(path.join(dir, category_data)) as fp:
            test_data = json.load(fp)

        # -> tags as string
        clips = test_data['clips_data']
        clips_tags_docs = [' '.join(clip_data['tagsCountMap']) for clip_data in clips]

        CATEGORIES.append(test_data['id'])

        test_samples_count = len(clips_tags_docs) // SPLIT_INDEX
        train_samples_count = len(clips_tags_docs) - test_samples_count

        x_data_train.extend(clips_tags_docs[:train_samples_count])
        x_data_test.extend(clips_tags_docs[train_samples_count:])

        y_train.extend([len(CATEGORIES)-1] * train_samples_count)
        y_test.extend([len(CATEGORIES)-1] * test_samples_count)

        print(len(x_data_test), len(y_test), len(x_data_train), len(y_train))

### train model

# term frequency / tf times inverse term frequency
vectorizer = TfidfVectorizer()
print('Vectorize: ', len(x_data_train))
x_train_data_vector = vectorizer.fit_transform(x_data_train)
x_test_data_vector = vectorizer.transform(x_data_test)



clf = MultinomialNB()
clf.fit(x_train_data_vector, y_train)


# MAKE PREDICTIONS
predictions = clf.predict(x_test_data_vector)
score = metrics.accuracy_score(y_test, predictions)
print(score)

# Draw the matrix
ax = plotsparce.plot_coo_matrix(x_train_data_vector)
ax.figure.show()
