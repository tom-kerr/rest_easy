rest_easy
====
Write RESTful API Wrappers Declaratively
------------

A python module that dynamically creates wrappers for RESTful APIs from YAML markup.

(in development)

Note: Documentation is in progress and some functionality may suddenly change.

License: GPLv3

Requires python 3.2 or greater.



How to query
------------

First, import the module and create an instance:

```python
from rest_easy.core.main import RestEasy

RestEasy = RestEasy()
```

There are three ways to form queries -- with setters, strings, or dicts. 

Each of the following are equivalent:
```python
#setters
dpla = RestEasy.get_wrappers('dpla')
dpla('v2').apiKey('xxxx')
dpla('v2').Items.searchIn.title('Tom Sawyer')
results = dpla('v2').Items.GET()

#strings
RestEasy.new_query('dpla->v2->apiKey->xxxx : Items->searchIn->title->Tom Sawyer')
results = RestEasy.GET()

#dicts
dct = {'dpla': 
        {'v2': 
          {'apiKey': 'xxxx',
           'Items': {'searchIn': 
                      {'title': 'Tom Sawyer'}
         }}}
       }
RestEasy.new_query(dct)
results = RestEasy.GET()
```

<h3>Setters</h3>
To query using setters, first retrieve the Source object:
```python
dpla = RestEasy.get_wrappers('dpla')
```
*dpla* is now an object with DPLA API wrappers as attributes. It's parameters can be accessed either with the dot operator or by passing keys and values as arguments to the parent object:

```python
# passing as args
dpla('v2').apiKey('xxxx')
dpla('v2').Items.searchIn('title', 'Tom Sawyer')

# dot operator
dpla.v2.apiKey('xxxx')
dpla.v2.Items.searchIn.title('Tom Sawyer')
```

Once some parameters are set, a query can be made by calling the **ResourceMethod** (which is always capitalized) object's HTTP request method. For example, *GET*:

```python
results = dpla('v2').Items.GET()
```

This will construct the request, query the server, reset the parameters, and return the results. 

Passing **json**, **xml**, or **obj** as the **return_format** argument to an HTTP request method will enable an attempt at conversion to that format. **obj** refers to a **DynamicAccessor**, which creates methods on-the-fly for accessing the contents of JSON.

Multiple queries can be made asynchronously like so:
```python
dpla('v2').apiKey('xxxx')

dpla('v2').Items.searchIn.title('Tom Sawyer')
dpla('v2').Items.new_query()
dpla('v2').Items.searchIn.title('Huckleberry Finn')

results = dpla('v2').Items.GET()

```
When the request method is called, each request is issued on a new thread, and all results are joined and returned in a list in the order in which they were made.

Asynchronous requests can also me made across multiple *Sources*:

```python
dpla = RestEasy.get_wrappers('dpla')
ol = RestEasy.get_wrappers('openlibrary')

dpla('v2').apiKey('xxxx')
dpla('v2').Items.searchIn.title('Tom Sawyer')

ol.Query.edition.title('Tom Sawyer')

results = RestEasy.GET()

```

Instead of manually calling *Items.GET* and Query.GET, the **RestEasy** object's *GET* calls each query's *GET*. The results this time are a dict, with the source names ('dpla', 'openlibrary') as the keys, and the values lists of json, xml, or **DynamicAccessors**. 


<h3>Strings</h3>

The strings interface uses three tokens, **->**, **|**, and **:**, to indicate the path to and value of a parameter, to separate multiple values, and to separate statements respectively.

```python
RestEasy.new_query('europeana->v2->apiKey->xxxx : europeana->v2->Record->recordId->/15503/90BCCA1FF521581674903BDDA2158EAE02EF3C8A')

RestEasy.new_query('openlibrary->MultiVolumesBrief->id->isbn->1234567890|0987654321')

```

Lists of statements are also accepted:

```python
RestEasy.new_query(['europeana->v2->apiKey->xxxx',
                    'europeana->v2->Record->recordId->/15503/90BCCA1FF521581674903BDDA2158EAE02EF3C8A'])
```

<h3>Dicts</h3>

```python
dct = {'dlese':
         {'ddsws':
          {'v1.1':
           {'Search': {'query': 'Magma',
                       'startingOffset': 1,
                       'numReturned': 5,
                       'fromDate': '2000',
                       'dateField': '2013'}
            }}}
         }
RestEasy.new_query(dct)

```


