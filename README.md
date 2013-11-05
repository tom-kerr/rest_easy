rest_easy
====
Write RESTful API Wrappers Declaratively
------------

A python module that dynamically creates wrappers for RESTful APIs from YAML markup.

(in development)

Note: Documentation is in progress and some functionality may suddenly change.

License: GPLv3

Requires python 2.7 or greater.



How to query
------------

First, we import the module and create an instance:

```python
from rest_easy.core.main import RestEasy

RestEasy = RestEasy()
```


There are three ways to make queries -- with setters, strings, or dicts.

Each of these queries are equivalent:

```python
#setters
dpla = RestEasy.getWrappers('dpla')
dpla('v2').apiKey('xxxx')
dpla('v2').Items.searchIn.title('Tom Sawyer')
results = dpla('v2').Items.GET()

#strings
results = RestEasy.GET('dpla', 'v2', 'apiKey->xxxx:Items->searchIn->title->Tom Sawyer')

#dicts
results = RestEasy.GET('dpla', 'v2', {'apiKey': 'xxxx',
                                      'Items': {
                                          'searchIn': {
                                              'title': 'Tom Sawyer'
                                              }
                                          }  
                                       })
```

<h3>Setters</h3>
To query using setters, one must first retrieve the Source object:
```python
dpla = RestEasy.getWrappers('dpla')
```
*dpla* is now an object with DPLA API wrappers as attributes. The root object of a wrapper is the **API**, which is always written in lowercase and contains parameters of two types, **Methods** and **Properties**. **Properties**, always in mixedCase, are setters which validate our input and build our query strings, while **Methods**, always Capitalized, handle HTTP requests and act as collections of Properties (and may also behave like Properties themselves). 

These parameters can be accessed either with the dot operator or by passing keys and values as arguments to the parent object:

```python
# passing as args
dpla('v2').Items.searchIn('title', 'Tom Sawyer')

# dot operator
dpla.v2.Items.searchIn.title('Tom Sawyer')
```

Once our parameters are set, we can query by calling the Method object's HTTP request method, for example **GET**.

```python
results = dpla('v2').Items.GET()
```

Calling Method Items' attribute GET will construct a url string from the parameters we set, query the server, and return the results. One can pass the argument **return_format** to GET to convert your results to a format not supported by the API. Accepted values are **json**, **xml**, or **object**. **object** will either return an object of class 'QueryObject' or a list of such, depending on the nature of the data being converted. **pretty_print** is another optional argument which when set to **True** will pretty print your results, in addition to returning them. 

Or, if we just want the url string:
```python
query_string = dpla('v2').Items.getQueryString()
```

<h3>Strings</h3>



<h3>Dicts</h3>




How to write a wrapper
-------------------------


<h3>Source</h3>
The most fundamental component in rest_easy is the **Source**. A Source is an online entity that exposes RESTful APIs, like The New York Times or the Digital Public Library of America, represented by one or more .yaml files that contain information about what its APIs expect. 


Each Source file contains data which is encapsulated in objects called APIs, Methods, and Properties.

<h3>API</h3>


<h3>Method</h3>


<h3>Property</h3>


rest_easy comes bundled with these Sources:

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


Installation

- python 2.7 -> "pip install rest_easy/ -r rest_easy/requirements.txt" or run "python rest_easy/setup.py install" and install the dependencies yourself.
- python 3.x  -> "pip-3.x install rest_easy/ -r rest_easy/requirements.txt" or run "python rest_easy/setup.py install" and install the dependencies yourself.

Dependencies
- lxml
- PyYAML
- xmltodict
- dicttoxml
- colorama
