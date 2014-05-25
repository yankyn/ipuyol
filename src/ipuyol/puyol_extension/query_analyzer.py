from ipuyol.orm_extension_base.orm_completer import OrmQueryAnalyzer

__author__ = 'Nathaniel'


class PuyolLikeQueryAnalyzer(OrmQueryAnalyzer):
    def get_from_clause(self):
        inner_query = self.query._q
        all_mappers = list(inner_query._join_entities) + [inner_query._entity_zero().entity_zero]
        all_classes = map(lambda x: x.entity, all_mappers)
        return all_classes

    def get_last_table(self):
        """
        ~`rtype`: mapper
        """
        return self.query._q._joinpoint_zero()