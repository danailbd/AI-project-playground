from os import path, walk
import json
from sklearn import metrics

from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer

from sklearn.naive_bayes import BernoulliNB, MultinomialNB
from sklearn.svm import LinearSVC
# from sklearn.cross_validataion import KFold
import numpy as np

from sklearn import cross_validation
from sklearn.cross_validation import KFold
from sklearn.cross_validation import StratifiedKFold
from sklearn.grid_search import GridSearchCV

from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.ensemble import RandomForestClassifier, VotingClassifier

SPLIT_INDEX = 7
###  prepare data sets
CATEGORIES = []


# Take data for all categories
def process_imput_data(data_path):
    x_data_train = []
    x_data_test  = []
    y_train      = []
    y_test       = []
    for (dir, dirs, files) in walk(data_path):
        for category_data_file in files:
            print('Category: ', category_data_file)
            test_data = None
            with open(path.join(dir, category_data_file)) as fp:
                loaded_data = json.load(fp)

            # -> tags as string
            clips = loaded_data['clips_data']
            clips_tags_docs = []
            for clip_data in clips:
                tags = clip_data['tagsCountMap']
                clips_tags_docs.append(' '.join(tags))
                print('-- Tags count: ', len(tags))

            CATEGORIES.append(loaded_data['id'])

            test_samples_count = len(clips_tags_docs) // SPLIT_INDEX
            train_samples_count = len(clips_tags_docs) - test_samples_count

            x_data_train.extend(clips_tags_docs[:train_samples_count])
            x_data_test.extend(clips_tags_docs[train_samples_count:])

            y_train.extend([len(CATEGORIES)-1] * train_samples_count)
            y_test.extend([len(CATEGORIES)-1] * test_samples_count)
    return ((x_data_train, y_train), (x_data_test, y_test))

# TODO make it return the generated data
test_data = process_imput_data('/home/danailbd/workspace/uni/AI/project/processed_data_no_filter')
x_data_train, y_train = test_data[0]
x_data_test, y_test = test_data[1]

### train model

# term frequency / tf times inverse term frequency
print('Train data: ', len(x_data_train))
print('Test data: ', len(x_data_test))
vectorizer = TfidfVectorizer(use_idf=False)
x_train_data_vector = vectorizer.fit_transform(x_data_train)
x_test_data_vector = vectorizer.transform(x_data_test)


for penalty in ["l2", "l1"]:
    print('=' * 80)
        
        # Train Liblinear model
        results.append(benchmark(LinearSVC(loss='l2', penalty=penalty,
                                            dual=True, tol=1e-8)))

clf1 = LogisticRegression(random_state=1)
clf2 = RandomForestClassifier(random_state=1)
clf3 = GaussianNB()
eclf1 = VotingClassifier(estimators=[
            ('lr', clf1), ('rf', clf2), ('gnb', clf3)], voting='hard')
eclf1 = eclf1.fit(x_train_data_vector.toarray(), y_train)
print(metrics.accuracy_score(eclf1.predict(x_test_data_vector.toarray()), y_test))

eclf2 = VotingClassifier(estimators=[
            ('lr', clf1), ('rf', clf2), ('gnb', clf3)],
            voting='soft')
eclf2 = eclf2.fit(x_train_data_vector.toarray(), y_train)
print(metrics.accuracy_score(eclf2.predict(x_test_data_vector.toarray()), y_test))


clf = MultinomialNB(alpha=1.0)
clf.fit(x_train_data_vector.toarray(), y_train)


# MAKE PREDICTIONS
predictions = clf.predict(x_test_data_vector.toarray())

score = metrics.accuracy_score(y_test, predictions)
print(score)
