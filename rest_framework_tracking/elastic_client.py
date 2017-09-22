from elasticsearch import Elasticsearch
from django.conf import settings


class ElasticClient(Elasticsearch):

    def __init__(self):
        elasticsearch_connection_config = getattr(settings, 'DRF_TRACKING_ELASTIC_CONFIG', None)
        self.elasticsearch_index = getattr(settings, 'DRF_TRACKING_ELASTIC_INDEX', None)
        super(ElasticClient, self).__init__(**elasticsearch_connection_config)

    def add_api_log(self, data):
        self.index(index=self.elasticsearch_index.lower(), doc_type="drf_log", body=data)
