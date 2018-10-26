from elasticsearch import Elasticsearch

from django.conf import settings
from django.utils.timezone import now


class ElasticClient(Elasticsearch):
    def __init__(self):
        elasticsearch_connection_config = getattr(settings, 'DRF_TRACKING_ELASTIC_CONFIG', None)
        self.elasticsearch_index = getattr(settings, 'DRF_TRACKING_ELASTIC_INDEX',
                                           "drf-tracking-%s" % now().strftime('%Y.%m.%d'))
        self.elasticsearch_type = getattr(settings, 'DRF_TRACKING_ELASTIC_TAGS', 'drf_logs')
        super(ElasticClient, self).__init__(elasticsearch_connection_config['host'],
                                            **elasticsearch_connection_config)

    def add_api_log(self, data):
        self.index(index=self.elasticsearch_index.lower(), doc_type=self.elasticsearch_type,
                   body=data)
