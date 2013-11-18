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
    dlese = RestEasy.get_wrappers('dlese').ddsws('v1.1')
    dlese.Search.query('earth')
    dlese.Search.startingOffset(1)
    dlese.Search.numReturned(5)
    #dlese.Search.dateField('2013')
    #dlese.Search.fromDate('2013')
    print (dlese.get_query_string())
    #results = dlese.GET(return_format='json')

@print_function_name
def dpla():
    dpla = RestEasy.get_wrappers('dpla').v2
    dpla.apiKey('xxxx')
    dpla.Items.searchIn.title('Dead Souls')
    dpla.Items.searchIn.spatial.city('Boston')
    dpla.Items.facets.spatial.coordinates('-10:70')
    print (dpla.Items.get_query_string())

    dpla.new_query()
    dpla.Items.searchIn.title('Mark Twain')
    print (dpla.Items.get_query_string())

    #results = dpla.Items.GET()

    #dpla.Collections.searchIn.title('blah')
    #dpla.Collections.pageSize()
    #print (dpla.Collections.get_query_string(reset=True))

@print_function_name
def europeana():
    europeana = RestEasy.get_wrappers('europeana')
    europeana('v2').apiKey('xxxx')
    europeana('v2').Search.query('Mark Twain')
    print (europeana('v2').Search.get_query_string())
    #results = europeana('v2').Search.GET()


@print_function_name
def googlebooks():
    googlebooks = RestEasy.get_wrappers('googlebooks').v1.Volumes
    googlebooks.query('riverboat')
    googlebooks.query.inAuthor('Twain')
    googlebooks.filter('ebooks')
    googlebooks.pagination.startIndex(2)
    googlebooks.pagination.maxResults(4)
    googlebooks.fields('items')
    print (googlebooks.get_query_string())
    #results = googlebooks.GET()

@print_function_name
def washpost():
    washpost = RestEasy.get_wrappers('washpost').trove('v1')
    washpost.apiKey('xxxx')
    washpost.Resources.variant('Mark Twain')
    washpost.Resources.includeVariants(1)
    print (washpost.Resources.get_query_string())
    #results = washpost.Resources.GET()

@print_function_name
def loc():
    loc = RestEasy.get_wrappers('loc').sru('v1.1')
    loc.query('dc.author any "Gogol"')
    loc.maximumRecords(1)
    print (loc.get_query_string())
    #results = loc.GET()

@print_function_name
def nytimes():
    nytimes = RestEasy.get_wrappers('nytimes').articles('v2')
    nytimes.apiKey('xxxx')
    nytimes.responseFormat('.json')
    nytimes.filteredQuery('Terror')
    nytimes.filteredQuery.body('blah')
    nytimes.facetField.section_name()
    print (nytimes.get_query_string())
    #results = nytimes.GET()

@print_function_name
def bhl():
    bhl = RestEasy.get_wrappers('bhl').v2
    bhl.apiKey('xxxx')
    bhl.bookSearch.title('Japanese Journal of Infectious Diseases')
    print (bhl.get_query_string())
    #results = bhl.GET()

@print_function_name
def openlibrary():
    openlib = RestEasy.get_wrappers('openlibrary')
    openlib.Query.edition.tableOfContents.pagenum("10")
    print (openlib.Query.get_query_string(reset=True))
    #results = openlib.Query.GET()

    openlib.MultiVolumesBrief.id.multikey([('oclc', '0030110408'),
                                           ('oclc', 424023),
                                           ('isbn', 3434343)])
    print (openlib.MultiVolumesBrief.get_query_string(reset=True))

    openlib.Books.id.ISBN(123456789)
    openlib.Books.callback('blah')
    print (openlib.Books.get_query_string(reset=True))


@print_function_name
def librarything():
    librarything = RestEasy.get_wrappers('librarything').webservices('v1.1')
    librarything.apiKey('xxxx')
    librarything.getAuthor.name('Mark Twain')
    print (librarything.get_query_string())
    #results = librarything.GET()

@print_function_name
def hathitrust():
    hathitrust = RestEasy.get_wrappers('hathitrust')

    hathitrust.VolumesBrief.id.isbn(1234567890)
    hathitrust.VolumesBrief.callback('shite')
    print (hathitrust.VolumesBrief.get_query_string(reset=True))
    #results = hathitrust.VolumesBrief.GET()

    hathitrust.MultiVolumesBrief.id.isbn(1234567890)
    hathitrust.MultiVolumesBrief.callback('blah')
    print(hathitrust.MultiVolumesBrief.get_query_string(reset=True))
    #results = hathitrust.MultiVolumesBrief.GET()

@print_function_name
def inline():
    print (RestEasy.get_query_string('dpla', 'v2',
                                     'apiKey->xxxx:Items->searchIn->title->Dead Souls',
                                     reset=True))
    
    print (RestEasy.get_query_string('dpla', 'v2', {'apiKey': 'xxxx',
                                                    'Items': {'searchIn':
                                                              {'title': 'Dead Souls'}}},
                                     reset=True))

    print (RestEasy.get_query_string('washpost', 'trove',
                                     'v1->apiKey->xxxx:v1->Resources->variant->Mark Twain:'+
                                     'v1->Resources->includeVariants->1',
                                     reset=True))


    #print RestEasy.get_query_string('europeana', 'v2', 'apiKey->432434:Search->query->blah')

    #RestEasy.get_query_string('europeana', 'v2', {'apiKey' : '432434',
    #                                             'Search': {'query': 'blah'}})
    #print RestEasy.get_query_string('washpost', ('Trove', 'v1'),
    #                           ['apiKey->3434343',
    #                             'Resources->variant->Mark Twain',
    #                             'Resources->includeVariants->1'])

    #print r.get_query_string('europeanav2', 'search', ['essential->wskey->232t4t',
    #                                                   'essential->query->Mark Twain',
    #                                                   'qf->TYPE->IMAGE'])

    #print RestEasy.get_query_string('openlibrary', 'Read', ['MultiVolumesBrief->id->isbn->76722',
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
        if source is not dlese:
            continue
        #try:
        source()

test(sources)


"""
ol = RestEasy.get_wrappers('openlibrary')
ol.Query.edition.genres('horror')

print (ol.Query.get_query_string(reset=True))
"""
