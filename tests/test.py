from __future__ import print_function

import pprint

from rest_easy.core.main import RestEasy

RestEasy = RestEasy()

def print_function_name(func):
    def wrapper():
        print ('\n', func.__name__.upper())
        func()
    return wrapper

@print_function_name
def dlese():
    dlese = RestEasy.getWrappers('dlese').ddsws('v1.1')
    dlese.Search.query('blah')
    dlese.Search.startingOffset(5)
    dlese.Search.numReturned(5)
    dlese.Search.dateField('dsdsa')
    dlese.Search.fromDate('dsdsa')
    print (dlese.getQueryString())


@print_function_name
def dpla():
    dpla = RestEasy.getWrappers('dpla').v2
    dpla.apiKey('45c8abc4a364304df1f9db9f9fcfb659')
    dpla.Items.searchIn.title('Dead Souls')
    dpla.Items.searchIn.spatial.city('Boston')
    dpla.Items.facets.spatial.coordinates('-10:70')
    print (dpla.Items.getQueryString())
    #dpla.Items.GET(pretty_print=True)
    #dpla.Collections.searchIn.title('blah')
    #dpla.Collections.pageSize()
    #print (dpla.Collections.getQueryString())

@print_function_name
def europeana():
    europeana = RestEasy.getWrappers('europeana')
    europeana('v2').apiKey('xxxx')
    europeana('v2').Search.query('Mark Twain')
    print (europeana('v2').Search.getQueryString())

@print_function_name
def googlebooks():
    googlebooks = RestEasy.getWrappers('googlebooks').v1.Volumes
    googlebooks.query('riverboat')
    googlebooks.query.inAuthor('Twain')
    googlebooks.filter('ebooks')
    googlebooks.pagination.startIndex(2)
    googlebooks.pagination.maxResults(4)
    googlebooks.fields('items')
    print (googlebooks.getQueryString())
    #results = googlebooks('v1').Volumes.GET()

@print_function_name
def washpost():
    washpost = RestEasy.getWrappers('washpost').trove('v1')
    washpost.apiKey('xxxxx')
    washpost.Resources.variant('Mark Twain')
    washpost.Resources.includeVariants(1)
    print (washpost.Resources.getQueryString())

@print_function_name
def loc():
    loc = RestEasy.getWrappers('loc').sru('v1.1')
    loc.query('dc.author any "Gogol"')
    loc.maximumRecords(1)
    print (loc.getQueryString())

@print_function_name
def nytimes():
    nytimes = RestEasy.getWrappers('nytimes').articles('v2')
    nytimes.apiKey('xxxx')
    nytimes.responseFormat('.json')
    nytimes.filteredQuery('Terror')
    nytimes.filteredQuery.body('blah')
    nytimes.facetField.section_name()
    print (nytimes.getQueryString())

@print_function_name
def bhl():
    bhl = RestEasy.getWrappers('bhl').v2
    bhl.apiKey('xxxx')
    bhl.bookSearch.title('Japanese Journal of Infectious Diseases')
    print (bhl.getQueryString())
    #results = bhl('v2').Query.GET(pretty_print=True)

@print_function_name
def openlibrary():
    openlib = RestEasy.getWrappers('openlibrary')
    openlib.Query.edition.tableOfContents.pagenum(2)
    print (openlib.Query.getQueryString())
    #results = openlib.RESTful.Query.GET(pretty_print=True)

    openlib.MultiVolumesBrief.id.multikey([('oclc', '0030110408'),
                                           ('oclc', 424023),
                                           ('isbn', 3434343)])
    print (openlib.MultiVolumesBrief.getQueryString())

    openlib.Books.id.ISBN(123456789)
    openlib.Books.callback('blah')
    print (openlib.Books.getQueryString())


@print_function_name
def librarything():
    librarything = RestEasy.getWrappers('librarything').webservices('v1.1')
    librarything.apiKey('xxxx')
    librarything.getAuthor.name('Mark Twain')
    print (librarything.getQueryString())


@print_function_name
def hathitrust():
    hathitrust = RestEasy.getWrappers('hathitrust')

    hathitrust.VolumesBrief.id.isbn(1234567890)
    hathitrust.VolumesBrief.callback('shite')
    print (hathitrust.VolumesBrief.getQueryString())

    hathitrust.MultiVolumesBrief.id.isbn(1234567890)
    hathitrust.MultiVolumesBrief.callback('blah')
    print(hathitrust.MultiVolumesBrief.getQueryString())


@print_function_name
def inline():

    print (RestEasy.getQueryString('dpla', 'v2',
                                   'apiKey->xxx:Items->searchIn->title->Dead Souls'))

    print (RestEasy.getQueryString('dpla', 'v2', {'apiKey': 'xxxx',
                                                    'Items': {'searchIn':
                                                              {'title': 'Dead Souls'}}}))

    print (RestEasy.getQueryString('washpost', 'trove',
                                     'v1->apiKey->1234:v1->Resources->variant->Mark Twain:'+
                                     'v1->Resources->includeVariants->1'))


    #print RestEasy.getQueryString('europeana', 'v2', 'apiKey->432434:Search->query->blah')

    #RestEasy.getQueryString('europeana', 'v2', {'apiKey' : '432434',
    #                                             'Search': {'query': 'blah'}})
    #print RestEasy.getQueryString('washpost', ('Trove', 'v1'),
    #                           ['apiKey->3434343',
    #                             'Resources->variant->Mark Twain',
    #                             'Resources->includeVariants->1'])

    #print r.getQueryString('europeanav2', 'search', ['essential->wskey->232t4t',
    #                                                   'essential->query->Mark Twain',
    #                                                   'qf->TYPE->IMAGE'])

    #print RestEasy.getQueryString('openlibrary', 'Read', ['MultiVolumesBrief->id->isbn->76722',
    #                                                        'MultiVolumesBrief->id->isbn->7777777'])

sources = [dlese,
           dpla,
           europeana,
           googlebooks,
           washpost,
           nytimes,
           loc,
           bhl,
           openlibrary,
           librarything,
           hathitrust,
           inline]

def test(sources):
    for source in sources:
        #if source is not inline:
        #    continue
        #try:
        source()

test(sources)


"""
ol = RestEasy.getWrappers('openlibrary')
ol.Query.edition.genres('horror')

print (ol.Query.getQueryString())
"""
