import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn import metrics
from sklearn.model_selection import ParameterGrid
from sklearn.cluster import KMeans
from google.oauth2 import service_account


def load_houses():
    """
    Loading the houses dataset in pandas dataframe
    :return: scaled data
    """
    # loading house dataset
    
    credentials =  service_account.Credentials.from_service_account_info(
        {
          #GCP CREDENTIALS HERE
        }
    )
    houses = pd.read_gbq('select houseMeters, houseType, devicesProfile, climaticProfile from `house_cluster_input`', 'org', credentials = credentials)
    # checking data shape
    row, col = houses.shape
    print(f'There are {row} rows and {col} columns') 
    print(houses.head(10))
    return houses


def load_embeddings(houses):
    

    # to work on copy of the data
    houses_scaled = houses.copy()
    # Scaling the data to keep the different attributes in same range.
    houses_scaled[houses_scaled.columns] = StandardScaler().fit_transform(houses_scaled)
    print(houses_scaled.describe())
    return houses_scaled

def pca_embeddings(df_scaled):
    """To reduce the dimensions of dataset we use Principal Component Analysis (PCA).
    Here we reduce it from 4 dimensions to 2.
    :param df_scaled: scaled data
    :return: pca result, pca for plotting graph
    """

    pca_2 = PCA(n_components=2)
    pca_2_result = pca_2.fit_transform(df_scaled)
    print('Explained variation per principal component: {}'.format(pca_2.explained_variance_ratio_))
    print('Cumulative variance explained by 2 principal components: {:.2%}'.format(
        np.sum(pca_2.explained_variance_ratio_)))

    # Results from pca.components_
    dataset_pca = pd.DataFrame(abs(pca_2.components_), columns=df_scaled.columns, index=['PC_1', 'PC_2'])
    print('\n\n', dataset_pca)
    
    print("\n*************** Most important features *************************")
    print('As per PC 1:\n', (dataset_pca[dataset_pca > 0.3].iloc[0]).dropna())
    print('\n\nAs per PC 2:\n', (dataset_pca[dataset_pca > 0.3].iloc[1]).dropna())
    print("\n******************************************************************")

    return pca_2_result, pca_2


def kmean_hyper_param_tuning(data):
    """
    Hyper parameter tuning to select the best from all the parameters on the basis of silhouette_score.
    :param data: dimensionality reduced data after applying PCA
    :return: best number of clusters for the model (used for KMeans n_clusters)
    """
    # candidate values for our number of cluster
    parameters = [10, 15, 20, 30, 40, 50, 60, 80]

    # instantiating ParameterGrid, pass number of clusters as input
    parameter_grid = ParameterGrid({'n_clusters': parameters})

    best_score = -1
    kmeans_model = KMeans()     # instantiating KMeans model
    silhouette_scores = []

    # evaluation based on silhouette_score
    for p in parameter_grid:
        kmeans_model.set_params(**p)    # set current hyper parameter
        kmeans_model.fit(data)          # fit model on dataset, this will find clusters based on parameter p

        ss = metrics.silhouette_score(data, kmeans_model.labels_)   # calculate silhouette_score
        silhouette_scores += [ss]       # store all the scores

        print('Parameter:', p, 'Score', ss)

        # check p which has the best score
        if ss > best_score:
            best_score = ss
            best_grid = p

    # plotting silhouette score
    plt.bar(range(len(silhouette_scores)), list(silhouette_scores), align='center', color='#722f59', width=0.5)
    plt.xticks(range(len(silhouette_scores)), list(parameters))
    plt.title('Silhouette Score', fontweight='bold')
    plt.xlabel('Number of Clusters')
    plt.show()

    return best_grid['n_clusters']


def visualizing_results(pca_result, label, centroids_pca):
    """ Visualizing the clusters
    :param pca_result: PCA applied data
    :param label: K Means labels
    :param centroids_pca: PCA format K Means centroids
    """
    # ------------------ Using Matplotlib for plotting-----------------------
    x = pca_result[:, 0]
    y = pca_result[:, 1]

    plt.scatter(x, y, c=label, alpha=0.5, s=200)  # plot different colors per cluster
    plt.title('Houses clusters')
    plt.xlabel('PCA 1')
    plt.ylabel('PCA 2')

    plt.scatter(centroids_pca[:, 0], centroids_pca[:, 1], marker='X', s=200, linewidths=1.5,
                color='red', edgecolors="black", lw=1.5)

    plt.show()


def main():
    print("1. Loading houses dataset\n")
    houses = load_houses()
    data_scaled = load_embeddings(houses)
    print("\n\n2. Reducing via PCA\n")
    pca_result, pca_2 = pca_embeddings(data_scaled)

    print("\n\n3. HyperTuning the Parameter for KMeans\n")
    optimum_num_clusters = kmean_hyper_param_tuning(data_scaled)
    print("optimum num of clusters =", optimum_num_clusters)

    # fitting KMeans
    kmeans = KMeans(n_clusters=optimum_num_clusters)
    kmeans.fit(data_scaled)
    centroids = kmeans.cluster_centers_
    centroids_pca = pca_2.transform(centroids)

    print("\n\n4. Visualizing the data")
    visualizing_results(pca_result, kmeans.labels_, centroids_pca)

    point=np.asarray([100,0,7000, 2]).reshape(1, -1)
    pointScaled = StandardScaler().fit_transform(point)
 

    #print(*centroids, sep='\n')
   
    clusterId = np.argmin(kmeans.transform(point))
    print("cluster id para el punto ", point)
    print(clusterId)

    print("resto de casas para ese centroide ")
    for index in np.where(kmeans.labels_ == clusterId):
        print(houses.iloc[index])

    print("Casas por cluster: ", np.unique(kmeans.labels_, return_counts=True))

    for clus in np.unique(kmeans.labels_):
      print("Cluster: ", clus)
      for index in np.where(kmeans.labels_ == clus):
          print(houses.iloc[index])
    
    houses['clusterId']=kmeans.labels_
    

if __name__ == "__main__":
    main()
