# didUPy
A very premature API wrapper for the Argo didUP Family platform written in Python using asyncio and aiohttp.

### Disclaimer
This library is not affiliated with Argo Software S.r.l.
It is experimental, needs documentation, supports only **one profile per account** as of now, and is **not production ready**. Use at your own risk. \
Some endpoints may be missing or they have not been wrapped into the library yet. \
If you want to help improve the project, feel free to open a pull request.

## Installation
I don't know the minimum Python version this will work on, but this library is being developed on Python 3.11.2 at the time of writing.
```bash
pip install -U git+https://github.com/Vinchethescript/didupy
```
###### Yet to be published on PyPI. The library will only be published on PyPI once it is stable and covers most (if not all) of the didUP Family API.

## Basic usage
```python
import asyncio
from didupy.client import DidUPClient

async def main():
    async with DidUPClient("SCHOOL_CODE", "USERNAME", "PASSWORD") as client:
        print(f"Hello, {client.me.user.first_name}!")

if __name__ == "__main__":
    asyncio.run(main())
```
