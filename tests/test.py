from __future__ import print_function

import yaml
import re
import pprint
import json
from io import StringIO

from rest_easy.core.main import RestEasy

RestEasy = RestEasy()


def print_function_name(func):
    def wrapper(**kwargs):
        print ('\n', func.__name__.upper())
        func(**kwargs)
    return wrapper

@print_function_name
def dlese(**kwargs):
    dlese = RestEasy.get_wrappers('dlese').ddsws('v1.1')
    dlese.Search.query('magma')
    dlese.Search.startingOffset(1)
    dlese.Search.numReturned(5)
    dlese.Search.fromDate('2000')
    dlese.Search.dateField('2013')
    if kwargs.get('url'):
        print (dlese.Search.get_url())
    if kwargs.get('query'):
        results = dlese.Search.GET()
        if kwargs.get('print'):
            print (results)
    dlese.ListGradeRanges()
    if kwargs.get('url'):
        print (dlese.ListGradeRanges.get_url())
    if kwargs.get('query'):
        results = dlese.ListGradeRanges.GET()
        if kwargs.get('print'):
            print (results)

@print_function_name
def dpla(**kwargs):
    dpla = RestEasy.get_wrappers('dpla').v2
    dpla.setApiKeyFromHome()        
    dpla.Items.searchIn.title('Dead Souls')
    dpla.Items.facets.spatial.city()
    dpla.Items.facets.spatial.coordinates('-10:70')
    if kwargs.get('url'):
        print (dpla.Items.get_url())
    
    dpla.Items.new_query()

    dpla.Items.searchIn.title('Mark Twain')
    if kwargs.get('url'):
        print (dpla.Items.get_url())

    if kwargs.get('query'):
        results = dpla.Items.GET()
        if kwargs.get('print'):
            print (results)
    
    #pprint.pprint(results[0]._data_)
    #for i in results:
        #pprint.pprint(i.aggrOriginalRecords()._data_)
        #print (dir(i.getDocsByIngestType('item')))
        #item = i.getDocsBySourceResource({'creator': 'Schernus, Martin (Mr)'})
        #pprint.pprint(item._data_)
        #pprint.pprint(item.aggrSourceResources(True))
        #print(dir(item.aggrSourceResources()))
        #pprint.pprint(item.aggrSourceResources().getSubject())
        #print (dir(item))
        #print(item.getId())
        #print (dir(i))
        #pprint.pprint(i.getDocsByDataProvider('University of California', True))
    
    #pprint.pprint(results)
    #print (dpla.Collections.get_url(reset=True))

@print_function_name
def europeana(**kwargs):
    europeana = RestEasy.get_wrappers('europeana')
    europeana('v2').setApiKeyFromHome()
    europeana('v2').Search.query('brassica')
    if kwargs.get('url'):
        print (europeana('v2').Search.get_url())
    if kwargs.get('query'):
        results = europeana('v2').Search.GET()
        if kwargs.get('print'):
            print (results)
    #for i in results:
    #    pprint.pprint (i._data_)
    #    print (dir(i))
    #    pprint.pprint(i.aggrIds())
    
    europeana('v2').Record.recordId('/15503/90BCCA1FF521581674903BDDA2158EAE02EF3C8A')
    if kwargs.get('url'):
        print (europeana('v2').Record.get_url())
    if kwargs.get('query'):
        results = europeana('v2').Record.GET()
        if kwargs.get('print'):
            print (results)

    europeana('v2').Suggestions.query('gogol')
    if kwargs.get('url'):
        print (europeana('v2').Suggestions.get_url())
    if kwargs.get('query'):
        results = europeana('v2').Suggestions.GET()
        if kwargs.get('print'):
            print (results)

    europeana('v2').OpenSearch.searchTerms('gogol')
    if kwargs.get('url'):
        print (europeana.v2.OpenSearch.get_url())
    if kwargs.get('query'):
        results = europeana('v2').OpenSearch.GET(return_format='json')
        if kwargs.get('print'):
            print (results)

@print_function_name
def googlebooks(**kwargs):
    googlebooks = RestEasy.get_wrappers('googlebooks').v1.Volumes
    googlebooks.query('riverboat')
    googlebooks.query.inAuthor('Twain')
    googlebooks.query.inTitle('Huckeberry')
    googlebooks.filter('ebooks')
    googlebooks.pagination.startIndex(2)
    googlebooks.pagination.maxResults(4)
    googlebooks.fields('items')
    googlebooks.onlyShowEpub()
    if kwargs.get('url'):
        print (googlebooks.get_url())
    if kwargs.get('query'):
        results = googlebooks.GET()
        if kwargs.get('print'):
            print (results)

    #for i in results:
    #    print(dir(i))
    #    pprint.pprint(i.aggrAccessInfos())
    #    pprint.pprint(i.aggrSelfLinks())

