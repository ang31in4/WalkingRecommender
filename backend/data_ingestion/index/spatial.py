from sklearn.neighbors import KDTree

# this creates a KDTree to be used as a spatial index
# input: a list of points in the form (lat, lon)  
class KDTree:
    def __init__(self, node_points):
        self.tree = KDTree(node_points)