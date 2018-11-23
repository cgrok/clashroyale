

<h1 align="center">Clash Royale</h1>


<div align="center">
    <strong><i>Interact with Clash Royale APIs using python.</i></strong>
    <br>
    <br>
    
<a href="https://travis-ci.com/cgrok/clashroyale">
  <img src="https://img.shields.io/travis/com/cgrok/clashroyale/master.svg?style=for-the-badge&colorB=ffbf00" alt="Travis" />
</a>

<a href="https://pypi.org/project/clashroyale/">
  <img src="https://img.shields.io/pypi/pyversions/clashroyale.svg?style=for-the-badge&colorB=ffbf00" alt="Travis" />
</a>

<a href="https://pypi.org/project/clashroyale/">
  <img src="https://img.shields.io/pypi/v/clashroyale.svg?style=for-the-badge&colorB=ffbf00" alt="Travis" />
</a>

<a href="https://pypi.org/project/clashroyale/">
  <img src="https://img.shields.io/pypi/dm/clashroyale.svg?style=for-the-badge&colorB=ffbf00" alt="Travis" />
</a>

<a href="https://github.com/cgrok/clashroyale/blob/master/LICENSE">
  <img src="https://img.shields.io/github/license/cgrok/clashroyale.svg?style=for-the-badge&colorB=ffbf00" alt="Travis" />
</a>

</div>
<br>
<div align="center">
    This library enables you to easily retrieve data from either the official Clash Royale api or royaleapi.com and dynamically interact with the data recieved in an object oriented style. Asynchronous usage is also supported.
</div>

### Installation

<img src='https://vignette.wikia.nocookie.net/clashroyale/images/d/df/Happy_Face.png/revision/latest?cb=20160706235303' align='right' height='90'>

To install the library simply use [pipenv](http://pipenv.org/) (or pip, of course).

```
pipenv install clashroyale
```

### Retrieving Data


```py
code goes here
```

### Accessing Data
You can easily access data via dot notation as shown.
```py
code goes here
```

You can also do this blah blah
```py
more stuff
```

### Asynchronous Usage:

To asynchronously make requests using aiohttp, simply use `APIClient.Async` to create the object. An example is as follows. Simply use the `await` keyword when calling api methods.

```py
code goes here
```

Alternatively you can use an async with block to automatically close the session once finished.
```py
async def main():
    async with RoyaleAPI.Async('url') as client:
        profile = await client.get_profile('2PP') 
```

### [Documentation](https://clashroyale.readthedocs.io)
You can find the full API reference here (https://clashroyale.readthedocs.io)

### License
This project is licensed under MIT

### Contributing
Feel free to contribute to this project, a helping hand is always appreciated. Join our discord server [here](https://discord.gg/etJNHCQ). 