rest_easy comes with wrappers for these Sources:

- dpla           (<a href='http://dp.la'>Digital Public Library of America</a>)
- bhl            (<a href='http://biodiversityheritagelibrary.org'>Biodiversity Heritage Library</a>)
- hathitrust     (<a href='http://hathitrust.org'>Hathi Trust</a>)
- openlibrary    (<a href='http://openlibrary.org'>Open Library</a>)
- europeana      (<a href='http://europeana.eu'>Europeana</a>)
- googlebooks    (<a href='http://books.google.com'>Google Books</a>)
- loc            (<a href='http://loc.gov/standards/sru'>Library of Congress SRU</a>)
- librarything   (<a href='http://www.librarything.com'>Library Thing</a>)
- dlese          (<a href='http://www.dlese.org'>Digital Library for Earth System Education</a>)
- nytimes        (<a href='http://developer.nytimes.com/'>The New York Times</a>)
- washpost       (<a href='https://developer.washingtonpost.com/'>The Washington Post</a>)


Help
-----

A help function is provided for getting information about the wrappers.

```
>>> RestEasy.help()

Source List
        nytimes
        hathitrust
        bhl
        librarything
        googlebooks
        openlibrary
        dpla
        europeana
        washpost
        loc
        dlese

>>> RestEasy.help('dpla')

Source "dpla"
    Digital Public Library of America   
    
    The Digital Public Library of America brings together the riches of 
    America’s libraries, archives, and museums, and makes them freely 
    available to the world. It strives to contain the full breadth of human 
    expression, from the written word, to works of art and culture, to records 
    of America’s heritage, to the efforts and data of science.
    
    Documentation:
      http://dp.la/info/developers/codex/
    
    apis:
        v2

>>> RestEasy.help('dpla->v2')

API "v2"
    essential: ['apiKey']

    methods:
        Collections
        Item
        Items
    properties:
        apiKey


>>> RestEasy.help('dpla->v2->Items')

Method "Items"
    A DPLA item is a reference to the digital representation of a single 
    piece of content indexed by the DPLA. The piece of content can be, for 
    example, a book, a photograph, a video, etc. The content is digitized 
    from its original, physical source and uploaded to an online repository. 
    The DPLA allows users to search for content across a multitude of online 
    repositories, including University of Virginia Library, Kentucky Digital 
    Library, Harvard University Library, etc. After retrieving DPLA items, 
    developers can display or follow links to their original online digital 
    records.
    
    http_method: GET

    properties:
        callback
        facetSize
        facets
        fetchFields
        keywordSearch
        page
        pageSize
        searchIn
        sortBy
        sortByPin
```


or, one can call a parameter's **help** method:

```
>>> dpla('v2').Items.help()

Method "Items"
    A DPLA item is a reference to the digital representation of a single 
    piece of content indexed by the DPLA. The piece of content can be, for 
    ...

```


------
DynamicAccessors
------

