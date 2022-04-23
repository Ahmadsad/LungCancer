from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, train_test_split, cross_val_score
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import csr_matrix

from sklearn.metrics import classification_report
# from lime import lime_tabular

import shap
import numpy as np
# import random

def get_AUC_ROC_value(X_test, Y_test, model):
    auc_roc = roc_auc_score(y_true = np.array(Y_test), y_score = np.array(model.predict(X_test)))
#     print("AUC_ROC:", auc_roc)
    return auc_roc

def get_train_test_split_data(data_list, labels, test_size=0.33, random_state=50, shuffle=False, stratify=None):
    X_train, X_test, Y_train, Y_test = train_test_split(data_list, labels, shuffle=shuffle, stratify=stratify,
                                                  test_size=test_size, random_state=random_state)
    return (X_train, X_test, Y_train, Y_test)

def get_tfidf_vectorization_model(data_list):
    return TfidfVectorizer().fit(data_list)

def get_tfidf_vectorized_data(to_be_vectorized_data, tfidf_model=None, tfidfTrain_data_list=None):
    if tfidf_model is None:
        vect = TfidfVectorizer().fit(tfidfTrain_data_list)
    else:
        vect = tfidf_model
    return vect.transform(to_be_vectorized_data)

def get_csr_matrix(vectorized_data_list, dtype="float"):
    """
    efficient arithmetic operations CSR + CSR, CSR * CSR, etc.
    efficient row slicing
    fast matrix vector products
    """
    try:
        return csr_matrix(vectorized_data_list, dtype=dtype).toarray()
    except:
        return
    
def get_classification_report(cls, test_data, test_labels, target_names=["cancer","no cancer"]):
    return classification_report(test_labels, cls.predict(test_data), target_names=target_names)

def get_shap_kernel_explainer_and_values(cls, training_data, test_data):
    explainer = shap.KernelExplainer(cls.predict_proba, training_data)
    shap_values = explainer.shap_values(test_data)
    return (explainer, shap_values)

def get_cross_validation_scores(clf, X_train, Y_train, cv=5, n_jobs=-1):
    scores = cross_val_score(clf, X_train, Y_train, cv=cv, n_jobs=n_jobs)
    print("Cross validation, %0.2f accuracy with a standard deviation of %0.2f" % (scores.mean(), scores.std()))
    return scores;
