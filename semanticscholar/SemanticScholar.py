from typing import Literal
import requests
from tenacity import (retry,
                      wait_fixed,
                      retry_if_exception_type,
                      stop_after_attempt)

from semanticscholar.semanticscholar import API_definitions, API_errors

class SemanticScholarError(Exception):
    pass

class SemanticScholar:

    DEFAULT_API_URL = 'https://api.semanticscholar.org/v1'
    GRAPH_API_URL = 'https://api.semanticscholar.org/graph/v1'
    DEFAULT_PARTNER_API_URL = 'https://partner.semanticscholar.org/v1'
    GRAPH_PARTNER_API_URL = 'https://partner.semanticscholar.org/graph/v1'

    auth_header = {}

    def __init__(
                self,
                timeout: int=2,
                graph_api: bool=False,
                api_key: str=None,
                api_url: str=None
            ) -> None:
        '''
        :param float timeout: an exception is raised
            if the server has not issued a response for timeout seconds.
        :param boolean graph_api: use old (default) or new, Academic Graph, API
        :param str api_key: (optional) private API key.
        :param str api_url: (optional) custom API url.
        '''

        if api_url:
            self.api_url = api_url
        else:
            if graph_api:
                self.api_url = self.GRAPH_API_URL
            else:
                self.api_url = self.DEFAULT_API_URL

        if api_key:
            self.auth_header = {'x-api-key': api_key}
            if not api_url:
                if graph_api:
                    self.api_url = self.GRAPH_PARTNER_API_URL
                else:
                    self.api_url = self.DEFAULT_PARTNER_API_URL

        self.timeout = timeout

    def paper(self, id: str, fields: list=[], include_unknown_refs: bool=False) -> dict:
        '''Paper lookup

        :param str id: S2PaperId, DOI or ArXivId.
        :param list fields: list of fields in query.
        :param float timeout: an exception is raised
            if the server has not issued a response for timeout seconds.
        :param bool include_unknown_refs:
            (optional) include non referenced paper.
        :returns: paper data or empty :class:`dict` if not found.
        :rtype: :class:`dict`
        '''

        data = self.__get_data('paper', id, fields, include_unknown_refs)

        return data

    def author(self, id: str, fields: list=[]) -> dict:
        '''Author lookup

        :param str id: S2AuthorId.
        :param list fields: list of fields in query
        :returns: author data or empty :class:`dict` if not found.
        :rtype: :class:`dict`
        '''

        data = self.__get_data('author', id, fields, False)

        return data

    @retry(
        wait=wait_fixed(30),
        retry=retry_if_exception_type(ConnectionRefusedError),
        stop=stop_after_attempt(10)
    )
    def __get_data(
                self,
                method: Literal['paper', 'author'],
                id: str,
                fields: list,
                include_unknown_refs: bool
            ) -> dict:
        '''Get data from Semantic Scholar API

        :param str method: 'paper' or 'author'.
        :param str id: id of the corresponding method.
        :param list fields: list of fields in query.
        :returns: data or empty :class:`dict` if not found.
        :rtype: :class:`dict`
        '''

        data = {}
        method_types = ['paper', 'author']
        if method not in method_types:
            raise ValueError(
                'Invalid method type. Expected one of: {}'.format(method_types)
            )

        url = '{}/{}/{}'.format(self.api_url, method, id)
        payload = {}
        if include_unknown_refs:
            payload['include_unknown_references'] = 'true'
        if (fields != []):
            payload['fields'] = ','.join(fields)
        r = requests.get(url, params=payload, timeout=self.timeout, headers=self.auth_header)

        if r.status_code == 200:
            data = r.json()
            if len(data) == 1 and 'error' in data:
                data = {}
        elif r.status_code == 403:
            raise PermissionError('HTTP status 403 Forbidden.')
        elif r.status_code == 429:
            raise ConnectionRefusedError('HTTP status 429 Too Many Requests.')
        elif str(r.status_code) in API_errors.keys():
            raise SemanticScholarError(r.json()['error'])

        return data