@print_function_name
def washpost(**kwargs):
    washpost = RestEasy.get_wrappers('washpost').trove('v1')
    washpost.setApiKeyFromHome()
    washpost.Resources.variant('Mark Twain')
    washpost.Resources.includeVariants(1)
    if kwargs.get('url'):
        print (washpost.Resources.get_url())
    if kwargs.get('query'):
        results = washpost.Resources.GET()
        if kwargs.get('print'):
            print (results)
    #print (results)

@print_function_name
def loc(**kwargs):
    loc = RestEasy.get_wrappers('loc').sru('v1.1').SearchRetrieve
    loc.query('dc.author any "Gogol"')
    loc.maximumRecords(1)
    if kwargs.get('url'):
        print (loc.get_url())
    if kwargs.get('query'):
        results = loc.GET()
        if kwargs.get('print'):
            print (results)

@print_function_name
def nytimes(**kwargs):
    nytimes = RestEasy.get_wrappers('nytimes').v2
    nytimes('articles').setApiKeyFromHome()
    nytimes('articles').Search.responseFormat('.json')
    #nytimes('articles').Search.filteredQuery('Terror')
    nytimes('articles').Search.filteredQuery.body.search('Terror')
    nytimes('articles').Search.filteredQuery.headline.search('Terror')
    #nytimes('articles').Search.callback()
    if kwargs.get('url'):
        print (nytimes('articles').Search.get_url())
    if kwargs.get('query'):
        results = nytimes('articles').Search.GET()
        if kwargs.get('print'):
            print (results)
    
    #pprint.pprint(dir(results[0].getResponse()))
    #print(dir(results[0].getResponse().getDocs()[0]))

    nytimes('bestsellers').setApiKeyFromHome()
    nytimes('bestsellers').Lists.responseFormat('.json')
    nytimes('bestsellers').Lists.listName('e-book-fiction')
    nytimes('bestsellers').Lists.date('1900-10-01')
    if kwargs.get('url'):
        print (nytimes('bestsellers').Lists.get_url())
    if kwargs.get('query'):
        results = nytimes('bestsellers').Lists.GET()
        if kwargs.get('print'):
            print (results)

@print_function_name
def bhl(**kwargs):
    bhl = RestEasy.get_wrappers('bhl').v2
    bhl.setApiKeyFromHome()
    bhl.AuthorSearch.name('Bob')
    if kwargs.get('url'):
        print (bhl.AuthorSearch.get_url())

    bhl.GetCollections()
    if kwargs.get('url'):
        print (bhl.GetCollections.get_url())

    bhl.NameCount()
    if kwargs.get('url'):
        print (bhl.NameCount.get_url())

    bhl.BookSearch.title('Japanese Journal of Infectious Diseases')
    if kwargs.get('url'):
        print (bhl.BookSearch.get_url())

    if kwargs.get('query'):
        results = RestEasy.GET()
        if kwargs.get('print'):
            print (results)

@print_function_name
def internetarchive(**kwargs):
    ia = RestEasy.get_wrappers('internetarchive')
    ia.identifier('testfilepost')
    ia.Download('ongrowthform00thom_files.xml')
    ia.Download.set_return_format('json')
    print (ia.Download.get_request_strings())
    #f = ia.Download.GET()
    #print(type(f))
    ia.MetadataRead.element('metadata')
    ia.MetadataRead.count(3)
    ia.MetadataRead.start(1)
    print(ia.MetadataRead.get_url())
    #print(ia.MetadataRead.GET())

    ia.MetadataWrite.target('metadata')
    ia.MetadataWrite.patch({'replace': '/doom', 
                            'value': 'test'})
    keys = ia.MetadataWrite.getApiKeysFromHome()
    access, secret = keys['access'], keys['secret']
    ia.MetadataWrite.access(access)
    ia.MetadataWrite.secret(secret)
    if kwargs.get('url'):
        print (ia.MetadataWrite.get_request_strings())
        print(ia.MetadataWrite.get_url())
    #if kwargs.get('query'):
    #    print(ia.MetadataWrite.POST())

