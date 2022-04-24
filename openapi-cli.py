import os
from functools import reduce
from inspect import Parameter
from inspect import signature

import click
import httpx


COMMAND_NAME = "openapi-cli"
PROGRAM_NAME = "OpenAPI CLI"
BASE_URL = "http://localhost:8000"


def get_program_version():
    return os.environ.get("VERSION", "unknown_version")

def get_program_license():
    return os.environ.get("LICENSE", "unknown_license")

def get_program_authors():
    return os.environ.get("AUTHORS", "unknown_authors")


def add_doc(documentation):
    def decorator(func):
        func.__doc__ = documentation
        return func
    return decorator


def str_to_type(type_name):
    if type_name == "integer":
        return int
    elif type_name == "boolean":
        return bool
    elif type_name == "string":
        return str
    elif type_name == "array":
        return list
    else:
        raise TypeError(f"Unknown type: {type_name}")


def add_parameters(parameters):
    def decorator(func):

        for parameter in parameters:
            func = click.option(
                f"--{parameter['name']}",
                help=parameter.get("description", None),
                default=parameter["schema"].get("default", None),
                required=parameter.get("required", True),
                type=str_to_type(parameter["schema"].get("type", "string")),
            )(func)

        return func

    return decorator


def create_command(method, path, documentation, parameters):

    @click.command(name=path)
    @add_doc(documentation)
    @add_parameters(parameters)
    def func(*args, **kwargs):
        path_params = filter(lambda parameter: parameter["in"] == "path", parameters)

        # Template all path parameters
        request_path = path
        for parameter in path_params:
            name = parameter["name"]
            request_path = request_path.replace("{" + name + "}", str(kwargs[name]))
            del kwargs[name]

        response = httpx.request(method.upper(), BASE_URL + request_path, params=kwargs)
        print(response.text)

    return func


def create_group(method, documentation):
    @click.group(name=method)
    @add_doc(documentation)
    def func():
        pass
    return func


def create_cli():
    spec_url=BASE_URL + "/openapi.json"

    response = httpx.get(spec_url)
    response.raise_for_status()
    openapi_json = response.json()

    @click.group()
    @add_doc(openapi_json["info"]["title"] + "\n" + openapi_json["info"].get("description", ""))
    def main():
        pass

    @main.group()
    def meta():
        """Various meta endpoints."""
        pass

    # meta TOS endpoint
    # meta contact endpoint
    # meta license endpoint

    # TODO: Add support for tags grouping

    @meta.command(help="Output version information and exit")
    def version():
        project_name = openapi_json["info"]["title"]
        project_version = openapi_json["info"]["version"]

        openapi_version = openapi_json["openapi"]

        version = get_program_version()
        license = get_program_license()
        authors = get_program_authors()

        lines = [
            f"{project_name} {project_version} (OpenAPI: {openapi_version})",
            f"Generated using {COMMAND_NAME} ({PROGRAM_NAME}) {version}.",
            "",
            f"{license}",
            "",
            f"Written by {authors}",
        ]
        click.echo("\n".join(lines))

    method_keys = reduce(
        set.union, (set(obj.keys()) for obj in openapi_json["paths"].values())
    )
    methods = {
        method: create_group(method, f"Collection of {method} calls")
        for method in method_keys
    }
    for group in methods.values():
        main.add_command(group)

    for path, obj in openapi_json["paths"].items():
        for method, mobj in obj.items():
            summary = mobj.get("summary", "") + "\n\n" + mobj.get("description", "")
            parameters = mobj.get("parameters", [])

            func = create_command(method, path, summary, parameters)
            methods[method].add_command(func)

    return main


if __name__ == '__main__':
    main = create_cli()
    main()
