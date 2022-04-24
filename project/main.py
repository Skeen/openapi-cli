from typing import Optional
from typing import Set

from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi import Body
from fastapi import Path
from fastapi import Query
from pydantic import BaseModel


description = """
The Bookstore API helps you do awesome stuff!

## Authors

# You can create and delete authors
# You can read all current authors and their metadata

## Books

# You can create and delete books
# You can read all current books
"""

tags_metadata = [
    {
        "name": "authors",
        "description": "Operations with authors.",
    },
    {
        "name": "books",
        "description": "Operations with books.",
        "externalDocs": {
            "description": "External book database",
            "url": "https://example.com/bookinfo",
        },
    },
]

app = FastAPI(
    title="Bookstore",
    description=description,
    version="0.0.1",
    terms_of_service="/terms_of_service",
    contact={
        "name": "William Christie Cartland",
        "url": "http://example.com/contact/",
        "email": "wcc@example.com",
    },
    license_info={
        "name": "MPL 2.0",
        "url": "https://mozilla.org/MPL/2.0/"
    },
    openapi_tags=tags_metadata,
)


class Author(BaseModel):
    name: str
    metadata: str


class Book(BaseModel):
    authors: Set[str]
    name: str


@app.get(
    "/",
    summary="Metadata endpoint",
    description="Announces metadata about the Bookstore API"
)
def metadata():
    return {"app": "bookstore"}


@app.get(
    "/terms_of_service",
    summary="Terms of Service",
    description="Lists the Terms of Service for the Bookstore API"
)
def terms_of_service():
    return "Lorem ipsum dolor sit amet, consectetuer adipiscing elit, sed diam nonummy nibh euismod tincidunt ut laoreet dolore magna aliquam erat volutpat. Ut wisi enim ad minim veniam, quis nostrud exerci tation ullamcorper suscipit lobortis nisl ut aliquip ex ea commodo consequat. Duis autem vel eum iriure dolor in hendrerit in vulputate velit esse molestie consequat, vel illum dolore eu feugiat nulla facilisis at vero eros et accumsan et iusto odio dignissim qui blandit praesent luptatum zzril delenit augue duis dolore te feugait nulla facilisi. Nam liber tempor cum soluta nobis eleifend option congue nihil imperdiet doming id quod mazim placerat facer possim assum. Typi non habent claritatem insitam; est usus legentis in iis qui facit eorum claritatem. Investigationes demonstraverunt lectores legere me lius quod ii legunt saepius. Claritas est etiam processus dynamicus, qui sequitur mutationem consuetudium lectorum. Mirum est notare quam littera gothica, quam nunc putamus parum claram, anteposuerit litterarum formas humanitatis per seacula quarta decima et quinta decima. Eodem modo typi, qui nunc nobis videntur parum clari, fiant sollemnes in futurum."


dummy_authors = [
    Author(
        name="William Shakespeare",
        metadata="Born 26 April 1564, died 23 April 1616",
    ),
    Author(
        name="Neil Gaiman",
        metadata="Born 10 November 1960"
    ),
    Author(
        name="Terry Pratchett",
        metadata="Born 28 April 1948, died 12 March 2015"
    )
]
authors = dict(map(lambda author: (author.name, author), dummy_authors))

dummy_books = [
    Book(name="Discworld", authors=["Terry Pratchett"]),
    Book(name="Good Omens", authors=["Neil Gaiman", "Terry Pratchett"]),
    Book(name="The Sandman", authors=["Neil Gaiman"]),
    Book(name="Hamlet", authors=["William Shakespeare"]),
    Book(name="Macbeth", authors=["William Shakespeare"]),
]
books = dict(map(lambda book: (book.name, book), dummy_books))


@app.get("/authors/", tags=["authors"])
async def get_authors() -> Set[str]:
    """Fetch all authors.

    Returns:
        A list of all author names.
    """
    return set(authors.keys())


@app.post("/authors/", tags=["authors"])
async def create_author(
    author: Author = Body(..., title="Author object to be created", description="Create the author object by adding it to the datastore."),
    force: bool = Query(False, title="Force creation", description="Flag to force replacement if a conflict occurs"),
) -> str:
    """Create an author object.

    Args:
        author: Author object to create.
        force: Force creation if a conflict occurs.

    Returns:
        "OK" if creation went well.
    """
    if author.name in authors:
        raise HTTPException(status_code=409, detail="Author already exists")
    authors[author.name] = author
    return "OK"


@app.delete("/author/{name}", tags=["authors"])
async def delete_author(
    name: str = Path(..., title="Name of the author to delete", description="Delete the author object from the datastore.")
) -> str:
    """Delete an author object.

    Args:
        name: The name of the author to delete.

    Returns:
        "OK" if deletion went well.
    """
    try:
        del authors[author.name]
        return "OK"
    except KeyError:
        raise HTTPException(status_code=404, detail="Author not found")


@app.get("/author/{name}", tags=["authors"])
async def get_author(
    name: str = Path(..., title="Name of the author to lookup", description="Return metadata about the author as fetched from the data store.")
) -> str:
    """Return metadata about the author.

    Args:
        name: The name of the author to find.

    Returns:
        All relevant metadata.
    """
    if name not in authors:
        raise HTTPException(status_code=404, detail="Author not found")
    return authors[name].metadata


@app.get("/books/", tags=["books"])
async def get_books(
    q: Optional[str] = Query(None, title="Query string", description="Book title query string to search in the datastore for a good match"),
    authors: Set[str] = Query([], title="Author filter", description="Filter books to only include titles by the provided author(s)"),
) -> Set[str]:
    """Fetch all books.

    Args:
        q: Book title query string
        authors: Author filter

    Returns:
        A list of all book names.
    """
    response_books = books.values()
    if q:
        response_books = filter(lambda book: q in book.name, response_books)
    if authors:
        response_books = filter(lambda book: authors.issubset(book.authors), response_books)
    return set(map(lambda book: book.name, response_books))


@app.post("/books/", tags=["books"])
async def create_book(
    book: Book = Body(..., title="Book object to be created", description="Create the book object by adding it to the datastore."),
    force: bool = Query(False, title="Force creation", description="Flag to force replacement if a conflict occurs"),
) -> str:
    """Create an book object.

    Args:
        book: Book object to create.
        force: Force creation if a conflict occurs.

    Returns:
        "OK" if creation went well.
    """
    if book.name in books:
        raise HTTPException(status_code=409, detail="Book already exists")
    books[book.name] = book
    return "OK"


@app.delete("/book/{name}", tags=["books"])
async def delete_book(
    name: str = Path(..., title="Name of the book to delete", description="Delete the book object from the datastore.")
) -> str:
    """Delete an book object.

    Args:
        name: The name of the book to delete.

    Returns:
        "OK" if deletion went well.
    """
    try:
        del books[book.name]
        return "OK"
    except KeyError:
        raise HTTPException(status_code=404, detail="Book not found")


@app.get("/book/{name}", tags=["books"])
async def get_book(
    name: str = Path(..., title="Name of the book to lookup", description="Return authors for the book as fetched from the data store.")
) -> Set[str]:
    """Return authors about the book.

    Args:
        name: The name of the book to find.

    Returns:
        All authors.
    """
    if name not in books:
        raise HTTPException(status_code=404, detail="Book not found")
    return books[name].authors