```python
>>> from rest_easy.core.main import RestEasy
>>> r = RestEasy()
>>> dpla = r.get_wrappers('dpla')
>>> dpla('v2')apiKey('xxxxx')
>>> dpla('v2').Items.searchIn.title('Dead Souls')
>>> results = dpla('v2')Items.GET(return_format='obj')
>>> results

[<rest_easy.core.convert.DynamicAccessor object at 0x7f2520f23828>]

>>> print (results[0]._data_)

{'count': 12,
 'docs': [{'@context': 'http://dp.la/api/items/context',
           '@id': 'http://dp.la/api/items/5adc45637647173f6ef0d9a25fd69d2b',
           '@type': 'ore:Aggregation',
           '_id': 'hathitrust--009668717',
           '_rev': '12-4b104ede2637604c8913857ce3a63e74',
           'admin': {'sourceResource': [{'title': 'Dead souls /'}],
                     'valid_after_enrich': [False],
                     'validation_message': ["'object' is a required "
                                            'property']},
           'aggregatedCHO': '#sourceResource',
           'dataProvider': ['University of California',
                            'University of California',
                            'University of Michigan',
                            'NMNH - Anthropology Dept.',
                            'Princeton University',
                            'University of Michigan',
                            'New York Public Library',
                            'Slavic and East European Collections. The '
                            'New York Public Library',
                            'National Anthropological Archives',
                            'Duke University'],
           'id': '5adc45637647173f6ef0d9a25fd69d2b',
           'ingestDate': '2014-08-06T18:45:59.497935',
           'ingestType': 'item',
           'ingestionSequence': 15,
           'isShownAt': 'http://catalog.hathitrust.org/Record/009668717',
           'originalRecord': {'_id': ['009668717'],
                              'controlfield': [{'#text': '009668717',
                                                'tag': '001'},
                                               {'#text': 'MiAaHDL',
                                                'tag': '003'},
                                               {'#text': '20110405000000.0',
                                                'tag': '005'},
                                               {'#text': 'm        '
                                                         'd        ',
                                                'tag': '006'},
                                               {'#text': 'cr bn ---auaua',
                                                'tag': '007'},
                                               {'#text': '921113s1915    '
                                                         'nyu           '
                                                         '000 1 eng d',
                                                'tag': '008'}],
                                   .... 
>>> dir(results[0])

['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_add_child_get_func_', '_add_get_func_', '_add_getby_func_', '_append_get_func_', '_build_accessors_', '_built_', '_data_', '_deferred_', '_format_attr_name_', '_format_dict_', '_format_list_', '_get_formatted_data_', '_get_match_func_', '_is_flat_', '_lazy_', '_make_plural_', '_match_dict_', '_match_list_', '_match_str_', 'aggrAdmins', 'aggrAggregatedCHOs', 'aggrArobaseContexts', 'aggrArobaseIds', 'aggrArobaseTypes', 'aggrDataProviders', 'aggrIds', 'aggrIngestDates', 'aggrIngestTypes', 'aggrIngestionSequences', 'aggrIsShownAts', 'aggrObjects', 'aggrOriginalRecords', 'aggrProviders', 'aggrScores', 'aggrSourceResources', 'aggr_Ids', 'aggr_Revs', 'getCount', 'getDocs', 'getDocsByAdmin', 'getDocsByAggregatedCHO', 'getDocsByArobaseContext', 'getDocsByArobaseId', 'getDocsByArobaseType', 'getDocsByDataProvider', 'getDocsById', 'getDocsByIngestDate', 'getDocsByIngestType', 'getDocsByIngestionSequence', 'getDocsByIsShownAt', 'getDocsByObject', 'getDocsByOriginalRecord', 'getDocsByProvider', 'getDocsByScore', 'getDocsBySourceResource', 'getDocsBy_Id', 'getDocsBy_Rev', 'getFacets', 'getLimit', 'getStart']

>>> print(results[0].aggrIds())

['5adc45637647173f6ef0d9a25fd69d2b',
 'db165fda72d885ebc8ab5c0e69aa149f',
 'b28047aa82169895181bf5d393c9c194',
 '1ff20f51d2ff33d4f4404011147a61af',
 'e61cd1d8573c41f376b25a362f02df0b',
 '7855728877da9e3c7189a6751b4a3d96',
 'ac91d10a0e062343d28f2fb87bc9428f',
 '6d4d2aec08fb275c0bbbae36f5993ec1',
 '37a3814da79c47ebb4c9bbb0b092edb3',
 'ac190a3d347dfb9572ee7efa014e2dfa']
```

DynamicAccessor objects have three types of methods for accessing data:

getField -> where 'field' is the key of an item one layer into a structure to be returned*, such as: 

        {'field': {'deeper_field': value}}
                    

getFieldBySubField -> where 'field' is the key of a list of dicts which can be retrieved based on the value of a 'SubField', for example:

        {'items': [ {'id': 1, 'title': ...,
                    {'id': 2, 'title': ...,
                  ]}
                           
an item can be retrieved by id (getItemsById), or by title (getItemsByTitle), or any other subfield. All items that match the input for that subfield will be returned*.

aggrField -> where 'field' is a subfield that occurs more than once among a list of dicts, and 'aggr' stands for aggregate. Considering the previous structure, a method called 'aggrId'would return* a list of the values of every 'id' field.
 
        
* If the field being returned contains another nested structure, another DynamicAccessor will be generated and returned for further access, otherwise, the value of that field or a list of values will be returned. One can defer the construction of nested DynamicAccessors by passing lazy=True to the parent's contructor, and even defer the parent's construction by passing it deferred=True. Construction of these objects will take place when one tries to access them.


Installation

- python3  -> "pip3 install rest_easy/ -r rest_easy/requirements.txt" or run "python3 rest_easy/setup.py install" and install the dependencies yourself.

Dependencies
- lxml
- PyYAML
- xmltodict
- dicttoxml