@print_function_name
def openlibrary(**kwargs):
    openlib = RestEasy.get_wrappers('openlibrary')
    openlib.Query.edition.tableOfContents.pagenum(9)
    openlib.Query.edition.title()
    openlib.Query.return_all()
    if kwargs.get('url'):
        print (openlib.Query.get_url())
    if kwargs.get('query'):
        results = openlib.Query.GET()
        if kwargs.get('print'):
            print (results)
    
    #results = openlib.Query.GET()
    #pprint.pprint (results)

    #for i in results:
        #pprint.pprint (i._data_)
        #pprint.pprint(i.getByCreated('2013-12-10T22:00:30.722924'))
        #pprint.pprint(i.getByTitle('A Book of Scripts', True))

        #pprint.pprint(dir(i.aggrDescriptions()[0]))
        #pprint.pprint(i.getSubjects())
        #item = i.getByTitle('A Book of Scripts')
        #pprint.pprint(item.getWorks())
        #pprint.pprint(dir(item))
        #print(dir(item.getWorksByKey('/works/OL9275492W')))
        #pprint.pprint(i.getSubjects())
        #pprint.pprint(i.aggrTitles())
        #print (dir(i.getByTitle('A Book of Scripts')))

        #pprint.pprint(toc[0].getTitles())
        #     pprint.pprint(i.getByTableOfContents({'title':'Authors Preface'}))
        #pprint.pprint(i.getByAuthors('/authors/OL337830A'))

        #pprint.pprint(i.getByKey('/books/OL9048506M'))
        #for a in dir(i):
        #    if a.startswith('get'):
        #        print ('----', a)
        #        pprint.pprint( getattr(i, a)() )
        #pprint.pprint(i.getIsbn10s())
        #pprint.pprint(dir(i.getIdentifiers()[0]))
        #print(dir(i))
    

    openlib.MultiVolumesBrief.id.multikey([('oclc', '0030110408'),
                                           ('oclc', 424023),
                                           ('isbn', 3434343)])
    if kwargs.get('url'):
        print (openlib.MultiVolumesBrief.get_url())
    if kwargs.get('query'):
        results =  (openlib.MultiVolumesBrief.GET())
        if kwargs.get('print'):
            print (results)

    #openlib.new_query()

    openlib.Books.id.ISBN(123456789)
    openlib.Books.callback('blah')
    if kwargs.get('url'):
        print (openlib.Books.get_url())
    if kwargs.get('query'):
        results = openlib.Books.GET()
        if kwargs.get('print'):
            print (results)

@print_function_name
def librarything(**kwargs):
    librarything = RestEasy.get_wrappers('librarything').webservices('v1.1')
    librarything.setApiKeyFromHome()
    librarything.GetAuthor.name('Mark Twain')
    if kwargs.get('url'):
        print (librarything.GetAuthor.get_url())
    if kwargs.get('query'):
        results = librarything.GetAuthor.GET()
        if kwargs.get('print'):
            print (results)
    #print (results)
    #pprint.pprint(results[0].getResponse(True))
    #print(dir(results[0].getResponse().getLtml().getItem()))

@print_function_name
def hathitrust(**kwargs):
    hathitrust = RestEasy.get_wrappers('hathitrust')
    hathitrust.VolumesBrief.id.isbn(1234567890)
    if kwargs.get('url'):
        print (hathitrust.VolumesBrief.get_url())
    if kwargs.get('query'):
        results = hathitrust.VolumesBrief.GET()
        if kwargs.get('print'):
            print (results)

    #hathitrust.MultiVolumesBrief.id.isbn(1234567890)
    hathitrust.MultiVolumesBrief.id.multikey([('isbn','1234567890'), 
                                              (('isbn','0987654321'))])
    if kwargs.get('url'):
        print(hathitrust.MultiVolumesBrief.get_url())
    if kwargs.get('query'):
        results = hathitrust.MultiVolumesBrief.GET()
        if kwargs.get('print'):
            print (results)

@print_function_name
def inline(**kwargs):
    print (RestEasy.get_url('openlibrary->MultiVolumesBrief->id->isbn->76722|7777777:Sdsd'))
    print (RestEasy.get_url('dpla->v2->Items->searchIn->title->blah:dpla->v2->apiKey->xxx'))
                             

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
           internetarchive,
           inline]


def test(sources, **kwargs):
    for source in sources:
        #if source is not internetarchive:
        #    continue
        source(**kwargs)


import sys
if __name__ == '__main__':
    args = sys.argv[1:] if sys.argv else ''
    kwargs = {}
    for a in ('url', 'query', 'print'):
        if [arg for arg in args if re.search('^-'+a+'$', arg)]:
            kwargs[a] = True
        else:
            kwargs[a] = False
    test(sources, **kwargs)



"""
results = RestEasy.GET(return_format='json')
pprint.pprint(results.keys())
print ([type(r) for r in results.values()])
for s, item in results.items():
    for m, v in item.items():
        print (s, m, type(v))
"""
"""
ol = RestEasy.get_wrappers('openlibrary')
ol.Query.edition.genres('horror')

print (ol.Query.get_url(reset=True))
"""



"""
from rest_easy.core.convert import DynamicAccessor

with open('dplaoutput.txt', 'r') as f:
    data = json.load(f)

    #pprint.pprint(data)

ro = DynamicAccessor(data)

print (dir(ro))
pprint.pprint (ro.getDocs()[0]._data_)

"""
#print (dir(ro.getDocs(True)[))
#pprint.pprint (ro.getDocsById('5adc45637647173f6ef0d9a25fd69d2b'))
#ro.getDocsByArobaseId()
#ro.getDocsBy_Id()
#ro.getDocsByTitle()

#pprint.pprint(k)



